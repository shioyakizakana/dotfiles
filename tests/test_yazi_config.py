"""Yazi設定のTOML互換性、fetcher登録、既存のキー操作を検証する。"""

from pathlib import Path
import os
import re
import shutil
import tempfile
import time
import tomllib
import unittest


CONFIG = Path(__file__).resolve().parents[1] / "home/dot_config/yazi"
YAZI = shutil.which("yazi")


class YaziConfigTests(unittest.TestCase):
    def test_managed_toml_files_are_parseable(self):
        for path in sorted(CONFIG.glob("*.toml")):
            with self.subTest(file=path.name):
                tomllib.loads(path.read_text())

    def test_git_fetchers_cover_files_and_directories(self):
        config = tomllib.loads((CONFIG / "yazi.toml").read_text())
        self.assertEqual(config["plugin"]["prepend_fetchers"], [
            {"group": "git", "url": "*", "run": "git"},
            {"group": "git", "url": "*/", "run": "git"},
        ])

    def test_public_packages_cover_configured_plugins_and_flavors(self):
        packages = tomllib.loads((CONFIG / "package.toml").read_text())
        keys = tomllib.loads((CONFIG / "keymap.toml").read_text())["mgr"]["prepend_keymap"]
        configured = {binding["run"].split()[1] for binding in keys
                      if binding["run"].startswith("plugin ")}
        configured.update(re.findall(r'setup_optional\("([^"\n]+)"',
                                     (CONFIG / "init.lua").read_text()))
        configured -= {"zoxide", "fzf", "bunny-private"}
        plugins = packages["plugin"]["deps"]
        self.assertEqual({entry["use"] for entry in plugins}, {
            "stelcodes/bunny" if name == "bunny" else f"yazi-rs/plugins:{name}"
            for name in configured
        })
        self.assertEqual(len(plugins), len(configured))
        flavors = tomllib.loads((CONFIG / "theme.toml").read_text())["flavor"]
        entries = packages["flavor"]["deps"]
        self.assertEqual({entry["use"] for entry in entries},
                         {f"yazi-rs/flavors:{name}" for name in flavors.values()})
        self.assertEqual(len(entries), len(set(flavors.values())))

    def test_public_packages_pin_revisions_and_record_content_hashes(self):
        mise = tomllib.loads((CONFIG.parent / "mise/config.toml").read_text())
        self.assertRegex(mise["tools"]["yazi"], r"^\d+\.\d+\.\d+$")
        packages = tomllib.loads((CONFIG / "package.toml").read_text())
        for kind in ("plugin", "flavor"):
            for entry in packages[kind]["deps"]:
                with self.subTest(package=entry["use"]):
                    self.assertEqual(set(entry), {"use", "rev", "hash"})
                    self.assertRegex(entry["rev"], r"^=[0-9a-f]{40}$")
                    self.assertRegex(entry["hash"], r"^[0-9a-f]{1,32}$")

    def test_manager_keybindings_keep_actions_arguments_and_descriptions(self):
        bindings = tomllib.loads((CONFIG / "keymap.toml").read_text())["mgr"]["prepend_keymap"]
        self.assertEqual(bindings, [
            {"on": "o", "run": "create"},
            {"on": "q", "run": "close"},
            {"on": "<C-i>", "run": "forward"},
            {"on": "<C-o>", "run": "back"},
            {"on": ["g", "?"], "run": "help"},
            {"on": ["i", "<Space>"], "run": "cd --interactive", "desc": "[cd]パスを入力してcd"},
            {"on": "-", "run": "leave", "desc": "[cd]親ディレクトリへ移動"},
            {"on": "<Enter>", "run": "plugin smart-enter", "desc": "[file]アクティブなファイルまたはフォルダを開く"},
            {"on": "<C-p>", "run": "plugin toggle-pane max-preview", "desc": "[file]プレビューを最大サイズで開く"},
            {"on": "e", "run": "plugin bunny", "desc": "[bookmark]ブックマークしたパスに移動"},
            {"on": ["c", "m"], "run": "plugin chmod"},
            {"on": ["z", "f"], "run": "plugin fzf"},
            {"on": ["z", "i"], "run": "plugin zoxide"},
        ])

    def test_escape_closes_the_input_layer(self):
        bindings = tomllib.loads((CONFIG / "keymap.toml").read_text())["input"]["prepend_keymap"]
        self.assertEqual(bindings, [{"on": "<Esc>", "run": "close", "desc": "Cancel input"}])

    @unittest.skipUnless(os.name == "posix" and YAZI, "POSIX環境とYaziが必要です")
    def test_yazi_loads_keymap_in_isolated_terminal(self):
        import errno
        import fcntl
        import pty
        import select
        import signal
        import struct
        import termios

        with tempfile.TemporaryDirectory(prefix="yazi smoke ") as directory:
            base = Path(directory)
            config = base / "config/yazi"
            config.mkdir(parents=True)
            (base / "bin").mkdir()
            (base / "work").mkdir()
            shutil.copyfile(CONFIG / "keymap.toml", config / "keymap.toml")
            # 公開keymapだけを実Yaziで読み、私的設定・プラグイン・外部CLIを使わず終了する。
            (config / "init.lua").write_text(
                'local f = assert(io.open(os.getenv("HOME") .. "/init-loaded", "w"))\n'
                'f:write("loaded"); f:close(); ya.emit("quit", {})\n'
            )
            environment = {
                "HOME": str(base), "PATH": str(base / "bin"), "TMPDIR": str(base),
                "XDG_CONFIG_HOME": str(base / "config"), "XDG_CACHE_HOME": str(base / "cache"),
                "XDG_STATE_HOME": str(base / "state"), "XDG_DATA_HOME": str(base / "data"),
                "TERM": "xterm-256color", "LANG": "C.UTF-8", "SHELL": "/bin/sh",
            }
            try:
                pid, terminal = pty.fork()
            except OSError as error:
                self.skipTest(f"疑似端末を作成できません: {error}")
            if pid == 0:
                try:
                    os.chdir(base / "work")
                    os.execve(YAZI, [YAZI], environment)
                finally:
                    os._exit(127)
            output = bytearray()
            status = None
            try:
                fcntl.ioctl(terminal, termios.TIOCSWINSZ, struct.pack("HHHH", 24, 100, 0, 0))
                deadline = time.monotonic() + 15
                while time.monotonic() < deadline:
                    if select.select([terminal], [], [], 0.1)[0]:
                        try:
                            output.extend(os.read(terminal, 65536))
                        except OSError as error:
                            if error.errno != errno.EIO:
                                raise
                    child, result = os.waitpid(pid, os.WNOHANG)
                    if child:
                        status = result
                        break
            finally:
                if status is None:
                    os.kill(pid, signal.SIGKILL)
                    os.waitpid(pid, 0)
                os.close(terminal)
            self.assertIsNotNone(status, "隔離Yaziが15秒以内に終了しませんでした")
            self.assertEqual(os.waitstatus_to_exitcode(status), 0, output.decode(errors="replace")[-2000:])
            self.assertEqual((base / "init-loaded").read_text(), "loaded")


if __name__ == "__main__":
    unittest.main()
