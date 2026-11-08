"""隔離HOMEとダミーツールでBash・Zshの起動設定を検証する。"""

import json
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
BASH = shutil.which("bash")
ZSH = shutil.which("zsh")
CHEZMOI = shutil.which("chezmoi")
MKDIR = shutil.which("mkdir")


@unittest.skipUnless(BASH and ZSH and CHEZMOI and MKDIR, "Bash・Zsh・chezmoi・mkdirが必要です")
class ShellConfigTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix="shell-startup ")
        self.addCleanup(directory.cleanup)
        self.base = Path(directory.name)
        self.home = self.base / "home with spaces"
        self.home.mkdir()
        self.bin = self.base / "commands"
        self.bin.mkdir()
        self.trace = self.base / "trace"
        self.trace.write_text("")
        self.environment = {
            "HOME": str(self.home), "PATH": str(self.bin), "TERM": "dumb",
            "LC_ALL": "C", "TRACE": str(self.trace), "SSH_AUTH_SOCK": "/dummy/existing.sock",
        }
        self.stub("mkdir", f'exec "{MKDIR}" "$@"\n')
        for name in ("mise", "zoxide", "atuin"):
            self.stub(name, f'printf "%s\\n" "{name} $*" >> "$TRACE"\nprintf ":\\n"\n')
        self.local_bin = self.home / ".local/bin"
        self.local_bin.mkdir(parents=True)
        update = self.local_bin / "update_apps"
        update.write_text(f'#!{BASH}\nprintf "update_apps %s\\n" "$*" >> "$TRACE"\n')
        update.chmod(0o755)
        self.write_startup_files()

    def stub(self, name, body):
        path = self.bin / name
        path.write_text(f"#!{BASH}\n{body}")
        path.chmod(0o755)
        return path

    def write_startup_files(self, proot=False):
        source = self.base / "empty-source"
        source.mkdir(exist_ok=True)
        config = self.base / "config.json"
        config.write_text(json.dumps({"data": {"prootUbuntu": proot}}))
        rendered = subprocess.run(
            [CHEZMOI, "--config", str(config), "--source", str(source),
             "--destination", str(self.home), "--cache", str(self.base / "cache"),
             "--persistent-state", str(self.base / "state.db"),
             "--refresh-externals=never", "--no-tty", "execute-template"],
            input=(ROOT / "home/dot_zshrc.tmpl").read_text(),
            env=self.environment, capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(rendered.returncode, 0, rendered.stderr)
        for name, text in (
            (".bashrc", (ROOT / "home/dot_bashrc").read_text()),
            (".zshrc", rendered.stdout),
        ):
            # システム補完や固定パスのHomebrewを実行せず、起動設定全体を読む。
            for host_path in (
                "/usr/bin/lesspipe", "/usr/bin/tput", "/usr/bin/dircolors",
                "/usr/share/bash-completion/bash_completion", "/etc/bash_completion",
                "/etc/debian_chroot", "/home/linuxbrew/.linuxbrew/bin/brew",
            ):
                replacement = shlex.quote(str(self.base / "disabled" / host_path.lstrip("/")))
                text = re.sub(
                    f'"{re.escape(host_path)}"|{re.escape(host_path)}',
                    lambda _: replacement, text,
                )
            (self.home / name).write_text(text)
        shutil.copyfile(ROOT / "home/dot_bash_aliases", self.home / ".bash_aliases")
        zdir = self.home / ".zsh"
        zdir.mkdir(exist_ok=True)
        for name in ("path.zsh", "alias.zsh"):
            shutil.copyfile(ROOT / "home/dot_zsh" / name, zdir / name)
        for name in ("operation.zsh", "completion.zsh", "plugin.zsh"):
            (zdir / name).write_text("# UI・補完・外部プラグインはこのテストの対象外。\n")
        (zdir / "functions").mkdir(exist_ok=True)
        (zdir / "functions/fixture.zsh").write_text(":\n")
        common = ROOT / "home/dot_config/shell"
        shutil.copytree(common, self.home / ".config/shell", dirs_exist_ok=True)
        environment = self.home / ".config/shell/env.sh"
        # ホストのsnap内のコマンドも探索対象へ入れない。
        environment.write_text(environment.read_text().replace("/snap/bin", str(self.base / "snap/bin")))

    def run_shell(self, shell, command, **environment):
        if shell == "bash":
            arguments = [BASH, "--noprofile", "--norc", "-ic"]
        else:
            arguments = [ZSH, "-df", "-ic"]
        # -c全体を先に解析するZshでも、対話入力と同様にalias定義後に解析する。
        return subprocess.run(
            [*arguments, f'. "$HOME/.{shell}rc"\nTEST_STARTUP_STATUS=$?\neval "$TEST_COMMAND"'],
            env={**self.environment, **environment, "TEST_COMMAND": command},
            capture_output=True, text=True, timeout=10,
        )

    def test_missing_legacy_file_does_not_cause_startup_error(self):
        for shell in ("bash", "zsh"):
            with self.subTest(shell=shell):
                result = self.run_shell(shell, 'printf "READY\\n"')
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, "READY\n")
                self.assertNotIn("funciton.sh", result.stderr)
                self.assertNotIn("no such file", result.stderr.lower())

    def test_existing_legacy_extension_is_loaded_with_spaces_in_home(self):
        legacy = self.home / "scripts/shell/funciton.sh"
        legacy.parent.mkdir(parents=True)
        legacy.write_text('legacy_fixture() { printf "legacy-loaded\\n"; }\n')
        for shell in ("bash", "zsh"):
            with self.subTest(shell=shell):
                result = self.run_shell(shell, "legacy_fixture")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, "legacy-loaded\n")

    def test_common_environment_and_paths_are_available_in_both_shells(self):
        directories = [self.home / name for name in (
            ".local/bin", "bin", ".zsh/plugin/plugins/fzf/bin", ".cargo/bin",
            "go", "go/bin", ".local/share/pnpm/bin",
        )]
        for path in directories:
            path.mkdir(parents=True, exist_ok=True)
        for shell in ("bash", "zsh"):
            with self.subTest(shell=shell):
                result = self.run_shell(shell, 'printf "%s\\n" "$TMPDIR" "$GOPATH" "$PNPM_HOME" "$FZF_INSTALL" "$EDITOR" "$LANG" "$LANGUAGE" "$PATH"')
                self.assertEqual(result.returncode, 0, result.stderr)
                lines = result.stdout.splitlines()
                self.assertEqual(lines[:7], [str(self.home / "tmp"), str(self.home / "go"),
                    str(self.home / ".local/share/pnpm"), str(self.home / ".zsh/plugin/plugins/fzf"),
                    "vim", "ja_JP.UTF-8", "ja_JP:ja"])
                paths = lines[7].split(":")
                expected = [str(path) for path in directories]
                self.assertEqual(paths[0], str(self.bin))
                self.assertEqual([path for path in paths if path in expected], expected)

    def test_reloading_common_environment_does_not_duplicate_paths(self):
        for shell in ("bash", "zsh"):
            with self.subTest(shell=shell):
                result = self.run_shell(shell, '. "$HOME/.config/shell/env.sh"\n. "$HOME/.config/shell/env.sh"\nprintf "%s\\n" "$PATH"')
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertNotIn("no such file", result.stderr.lower())
                paths = result.stdout.strip().split(":")
                self.assertEqual(paths.count(str(self.local_bin)), 1)

    def test_explicit_tmpdir_and_available_editor_are_respected(self):
        self.stub("nvim", ":\n")
        tmpdir = self.base / "custom tmp"
        for shell in ("bash", "zsh"):
            with self.subTest(shell=shell):
                result = self.run_shell(shell, 'printf "%s\\n" "$TMPDIR" "$EDITOR"', TMPDIR=str(tmpdir))
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.splitlines(), [str(tmpdir), "nvim"])
                self.assertTrue(tmpdir.is_dir())

    def test_common_aliases_use_managed_update_command_and_keep_shell_reload(self):
        for shell in ("bash", "zsh"):
            with self.subTest(shell=shell):
                self.trace.write_text("")
                result = self.run_shell(shell, 'upd apt\nalias reload\nalias cmlg\nalias nvlg')
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("update_apps apt\n", self.trace.read_text())
                self.assertIn(f"~/.{shell}rc", result.stdout)
                self.assertIn("nvim +LazyGit", result.stdout)

    def test_tool_initializers_receive_the_matching_shell(self):
        for shell in ("bash", "zsh"):
            with self.subTest(shell=shell):
                self.trace.write_text("")
                result = self.run_shell(shell, ":")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(self.trace.read_text().splitlines(), [
                    f"mise activate {shell}", f"zoxide init {shell} --cmd cd", f"atuin init {shell}",
                ])

    def test_existing_ssh_socket_behavior_is_preserved(self):
        for shell, expected in (("bash", "/dummy/existing.sock"), ("zsh", str(self.home / ".ssh/proton-pass-agent.sock"))):
            with self.subTest(shell=shell):
                result = self.run_shell(shell, 'printf "%s\\n" "$SSH_AUTH_SOCK"')
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.strip(), expected)

    def test_optional_fzf_settings_keep_success_and_support_spaces_in_home(self):
        for shell in ("bash", "zsh"):
            with self.subTest(shell=shell):
                result = self.run_shell(shell, 'printf "%s\\n" "$TEST_STARTUP_STATUS"')
                self.assertEqual(result.stdout.strip(), "0", result.stderr)
                (self.home / f".fzf.{shell}").write_text("FZF_FIXTURE=loaded\n")
                result = self.run_shell(shell, 'printf "%s %s\\n" "$TEST_STARTUP_STATUS" "$FZF_FIXTURE"')
                self.assertEqual(result.stdout.strip(), "0 loaded", result.stderr)

    def test_proot_alias_is_available_when_proot_template_flag_and_runtime_match(self):
        self.write_startup_files(proot=True)
        for shell in ("bash", "zsh"):
            with self.subTest(shell=shell):
                result = self.run_shell(shell, 'alias cd_android', PROOT_L2S_DIR="/dummy/proot")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("cd /sdcard", result.stdout)

    def test_rendered_zsh_template_is_valid_with_both_proot_flags(self):
        for proot in (False, True):
            with self.subTest(proot=proot):
                self.write_startup_files(proot=proot)
                result = subprocess.run(
                    [ZSH, "-dfn", str(self.home / ".zshrc")], env=self.environment,
                    capture_output=True, text=True, timeout=10,
                )
                self.assertEqual(result.returncode, 0, result.stderr)


if __name__ == "__main__":
    unittest.main()
