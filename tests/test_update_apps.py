"""明示的なAPT更新を、実際の更新なしで検証する。"""

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
        self.trace = self.base / "trace"
        self.trace.write_text("")
        for name, body in {
            "id": 'printf "%s\\n" "$TEST_UID"\n',
            "apt-get": 'printf "%s\\n" "apt-get $*" >> "$TRACE"\n'
                       '[[ "$1" != update ]] || exit "${UPDATE_EXIT:-0}"\n',
            "sudo": 'printf "%s\\n" "sudo $*" >> "$TRACE"\n"$@"\n',
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
            env={**self.environment, **environment}, timeout=10,
        )

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
