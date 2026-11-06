"""APTとsudoをダミーにしてroot・非root・失敗時の動作を検証する。"""

from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


SOURCE = (
    Path(__file__).resolve().parents[1]
    / "home/.chezmoiscripts/run_after_install-apt.sh"
)
BASH = shutil.which("bash")


class AptInstallTests(unittest.TestCase):
    def setUp(self):
        workspace = tempfile.TemporaryDirectory(prefix="apt policy ")
        self.addCleanup(workspace.cleanup)
        self.base = Path(workspace.name)
        self.bin = self.base / "bin"
        self.bin.mkdir()
        self.trace = self.base / "trace"
        self.trace.write_text("")
        self.command(
            "id", 'printf "%s\\n" "$TEST_UID"\n'
        )
        self.command(
            "apt",
            'printf "apt %s\\n" "$*" >> "$TRACE"\n'
            'if [[ "$1" == update ]]; then exit "${UPDATE_EXIT:-0}"; fi\n',
        )
        self.command(
            "sudo", 'printf "sudo %s\\n" "$*" >> "$TRACE"\n"$@"\n'
        )
        self.environment = {
            "HOME": str(self.base),
            "PATH": str(self.bin),
            "TRACE": str(self.trace),
            "TEST_UID": "1000",
        }

    def command(self, name, content):
        path = self.bin / name
        path.write_text(f"#!{BASH}\n" + content)
        path.chmod(0o755)

    def run_script(self, answers="y\n", **environment):
        return subprocess.run(
            [BASH, "-c", 'source "$1"; main', "--", str(SOURCE)],
            input=answers,
            capture_output=True,
            text=True,
            env={**self.environment, **environment},
            timeout=10,
        )

    def test_root_runs_apt_without_sudo(self):
        (self.bin / "sudo").unlink()
        result = self.run_script(TEST_UID="0")
        self.assertEqual(result.returncode, 0, result.stderr)
        trace = self.trace.read_text()
        self.assertIn("apt update -y\n", trace)
        self.assertIn("apt upgrade -y\n", trace)
        self.assertIn("apt install -y ", trace)
        self.assertNotIn("sudo", trace)

    def test_non_root_uses_sudo_for_apt(self):
        result = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        trace = self.trace.read_text()
        self.assertIn("sudo apt update -y\n", trace)
        self.assertIn("sudo apt upgrade -y\n", trace)
        self.assertIn("sudo apt install -y ", trace)

    def test_non_root_without_sudo_stops_before_apt(self):
        (self.bin / "sudo").unlink()
        result = self.run_script()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("sudo", result.stderr)
        self.assertEqual(self.trace.read_text(), "")

    def test_missing_apt_stops_before_sudo(self):
        (self.bin / "apt").unlink()
        result = self.run_script()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("apt", result.stderr)
        self.assertEqual(self.trace.read_text(), "")

    def test_failed_update_does_not_upgrade_or_install(self):
        result = self.run_script(UPDATE_EXIT="17")
        self.assertEqual(result.returncode, 17, result.stderr)
        self.assertNotIn("upgrade", self.trace.read_text())
        self.assertNotIn("install", self.trace.read_text())

    def test_decline_runs_no_package_commands(self):
        result = self.run_script("n\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.trace.read_text(), "")

    def test_eof_runs_no_package_commands(self):
        result = self.run_script("")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.trace.read_text(), "")


if __name__ == "__main__":
    unittest.main()
