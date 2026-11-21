"""初期登録の専用入口と、認証を実行しないBash・Zsh補完を検証する。"""

import json
from pathlib import Path
import shlex
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASH = shutil.which("bash")
ZSH = shutil.which("zsh")
CHEZMOI = shutil.which("chezmoi")


class ProtonCompletionTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix="")
        self.addCleanup(directory.cleanup)
        self.base = Path(directory.name)
        self.home = self.base / "home with spaces"
        self.bin = self.home / ".local/bin"
        self.bin.mkdir(parents=True)
        self.helper = self.bin / "proton-pass-key-cache.py"
        source = (ROOT / "home/dot_local/bin/private_executable_proton-pass-key-cache.py.tmpl").read_text()
        # シバンの展開はsetupテストで確認し、ここでは補完処理を検証する。
        self.helper.write_text(f"#!{sys.executable}\n" + source.partition("\n")[2])
        self.helper.chmod(0o755)
        (self.bin / "python3").symlink_to(sys.executable)
        self.trace = self.base / "trace"
        self.env = {"HOME": str(self.home), "PATH": str(self.bin), "TRACE": str(self.trace),
                    "PROTON_PASS_CACHE_TTL": "invalid", "PROTON_PASS_KEY_PROVIDER": "invalid"}
        for name in ("age", "pass-cli"):
            stub = self.bin / name
            stub.write_text(f'#!{BASH}\nprintf "unexpected\\n" >> "$TRACE"\nexit 99\n')
            stub.chmod(0o755)

    def complete(self, command, *words):
        result = subprocess.run([sys.executable, "-B", str(self.helper), "complete", command, *words],
                                env=self.env, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.trace.exists())
        self.assertFalse((self.home / ".cache").exists())
        return result.stdout.splitlines()

    def profiles(self):
        root = self.home / ".local/share/proton-pass/projects"
        for name in ("alpha", "beta", "invalid name", "global"):
            (root / name).mkdir(parents=True)
        (root / "linked").symlink_to(root / "alpha")
        (root / "file").write_text("dummy file, not a project")
        return root

    def test_completion_never_initializes_or_authenticates(self):
        self.assertIn("--profile", self.complete("proton-pass", ""))
        self.assertEqual(self.complete("proton-pass", "--profile", ""), ["global"])
        self.assertFalse((self.home / ".local/share").exists())

    def test_registered_names_are_filtered_without_opening_ciphertexts(self):
        root = self.profiles()
        # 暗号文を開く実装ならFIFOで停止する。補完は名前だけを読む。
        import os
        os.mkfifo(root / "alpha/token.age")
        self.assertEqual(self.complete("proton-pass", "--profile", ""), ["global", "alpha", "beta"])
        self.assertEqual(self.complete("proton-pass", "--profile", "a"), ["alpha"])
        self.assertEqual(self.complete("setup-proton-pass-project", ""), ["--help", "alpha", "beta"])

    def test_cache_options_and_values_follow_argument_position(self):
        command = "proton-pass-key-cache.py"
        self.assertEqual(self.complete(command, "--ttl-minutes", ""), ["15", "30", "45", "60"])
        self.assertEqual(self.complete(command, "--ttl-minutes", "3"), ["30"])
        choices = self.complete(command, "--profile", "alpha", "--ttl-minutes", "30", "")
        self.assertEqual(choices, ["--help", "unlock", "status", "lock", "run"])
        self.assertEqual(self.complete(command, "unlock", ""), [])
        self.assertNotIn("configure", self.complete(command, ""))
        self.assertNotIn("_serve", self.complete(command, ""))
        self.assertEqual(self.complete("proton-pass", "--profile", "alpha", "lo"), ["login", "logout"])
        self.assertEqual(self.complete("proton-pass", "--profile", "alpha", "login", ""), [])
        self.assertEqual(self.complete("proton-pass", "info", "--profile", ""), [])
        self.assertEqual(self.complete(command, "unlock", "--ttl-minutes", ""), [])

    @unittest.skipUnless(BASH and ZSH, "Bash・Zshが必要です")
    def test_bash_and_zsh_use_same_dynamic_candidates(self):
        self.profiles()
        bash_source = ROOT / "home/dot_config/bash/completions/proton-pass.bash"
        zsh_source = ROOT / "home/dot_zsh/completions/_proton-pass"
        for words, expected in (
            (["proton-pass", "--profile", "a"], ["alpha"]),
            (["proton-pass-key-cache.py", "--profile", "alpha", "--ttl-minutes", ""], ["15", "30", "45", "60"]),
            (["setup-proton-pass-project", "b"], ["beta"]),
        ):
            with self.subTest(words=words):
                quoted = shlex.join(words)
                bash = f'source "$1"; COMP_WORDS=({quoted}); COMP_CWORD={len(words)-1}; _proton_pass_complete; printf "%s\\n" "${{COMPREPLY[@]}}"'
                zsh = f'compadd() {{ shift; local array=$1; print -rl -- "${{(@P)array}}"; }}; words=({quoted}); CURRENT={len(words)}; source "$1"'
                for shell, code, source in ((BASH, bash, bash_source), (ZSH, zsh, zsh_source)):
                    result = subprocess.run([shell, "-fc", code, "test", str(source)], env=self.env,
                                            capture_output=True, text=True, timeout=10)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(result.stdout.splitlines(), expected)
        self.assertFalse(self.trace.exists())
        self.assertFalse((self.home / ".cache").exists())

    @unittest.skipUnless(BASH, "Bashが必要です")
    def test_loading_bash_completion_does_not_run_python(self):
        self.helper.write_text(f'#!{BASH}\nprintf "unexpected\\n" >> "$TRACE"\n')
        result = subprocess.run([BASH, "-fc", 'source "$1"; complete -p proton-pass-key-cache.py',
                                 "test", str(ROOT / "home/dot_config/bash/completions/proton-pass.bash")],
                                env=self.env, capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("_proton_pass_complete", result.stdout)
        self.assertFalse(self.trace.exists())

    @unittest.skipUnless(BASH and ZSH, "Bash・Zshが必要です")
    def test_subcommand_values_are_not_forwarded_to_completion_process(self):
        self.helper.write_text(f'#!{BASH}\nprintf "%s\\n" "$@" > "$TRACE"\n')
        for words in (["proton-pass", "login", "--pat", "dummy-private-value", ""],
                      ["proton-pass-key-cache.py", "run", "--", "app", "dummy-private-value", ""]):
            quoted = shlex.join(words)
            for shell, code, source in (
                (BASH, f'source "$1"; COMP_WORDS=({quoted}); COMP_CWORD={len(words)-1}; _proton_pass_complete',
                 ROOT / "home/dot_config/bash/completions/proton-pass.bash"),
                (ZSH, f'words=({quoted}); CURRENT={len(words)}; source "$1"',
                 ROOT / "home/dot_zsh/completions/_proton-pass"),
            ):
                with self.subTest(shell=shell, words=words):
                    result = subprocess.run([shell, "-fc", code, "test", str(source)], env=self.env,
                                            capture_output=True, text=True, timeout=10)
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertFalse(self.trace.exists())

    @unittest.skipUnless(BASH and CHEZMOI, "Bash・chezmoiが必要です")
    def test_setup_entry_delegates_to_checkout_and_rejects_global(self):
        source = self.base / "checkout ' $literal `literal`"
        (source / "home").mkdir(parents=True)
        (source / ".chezmoiroot").write_text("home\n")
        (source / "bootstrap").mkdir()
        bootstrap = source / "bootstrap/setup-proton-pass.sh"
        bootstrap.write_text('printf "%s\\n" "$@" > "$TRACE"\nexit 17\n')
        config = self.base / "config.json"
        config.write_text(json.dumps({"data": {}}))
        result = subprocess.run(
            [CHEZMOI, "--config", str(config), "--source", str(source),
             "--destination", str(self.home), "--cache", str(self.base / "cache"),
             "--persistent-state", str(self.base / "state.db"),
             "--refresh-externals=never", "--no-tty", "execute-template"],
            input=(ROOT / "home/dot_local/bin/executable_setup-proton-pass-project.tmpl").read_text(),
            env=self.env, capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        entry = self.base / "setup-entry"
        entry.write_text(result.stdout)
        (self.bin / "bash").symlink_to(BASH)
        for arguments in ([], ["global"], ["../escape"], ["alpha", "extra"], ["--help"]):
            execution = subprocess.run([BASH, str(entry), *arguments], env=self.env,
                                       capture_output=True, text=True, timeout=10)
            self.assertEqual(execution.returncode, 0 if arguments == ["--help"] else 1)
            self.assertFalse(self.trace.exists())
        execution = subprocess.run([BASH, str(entry), "alpha"], env=self.env,
                                   capture_output=True, text=True, timeout=10)
        self.assertEqual(execution.returncode, 17, execution.stderr)
        self.assertEqual(self.trace.read_text().splitlines(), ["--profile", "alpha", "env"])
