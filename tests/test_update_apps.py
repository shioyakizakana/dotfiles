"""明示的なAPT・mise更新を、実際の更新なしで検証する。"""

from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


SOURCE = Path(__file__).resolve().parents[1] / "home/dot_local/bin/executable_update_apps"
BASH = shutil.which("bash")


class UpdateAppsTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix="explicit updates ")
        self.addCleanup(directory.cleanup)
        self.base = Path(directory.name)
        self.bin = self.base / "bin"
        self.bin.mkdir()
        self.project = self.base / "project"
        self.project.mkdir()
        (self.project / "mise.toml").write_text('[tools]\nnode = "20"\n')
        self.trace = self.base / "trace"
        self.trace.write_text("")
        for name, body in {
            "id": 'printf "%s\\n" "$TEST_UID"\n',
            "apt-get": 'printf "%s\\n" "apt-get $*" >> "$TRACE"\n'
                       '[[ "$1" != update ]] || exit "${UPDATE_EXIT:-0}"\n',
            "sudo": 'printf "%s\\n" "sudo $*" >> "$TRACE"\n"$@"\n',
            "mise": '''printf 'mise' >> "$TRACE"
printf ' <%s>' "$@" >> "$TRACE"
printf '\\n' >> "$TRACE"
if [[ "${1:-}" == --cd ]]; then
  cd -- "$2" || exit 1
  shift 2
fi
printf 'mise-target <%s> <%s>\\n' "$PWD" "$1" >> "$TRACE"
case "$1" in
  outdated)
    printf '%s\\n' "${OUTDATED_OUTPUT:-All tools are up to date}"
    exit "${OUTDATED_EXIT:-0}"
    ;;
  upgrade) exit "${UPGRADE_EXIT:-0}" ;;
  *) exit 2 ;;
esac
''',
        }.items():
            executable = self.bin / name
            executable.write_text(f"#!{BASH}\n" + body)
            executable.chmod(0o755)
        self.environment = {
            "HOME": str(self.base), "PATH": str(self.bin),
            "TRACE": str(self.trace), "TEST_UID": "1000",
        }

    def run_command(self, *arguments, **environment):
        return subprocess.run(
            [BASH, str(SOURCE), *arguments], capture_output=True, text=True,
            env={**self.environment, **environment}, cwd=self.project, timeout=10,
        )

    def mise_calls(self, *commands):
        return [line for command in commands for line in (
            f"mise <--cd> <{self.base}> <{command}>",
            f"mise-target <{self.base}> <{command}>",
        )]

    def test_mise_updates_home_tools_from_another_project(self):
        result = self.run_command("mise")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.trace.read_text().splitlines(),
                         self.mise_calls("outdated", "upgrade"))

    def test_mise_outdated_candidates_allow_upgrade(self):
        result = self.run_command("mise", OUTDATED_OUTPUT="node 24.0.0 24.1.0")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("node 24.0.0 24.1.0", result.stdout)
        self.assertEqual(self.trace.read_text().splitlines(),
                         self.mise_calls("outdated", "upgrade"))

    def test_mise_outdated_failure_stops_before_upgrade(self):
        for status in (1, 17):
            with self.subTest(status=status):
                self.trace.write_text("")
                result = self.run_command("mise", OUTDATED_EXIT=str(status))
                self.assertEqual(result.returncode, 1, result.stderr)
                self.assertIn("FAILED: mise", result.stdout)
                self.assertEqual(self.trace.read_text().splitlines(),
                                 self.mise_calls("outdated"))

    def test_mise_upgrade_failure_is_reported(self):
        result = self.run_command("mise", UPGRADE_EXIT="23")
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("FAILED: mise", result.stdout)
        self.assertNotIn("SUCCESS: mise", result.stdout)
        self.assertEqual(self.trace.read_text().splitlines(),
                         self.mise_calls("outdated", "upgrade"))

    def test_mise_failure_keeps_other_targets_and_final_failure(self):
        result = self.run_command("mise", "apt", OUTDATED_EXIT="17")
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertIn("SUCCESS: apt", result.stdout)
        trace = self.trace.read_text().splitlines()
        self.assertEqual(trace[:2], self.mise_calls("outdated"))
        self.assertIn("apt-get upgrade -y", trace)
        self.assertIn("1 update target(s) failed.", result.stdout)

    def test_missing_mise_is_skipped_without_updates(self):
        (self.bin / "mise").unlink()
        result = self.run_command("mise")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.trace.read_text(), "")

    def test_root_can_explicitly_update_without_sudo(self):
        (self.bin / "sudo").unlink()
        result = self.run_command("apt", TEST_UID="0")
        self.assertEqual(result.returncode, 0, result.stderr)
        trace = self.trace.read_text()
        self.assertIn("apt-get upgrade -y\n", trace)
        self.assertIn("apt-get autoremove -y\n", trace)
        self.assertNotIn("sudo", trace)

    def test_non_root_uses_sudo(self):
        result = self.run_command("apt")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("sudo apt-get upgrade -y\n", self.trace.read_text())

    def test_non_root_without_sudo_is_failure(self):
        (self.bin / "sudo").unlink()
        result = self.run_command("apt")
        self.assertEqual(result.returncode, 1)
        self.assertEqual(self.trace.read_text(), "")

    def test_update_failure_stops_upgrade_and_cleanup(self):
        result = self.run_command("apt", UPDATE_EXIT="17")
        self.assertEqual(result.returncode, 1)
        self.assertNotIn("upgrade", self.trace.read_text())
        self.assertNotIn("autoremove", self.trace.read_text())

    def test_no_target_does_not_update(self):
        result = self.run_command()
        self.assertEqual(result.returncode, 2)
        self.assertEqual(self.trace.read_text(), "")

    def test_invalid_target_does_not_update(self):
        result = self.run_command("unknown")
        self.assertEqual(result.returncode, 2)
        self.assertEqual(self.trace.read_text(), "")


if __name__ == "__main__":
    unittest.main()
