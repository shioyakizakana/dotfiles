"""隔離HOMEとダミーツールでBash・Zshの起動設定を検証する。"""

import os
from pathlib import Path
import re
import shlex
import shutil
import subprocess
import tempfile
import unittest

from chezmoi_template import render_template


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

    def write_startup_files(self, proot=False, termux=None):
        data = {"prootUbuntu": proot}
        if termux is not None:
            data["termux"] = termux
        for name, text in (
            (".bashrc", (ROOT / "home/dot_bashrc").read_text()),
            (".zshrc", render_template(ROOT / "home/dot_zshrc.tmpl", data)),
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
        environment.write_text(render_template(common / "env.sh.tmpl", data).replace(
            "/snap/bin", str(self.base / "snap/bin")))

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

    def test_zeno_child_uses_termux_sqlite_only_for_termux_without_override(self):
        prefix = self.base / "termux prefix"
        library = prefix / "lib/libsqlite3.so"
        library.parent.mkdir(parents=True)
        library.write_text("dummy library; never loaded\n")
        self.environment["PREFIX"] = str(prefix)
        self.stub("deno", 'printf "%s\\n" "${DENO_SQLITE_PATH:-unset}"\n')
        for termux, proot, override, expected in (
            (True, False, None, str(library)),
            (True, False, "/custom/sqlite.so", "/custom/sqlite.so"),
            (False, False, None, "unset"),
            (False, True, None, "unset"),
            (None, False, None, "unset"),
        ):
            with self.subTest(termux=termux, proot=proot, override=override):
                self.write_startup_files(proot=proot, termux=termux)
                (self.home / ".zsh/plugin.zsh").write_text("deno\n")
                environment = {} if override is None else {"DENO_SQLITE_PATH": override}
                result = self.run_shell("zsh", ":", **environment)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, expected + "\n", result.stderr)

    def test_termux_does_not_select_missing_sqlite_or_relative_prefix(self):
        self.write_startup_files(termux=True)
        for prefix in ("", "relative/prefix", str(self.base / "absent prefix")):
            with self.subTest(prefix=prefix):
                result = self.run_shell("zsh", 'printf "%s\\n" "${DENO_SQLITE_PATH:-unset}"',
                                        PREFIX=prefix)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout, "unset\n")

    def test_snapshot_function_preserves_arguments_and_exit_status(self):
        script = self.local_bin / "nvim-snapshot.py"
        script.write_text("# fixture\n")
        self.stub("python3", 'printf "<%s>\n" "$@"\nexit 23\n')
        for shell in ("bash", "zsh"):
            with self.subTest(shell=shell):
                result = self.run_shell(shell, "nvim_snapshot save --note 'spaces and $(literal)' ''")
                self.assertEqual(result.returncode, 23, result.stderr)
                self.assertEqual(result.stdout.splitlines(), [f"<{script}>", "<save>", "<--note>", "<spaces and $(literal)>", "<>"])

    def test_snapshot_function_handles_missing_python_or_script(self):
        for shell in ("bash", "zsh"):
            with self.subTest(shell=shell):
                result = self.run_shell(shell, f'PATH={shlex.quote(str(self.bin))}\nprintf "%s\\n" "$TEST_STARTUP_STATUS"; nvim_snapshot list')
                self.assertEqual(result.returncode, 127)
                self.assertEqual(result.stdout.strip(), "0")
                self.assertIn("Python", result.stderr)
        self.stub("python3", 'exit 99\n')
        for shell in ("bash", "zsh"):
            result = self.run_shell(shell, 'nvim_snapshot list')
            self.assertEqual(result.returncode, 127)
            self.assertIn("nvim-snapshot.py", result.stderr)

    def test_snapshot_definition_is_repeatable_without_running_cli_or_changing_shell(self):
        self.stub("python3", 'printf "UNEXPECTED\n" >> "$TRACE"\n')
        for shell in ("bash", "zsh"):
            with self.subTest(shell=shell):
                self.trace.write_text("")
                result = self.run_shell(shell, 'before_pwd=$PWD; before_umask=$(umask); before_path=$PATH; before_options=$-\n. "$HOME/.config/shell/functions.sh"\n. "$HOME/.config/shell/functions.sh"\n[ "$PWD" = "$before_pwd" ] && [ "$(umask)" = "$before_umask" ] && [ "$PATH" = "$before_path" ] && [ "$-" = "$before_options" ]')
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertNotIn("同名", result.stderr)
                self.assertNotIn("UNEXPECTED", self.trace.read_text())

    def test_existing_legacy_snapshot_function_is_preserved(self):
        legacy = self.home / "scripts/shell/funciton.sh"
        legacy.parent.mkdir(parents=True)
        legacy.write_text('nvim_snapshot() { printf "legacy\\n"; }\n')
        for shell in ("bash", "zsh"):
            with self.subTest(shell=shell):
                result = self.run_shell(shell, 'nvim_snapshot')
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.strip(), "legacy")
                self.assertIn("同名", result.stderr)

    def test_snapshot_git_ignore_is_explicit_without_ignoring_cli(self):
        git = shutil.which("git")
        result = subprocess.run([git, "check-ignore", "--no-index", "--stdin"], cwd=ROOT,
                                input="home/dot_config/nvim/lazy-lock.json\nhome/dot_local/bin/executable_nvim-snapshot.py\n",
                                capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.splitlines(), ["home/dot_config/nvim/lazy-lock.json"])

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

    def test_proot_prefers_local_mise_for_startup_and_child_commands(self):
        self.write_startup_files(proot=True)
        local_mise = self.local_bin / "mise"
        local_mise.write_text(
            f'#!{BASH}\nprintf "%s\\n" "linux-mise $*" >> "$TRACE"\nprintf ":\\n"\n'
        )
        local_mise.chmod(0o755)
        self.environment["PATH"] += ":" + str(self.local_bin)
        for shell in ("bash", "zsh"):
            with self.subTest(shell=shell):
                self.trace.write_text("")
                result = self.run_shell(shell,
                    '. "$HOME/.config/shell/env.sh"\n'
                    '. "$HOME/.config/shell/env.sh"\n'
                    f'"{BASH}" -c \'mise --version\'\n'
                    'printf "%s\\n" "$PATH"')
                self.assertEqual(result.returncode, 0, result.stderr)
                trace = self.trace.read_text().splitlines()
                self.assertIn(f"linux-mise activate {shell}", trace)
                self.assertIn("linux-mise --version", trace)
                self.assertFalse(any(line.startswith("mise ") for line in trace), trace)
                self.assertEqual(result.stdout.splitlines()[-1].split(":").count(str(self.local_bin)), 1)

    def test_non_proot_and_termux_keep_mise_path_priority(self):
        local_mise = self.local_bin / "mise"
        local_mise.write_text(f'#!{BASH}\nprintf "forbidden:local-mise\\n" >> "$TRACE"\nexit 91\n')
        local_mise.chmod(0o755)
        self.environment["PATH"] += ":" + str(self.local_bin)
        for proot, termux in ((False, False), (False, True), (True, True)):
            self.write_startup_files(proot=proot, termux=termux)
            for shell in ("bash", "zsh"):
                with self.subTest(proot=proot, termux=termux, shell=shell):
                    self.trace.write_text("")
                    result = self.run_shell(shell, ":")
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertIn(f"mise activate {shell}", self.trace.read_text())
                    self.assertNotIn("forbidden:local-mise", self.trace.read_text())

    def test_startup_without_npm_does_not_add_an_implicit_bin_path(self):
        for shell in ("bash", "zsh"):
            with self.subTest(shell=shell):
                result = self.run_shell(shell,
                    'printf "%s\\n" "${NPM_GLOBAL_PREFIX-unset}" "$PATH"')
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertNotIn("npm", result.stderr)
                prefix, path = result.stdout.splitlines()
                self.assertEqual(prefix, "unset")
                self.assertNotIn("/bin", path.split(":"))

    def test_explicit_npm_prefix_is_preserved_and_only_existing_absolute_bin_is_added(self):
        prefix = self.base / "npm prefix with spaces"
        (prefix / "bin").mkdir(parents=True)
        # 存在する相対パスも候補にし、存在確認だけで追加されないことを確かめる。
        relative = os.path.relpath(prefix)
        self.stub("npm", 'printf "forbidden:npm\\n" >> "$TRACE"\nexit 91\n')
        for shell in ("bash", "zsh"):
            for value, expected in (
                (str(prefix), True), (str(prefix) + "/", True),
                ("", False), (relative, False), (str(self.base / "missing prefix"), False),
            ):
                with self.subTest(shell=shell, prefix=value):
                    self.trace.write_text("")
                    result = self.run_shell(shell,
                        '. "$HOME/.config/shell/env.sh"\n'
                        'printf "<%s>\\n%s\\n" "$NPM_GLOBAL_PREFIX" "$PATH"',
                        NPM_GLOBAL_PREFIX=value)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertNotIn("forbidden:npm", self.trace.read_text())
                    value_line, path = result.stdout.splitlines()
                    self.assertEqual(value_line, f"<{value}>")
                    self.assertEqual(path.split(":").count(str(prefix / "bin")), int(expected))
                    self.assertNotIn("/bin", path.split(":"))
                    self.assertNotIn(relative + "/bin", path.split(":"))

    def test_common_path_keeps_termux_and_mise_paths_without_querying_npm(self):
        native_bin = self.base / "termux prefix/bin"
        runtime_bin = self.base / "mise runtime/bin"
        native_bin.mkdir(parents=True)
        runtime_bin.mkdir(parents=True)
        self.environment["PATH"] += ":" + str(native_bin)
        self.environment["PREFIX"] = str(native_bin.parent)
        self.stub("npm", 'printf "forbidden:npm\\n" >> "$TRACE"\nexit 91\n')
        activation = f'export PATH={shlex.quote(str(runtime_bin))}:"$PATH"'
        self.stub("mise", f"printf '%s\\n' {shlex.quote(activation)}\n")
        for termux in (False, True):
            self.write_startup_files(proot=not termux, termux=termux)
            for shell in ("bash", "zsh"):
                with self.subTest(shell=shell, termux=termux):
                    self.trace.write_text("")
                    result = self.run_shell(shell,
                        '. "$HOME/.config/shell/env.sh"\nprintf "%s\\n" "$PATH"')
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertNotIn("forbidden:npm", self.trace.read_text())
                    paths = result.stdout.strip().split(":")
                    self.assertEqual(paths[0], str(runtime_bin))
                    self.assertEqual(paths.count(str(runtime_bin)), 1)
                    self.assertEqual(paths.count(str(native_bin)), 1)
                    self.assertLess(paths.index(str(native_bin)), paths.index(str(self.local_bin)))

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
        self.stub("chezmoi", ":\n")
        self.stub("nvim", ":\n")
        for shell in ("bash", "zsh"):
            with self.subTest(shell=shell):
                self.trace.write_text("")
                result = self.run_shell(shell, 'upd apt\nalias reload\nalias cmlg\nalias nvlg')
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("update_apps apt\n", self.trace.read_text())
                self.assertIn(f"~/.{shell}rc", result.stdout)
                self.assertIn("nvim +LazyGit", result.stdout)

    def test_missing_replacement_tools_leave_standard_commands_available(self):
        for name in ("cat", "rm", "grep", "man", "find", "ls"):
            self.stub(name, f'printf "standard-{name}\\n"\n')
        for shell in ("bash", "zsh"):
            with self.subTest(shell=shell):
                result = self.run_shell(shell, "cat\nrm\ngrep\nman\nfind\nls")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.splitlines(), [
                    f"standard-{name}" for name in ("cat", "rm", "grep", "man", "find", "ls")
                ])

    def test_available_replacement_tools_receive_alias_arguments(self):
        for name in ("bat", "gomi", "rg", "tldr", "fd", "eza"):
            self.stub(name, f'printf "{name} %s\\n" "$*"\n')
        for shell in ("bash", "zsh"):
            with self.subTest(shell=shell):
                result = self.run_shell(shell, "cat sample\nrm sample\ngrep word\nman topic\nfind dir\nls\nlt")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.splitlines(), [
                    "bat --paging=never sample", "gomi sample", "rg word", "tldr topic",
                    "fd dir", "eza --group-directories-first", "eza --tree --level=2 --group-directories-first",
                ])

    def test_man_alias_follows_tldr_when_switching_from_tealdeer_to_tlrc(self):
        self.stub("tldr", 'printf "tealdeer %s\\n" "$*"\n')
        tlrc_bin = self.base / "tlrc/bin"
        tlrc_bin.mkdir(parents=True)
        executable = tlrc_bin / "tldr"
        executable.write_text(f'#!{BASH}\nprintf "tlrc %s\\n" "$*"\n')
        executable.chmod(0o755)
        for shell in ("bash", "zsh"):
            with self.subTest(shell=shell):
                result = self.run_shell(
                    shell, 'man topic\nPATH="$TLRC_BIN:$PATH"\nman topic\ntldr --version',
                    TLRC_BIN=str(tlrc_bin),
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertEqual(result.stdout.splitlines(), [
                    "tealdeer topic", "tlrc topic", "tlrc --version",
                ])

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
