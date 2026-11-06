"""隔離したchezmoiソースで環境別の対象とTermuxのパスを再現する。"""

import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import tomllib
import unittest


ROOT = Path(__file__).resolve().parents[1]
CHEZMOI = shutil.which("chezmoi")


@unittest.skipUnless(CHEZMOI, "chezmoiが必要です")
class EnvironmentPolicyTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix="chezmoi environment ")
        self.addCleanup(directory.cleanup)
        self.base = Path(directory.name)
        self.source = self.base / "source"
        self.source.mkdir()
        shutil.copyfile(ROOT / "home/.chezmoiignore", self.source / ".chezmoiignore")
        scripts = self.source / ".chezmoiscripts"
        scripts.mkdir()
        for name in ("apt", "brew", "mise"):
            # managedはスクリプトを実行しない。実スクリプトは持ち込まない。
            (scripts / f"run_after_install-{name}.sh").write_text(
                "#!/usr/bin/env bash\nexit 99\n"
            )
        mise = self.source / "dot_config/mise/config.toml"
        mise.parent.mkdir(parents=True)
        mise.write_text("[tools]\n")
        self.prefix = self.base / "data/data/com.termux/files/usr"
        (self.prefix / "bin").mkdir(parents=True)
        self.environment = {
            "HOME": str(self.base / "home"),
            "PATH": str(self.prefix / "bin"),
            # prootに引き継がれたPREFIXでもAndroidとは限らない。
            "PREFIX": str(self.prefix),
        }
        self.config = self.base / "config.json"

    def run_chezmoi(self, arguments, flags=None, os_name="linux", text=None):
        self.config.write_text(json.dumps({"data": flags or {}}))
        return subprocess.run(
            [
                CHEZMOI,
                "--config", str(self.config),
                "--source", str(self.source),
                "--destination", str(self.base / "home"),
                "--cache", str(self.base / "cache"),
                "--persistent-state", str(self.base / "state.db"),
                "--refresh-externals=never", "--no-tty",
                "--override-data", json.dumps(
                    {"chezmoi": {"os": os_name, "arch": "arm64"}}
                ),
                *arguments,
            ],
            input=text,
            capture_output=True,
            text=True,
            env=self.environment,
            timeout=10,
        )

    def managed(self, flags, os_name="linux"):
        result = self.run_chezmoi(
            ["managed", "--path-style=source-relative"], flags, os_name
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return set(result.stdout.splitlines())

    def installer_names(self, entries):
        return {
            name for name in ("apt", "brew", "mise")
            if f".chezmoiscripts/run_after_install-{name}.sh" in entries
        }

    def test_supported_ubuntu_environments_keep_all_installers(self):
        for flag in ("nativeUbuntu", "wslUbuntu", "qemuUbuntu"):
            with self.subTest(flag=flag):
                entries = self.managed({flag: True})
                self.assertEqual(self.installer_names(entries), {"apt", "brew", "mise"})
                self.assertIn("dot_config/mise/config.toml", entries)
        entries = self.managed({"qemuUbuntu": True}, "android")
        self.assertEqual(self.installer_names(entries), {"apt", "brew", "mise"})

    def test_proot_keeps_apt_and_mise_with_inherited_termux_prefix(self):
        for os_name in ("linux", "android"):
            with self.subTest(os_name=os_name):
                entries = self.managed({"prootUbuntu": True}, os_name)
                self.assertEqual(self.installer_names(entries), {"apt", "mise"})
                self.assertIn("dot_config/mise/config.toml", entries)

    def test_termux_excludes_ubuntu_installers_and_mise_configuration(self):
        for os_name in ("linux", "android"):
            with self.subTest(os_name=os_name):
                entries = self.managed({"termux": True}, os_name)
                self.assertEqual(self.installer_names(entries), set())
                self.assertNotIn("dot_config/mise/config.toml", entries)

    def test_unknown_environment_excludes_installers(self):
        entries = self.managed({})
        self.assertEqual(self.installer_names(entries), set())

    def test_android_without_guest_flag_excludes_ubuntu_installers(self):
        entries = self.managed({"nativeUbuntu": True}, "android")
        self.assertEqual(self.installer_names(entries), set())

    def test_termux_flag_overrides_conflicting_ubuntu_flag(self):
        entries = self.managed({"termux": True, "nativeUbuntu": True})
        self.assertEqual(self.installer_names(entries), set())

    def test_non_linux_os_does_not_run_ubuntu_installers(self):
        entries = self.managed({"nativeUbuntu": True}, "darwin")
        self.assertEqual(self.installer_names(entries), set())

    def test_init_data_selects_termux_and_proot_policies(self):
        for linux_env, os_name, expected in (
            ("termux", "linux", set()),
            ("termux", "android", set()),
            ("proot-ubuntu", "linux", {"apt", "mise"}),
            ("proot-ubuntu", "android", {"apt", "mise"}),
        ):
            with self.subTest(linux_env=linux_env, os_name=os_name):
                prompt = (
                    "Execute Linux Environment (native-ubuntu/wsl-ubuntu/qemu-ubuntu/proot-ubuntu/termux)"
                    if os_name == "linux"
                    else "Execute Linux Environment (termux/qemu-ubuntu/proot-ubuntu)"
                )
                result = self.run_chezmoi(
                    [
                        "execute-template", "--init",
                        "--promptString", "Machine type (personal/work)=personal",
                        "--promptString", f"{prompt}={linux_env}",
                    ],
                    os_name=os_name,
                    text=(ROOT / ".chezmoi.toml.tmpl").read_text(),
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                data = tomllib.loads(result.stdout)["data"]
                self.assertEqual(data["protonPassProvider"], "env")
                self.assertEqual(data["termux"], linux_env == "termux")
                self.assertEqual(data["prootUbuntu"], linux_env == "proot-ubuntu")
                entries = self.managed(data, os_name)
                self.assertEqual(self.installer_names(entries), expected)

    def render_tmux(self, flags=None, os_name="linux"):
        source = ROOT / "home/dot_config/tmux/tmux.conf.tmpl"
        if not source.exists():
            source = ROOT / "home/dot_config/tmux/tmux.conf"
        result = self.run_chezmoi(
            ["execute-template"], flags, os_name, source.read_text()
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        return result.stdout

    def test_termux_tmux_uses_zsh_from_prefix_without_system_bin(self):
        zsh = self.prefix / "bin/zsh"
        zsh.write_text("not executed: zsh fixture\n")
        zsh.chmod(0o755)
        rendered = self.render_tmux({"termux": True}, "android")
        self.assertIn(f'set-option -g default-shell "{zsh}"', rendered)
        self.assertNotIn("default-shell /bin/zsh", rendered)

    def test_tmux_keeps_default_shell_when_zsh_is_missing(self):
        rendered = self.render_tmux({"termux": True}, "android")
        self.assertNotIn("set-option -g default-shell", rendered)


if __name__ == "__main__":
    unittest.main()
