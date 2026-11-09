"""一時Gitリポジトリでhookを検証し、commitやpushは行わない。"""

import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
LEFTHOOK = shutil.which("lefthook")
GIT = shutil.which("git")
SH = shutil.which("sh")


@unittest.skipUnless(LEFTHOOK and GIT and SH, "lefthook・Git・shが必要です")
class GitHookTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix="git-hooks-")
        self.addCleanup(directory.cleanup)
        self.base = Path(directory.name)
        self.repo = self.base / "repo with spaces"
        self.repo.mkdir()
        self.bin = self.base / "data/data/com.termux/files/usr/bin"
        self.bin.mkdir(parents=True)
        (self.bin / "lefthook").symlink_to(LEFTHOOK)
        (self.bin / "sh").symlink_to(SH)
        self.trace = self.base / "trace"
        self.trace.write_text("")
        self.environment = {
            "HOME": str(self.base), "PATH": str(self.bin) + os.pathsep + os.defpath,
            "PREFIX": str(self.bin.parent), "LC_ALL": "C", "TRACE": str(self.trace),
            "GIT_CONFIG_GLOBAL": os.devnull, "GIT_CONFIG_NOSYSTEM": "1",
        }
        self.run_command([GIT, "init", "-q", str(self.repo)])
        # 部分stage時の退避処理にはHEADが必要。ダミーのGitオブジェクトだけを用意する。
        # 実リポジトリの履歴を使わず、git commitやpushも実行しない。
        tree = self.run_command([GIT, "hash-object", "-w", "-t", "tree", "--stdin"]).stdout.strip()
        commit = self.run_command([GIT, "hash-object", "-w", "-t", "commit", "--stdin"],
                                  data=f"tree {tree}\nauthor Fixture <fixture@example.invalid> 1 +0000\ncommitter Fixture <fixture@example.invalid> 1 +0000\n\nfixture\n").stdout.strip()
        self.run_command([GIT, "update-ref", "HEAD", commit])
        shutil.copyfile(ROOT / "lefthook.yml", self.repo / "lefthook.yml")
        shutil.copyfile(ROOT / ".gitignore", self.repo / ".gitignore")
        make = self.bin / "make"
        make.write_text(f'#!{SH}\nprintf "make %s\\n" "$*" >> "$TRACE"\nexit "${{MAKE_EXIT:-0}}"\n')
        make.chmod(0o755)
        self.run_command([LEFTHOOK, "install", "pre-commit", "pre-push"])

    def run_command(self, arguments, check=True, data="", **environment):
        return subprocess.run(arguments, cwd=self.repo, env={**self.environment, **environment},
                              input=data, capture_output=True, text=True, timeout=15, check=check)

    def stage(self, contents):
        (self.repo / "sample.txt").write_text(contents)
        self.run_command([GIT, "add", "--", "sample.txt"])

    def hook(self, name, **environment):
        hook = self.repo / ".git/hooks" / name
        # Termuxでも実行できるよう、テスト用hookだけをその環境のshへ合わせる。
        text = hook.read_text()
        hook.write_text(f"#!{SH}\n" + text.split("\n", 1)[1])
        return self.run_command([str(hook)], check=False, **environment)

    def test_config_is_valid_and_local_override_is_ignored_by_git(self):
        result = self.run_command([LEFTHOOK, "validate"])
        self.assertEqual(result.returncode, 0)
        result = self.run_command([GIT, "check-ignore", "lefthook-local.yml"])
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_precommit_accepts_clean_staged_content_without_changing_files(self):
        self.stage("clean\n")
        before = self.run_command([GIT, "diff", "--cached"]).stdout
        result = self.hook("pre-commit")
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(self.run_command([GIT, "diff", "--cached"]).stdout, before)
        self.assertEqual((self.repo / "sample.txt").read_text(), "clean\n")

    def test_precommit_rejects_staged_whitespace_without_fixing_or_restaging(self):
        self.stage("bad \n")
        before = self.run_command([GIT, "diff", "--cached"]).stdout
        result = self.hook("pre-commit")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.run_command([GIT, "diff", "--cached"]).stdout, before)
        self.assertEqual((self.repo / "sample.txt").read_text(), "bad \n")

    def test_precommit_checks_index_instead_of_unstaged_content(self):
        self.stage("clean\n")
        (self.repo / "sample.txt").write_text("unstaged \n")
        result = self.hook("pre-commit")
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual((self.repo / "sample.txt").read_text(), "unstaged \n")

    def test_prepush_runs_common_check_and_propagates_failure(self):
        self.stage("clean\n")
        # push履歴を作らず、ファイル候補だけを渡す。makeはダミーなので再帰検証しない。
        arguments = [LEFTHOOK, "run", "pre-push", "--file", "sample.txt", "--force", "--no-auto-install"]
        result = self.run_command(arguments, check=False)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        result = self.run_command(arguments, check=False, MAKE_EXIT="23")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.trace.read_text().splitlines(), ["make check", "make check"])

    def test_missing_lefthook_does_not_fall_back_to_an_installer(self):
        self.stage("clean\n")
        (self.bin / "lefthook").unlink()
        for command in ("mise", "uv", "npm", "npx", "go", "bundle", "yarn", "pnpm", "devbox"):
            path = self.bin / command
            path.write_text(f'#!{SH}\nprintf "unexpected:{command}\\n" >> "$TRACE"\nexit 99\n')
            path.chmod(0o755)
        result = self.hook("pre-commit")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.trace.read_text(), "")

    def test_generated_hook_runs_with_termux_style_interpreter_path(self):
        self.stage("clean\n")
        hook = self.repo / ".git/hooks/pre-commit"
        text = hook.read_text()
        hook.write_text(f"#!{self.bin / 'sh'}\n" + text.split("\n", 1)[1])
        result = self.run_command([str(hook)], check=False)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)
        self.assertEqual(hook.read_text().splitlines()[0], f"#!{self.bin / 'sh'}")
        result = self.run_command([str(hook)], check=False)
        self.assertEqual(result.returncode, 0, result.stderr + result.stdout)


if __name__ == "__main__":
    unittest.main()
