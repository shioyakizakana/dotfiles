"""任意依存の欠落・準備済み状態を、実プラグインを使わず検証する。"""

from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
ZSH = shutil.which("zsh")
BASH = shutil.which("bash")
LUA = shutil.which("lua")


class OptionalDependencyTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix="optional dependencies ")
        self.addCleanup(directory.cleanup)
        self.base = Path(directory.name)
        self.home = self.base / "home with spaces"
        self.home.mkdir()
        self.bin = self.base / "bin"
        self.bin.mkdir()
        self.environment = {"HOME": str(self.home), "PATH": str(self.bin), "TERM": "dumb"}

    def stub(self, name):
        path = self.bin / name
        path.write_text(f"#!{BASH}\nexit 0\n")
        path.chmod(0o755)

    def plugins(self):
        zdir = self.home / ".zsh"
        shutil.copytree(ROOT / "home/dot_zsh/plugin", zdir / "plugin")
        shutil.copyfile(ROOT / "home/dot_zsh/plugin.zsh", zdir / "plugin.zsh")
        self.environment["ZDIR"] = str(zdir)
        return zdir / "plugin/plugins"

    def zsh(self, command):
        return subprocess.run([ZSH, "-df", "-c", command], env=self.environment,
                              capture_output=True, text=True, timeout=10)

    @unittest.skipUnless(ZSH and BASH, "ZshとBashが必要です")
    def test_missing_zsh_plugins_do_not_produce_source_errors(self):
        self.plugins()
        result = self.zsh('source "$ZDIR/plugin.zsh"; printf "READY\\n"')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "READY\n")
        self.assertEqual(result.stderr, "")

    @unittest.skipUnless(ZSH and BASH, "ZshとBashが必要です")
    def test_fzf_load_waits_for_binary_and_both_shell_files(self):
        plugins = self.plugins()
        shell = plugins / "fzf/shell"
        shell.mkdir(parents=True)
        (shell / "key-bindings.zsh").write_text('FZF_KEYS=loaded\n')
        (shell / "completion.zsh").write_text('FZF_COMPLETION=loaded\n')
        result = self.zsh('source "$ZDIR/plugin/fzf.zsh"; _fzf_lazy_load; printf "%s\\n" "${_FZF_LAZY_LOADED:-absent}"')
        self.assertEqual(result.stdout, "absent\n", result.stderr)
        self.stub("fzf")
        result = self.zsh('source "$ZDIR/plugin/fzf.zsh"; _fzf_lazy_load; printf "%s %s %s\\n" "$_FZF_LAZY_LOADED" "$FZF_KEYS" "$FZF_COMPLETION"')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "1 loaded loaded\n")
        (shell / "completion.zsh").unlink()
        result = self.zsh('source "$ZDIR/plugin/fzf.zsh"; _fzf_lazy_load; printf "%s\\n" "${_FZF_LAZY_LOADED:-absent}"')
        self.assertEqual(result.stdout, "absent\n", result.stderr)
        self.assertEqual(result.stderr, "")

    @unittest.skipUnless(ZSH and BASH, "ZshとBashが必要です")
    def test_zeno_bootstraps_only_when_runtime_and_fzf_integration_are_ready(self):
        plugins = self.plugins()
        zeno = plugins / "zeno/zeno-bootstrap.zsh"
        zeno.parent.mkdir(parents=True)
        zeno.write_text('printf "zeno-ready\\n"\n')
        command = 'source "$ZDIR/plugin.zsh"; printf "READY\\n"'
        for name in ("fzf", "deno"):
            self.stub(name)
            result = self.zsh(command)
            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertEqual(result.stdout, "READY\n")
            self.assertEqual(result.stderr, "")
        shell = plugins / "fzf/shell"
        shell.mkdir(parents=True)
        for name in ("key-bindings.zsh", "completion.zsh"):
            (shell / name).write_text(":\n")
        result = self.zsh(command)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "zeno-ready\nREADY\n")
        self.assertEqual(result.stderr, "")

    @unittest.skipUnless(ZSH, "Zshが必要です")
    def test_available_zsh_theme_loads_with_spaces_in_home(self):
        plugins = self.plugins()
        theme = plugins / "powerlevel10k/powerlevel10k.zsh-theme"
        theme.parent.mkdir(parents=True)
        theme.write_text('printf "theme-loaded\\n"\n')
        result = self.zsh('source "$ZDIR/plugin.zsh"')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout, "theme-loaded\n")
        self.assertEqual(result.stderr, "")

    @unittest.skipUnless(LUA, "Luaが必要です")
    def test_yazi_missing_plugins_are_reported_without_aborting_initialization(self):
        result = self.lua('''
require = function(name)
  if name == "zoxide" or name == "session" then return { setup = function() end } end
  error("dummy import failure: " .. name)
end
''')
        self.assertEqual(result.returncode, 0, result.stderr)
        for name in ("git", "full-border", "bunny-private"):
            self.assertIn(name, result.stdout)
        self.assertIn("READY", result.stdout)
        self.assertNotIn("dummy import failure", result.stdout + result.stderr)

    @unittest.skipUnless(LUA, "Luaが必要です")
    def test_yazi_available_plugins_keep_setup_options(self):
        result = self.lua('''
require = function(name)
  return { setup = function(self, opts)
    if name == "zoxide" then assert(opts.update_db == true) end
    if name == "session" then assert(opts.sync_yanked == true) end
    if name == "full-border" then assert(opts.type == "rounded") end
    print("setup:" .. name)
  end }
end
''')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("warning:", result.stdout)
        self.assertEqual(result.stdout.splitlines(), [f"setup:{name}" for name in (
            "zoxide", "session", "git", "full-border", "bunny-private") ] + ["READY"])

    @unittest.skipUnless(LUA, "Luaが必要です")
    def test_yazi_setup_errors_are_not_silently_suppressed(self):
        result = self.lua('''
require = function(name)
  return { setup = function()
    if name == "git" then error("broken setup") end
  end }
end
''')
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("broken setup", result.stderr)

    def lua(self, prelude):
        # require・UI・通知だけをモック化し、実プラグインや私的設定には触れない。
        code = 'ui = { Border = { ROUNDED = "rounded" } }\nya = { err = function(message) print("warning:" .. message) end }\n'
        code += prelude + "\n" + (ROOT / "home/dot_config/yazi/init.lua").read_text() + '\nprint("READY")\n'
        return subprocess.run([LUA, "-"], input=code, env=self.environment,
                              capture_output=True, text=True, timeout=10)

    @unittest.skipUnless(BASH, "Bashが必要です")
    def test_textlint_missing_dependency_gives_manual_preparation_path(self):
        result = subprocess.run([BASH, str(ROOT / "home/dot_local/bin/executable_textlint-ja")],
                                env=self.environment, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 1)
        self.assertIn("npm ci", result.stderr)
        self.assertIn(str(self.home / ".local/share/textlint-ja"), result.stderr)
        self.assertEqual(result.stdout, "")

    @unittest.skipUnless(BASH, "Bashが必要です")
    def test_textlint_passes_configuration_and_spaced_file_argument(self):
        tool_dir = self.home / ".local/share/textlint-ja"
        executable = tool_dir / "node_modules/.bin/textlint"
        executable.parent.mkdir(parents=True)
        executable.write_text(f'#!{BASH}\nprintf "%s\\n" "$@"\nexit 7\n')
        executable.chmod(0o755)
        result = subprocess.run([BASH, str(ROOT / "home/dot_local/bin/executable_textlint-ja"), "file with spaces.md"],
                                env=self.environment, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 7)
        self.assertEqual(result.stdout.splitlines(), ["--config", str(tool_dir / ".textlintrc.json"),
            "--rulesdir", str(tool_dir), "file with spaces.md"])


if __name__ == "__main__":
    unittest.main()
