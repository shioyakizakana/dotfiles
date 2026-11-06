"""実際の導入・通信を行わずHomebrew適用処理を検証する。"""

import os
from pathlib import Path
import subprocess
import tempfile
import unittest


SOURCE = (
    Path(__file__).resolve().parents[1]
    / "home/.chezmoiscripts/run_after_install-brew.sh"
)


class HomebrewInstallTests(unittest.TestCase):
    def setUp(self):
        workspace = tempfile.TemporaryDirectory(prefix="brew apply ")
        self.addCleanup(workspace.cleanup)
        self.workspace = Path(workspace.name)
        self.fixture_home = self.workspace / "home"
        self.fixture_home.mkdir()
        (self.fixture_home / ".Brewfile").write_text('brew "dummy-package"\n')
        self.trace = self.workspace / "trace"
        self.trace.write_text("")
        self.brew = self.workspace / "bin/brew"
        self.brew.parent.mkdir()
        self.brew.write_text(
            '#!/bin/bash\n'
            'printf "brew" >> "$TRACE"\n'
            'printf " <%s>" "$@" >> "$TRACE"\n'
            'printf "\\n" >> "$TRACE"\n'
            'exit "${BREW_EXIT:-0}"\n'
        )
        self.brew.chmod(0o755)
        # PATHの探索と既知の配置先を置き換え、ホストのHomebrewを参照しない。
        self.prelude = r'''
id() { printf '%s\n' "${TEST_UID:-1000}"; }
get_brew_path() {
  if [[ "${BREW_AVAILABLE:-0}" == 1 || -f "$INSTALLED" ]]; then
    printf '%s\n' "$DUMMY_BREW"
  else
    return 1
  fi
}
curl() {
  printf 'download\n' >> "$TRACE"
  printf 'touch "$INSTALLER_STARTED"\n'
  case "${INSTALL_MODE:-ok}" in
    download-failed) return 22 ;;
    installer-failed) printf 'exit 23\n' ;;
    missing-brew) printf ':\n' ;;
    *) printf 'touch "$INSTALLED"\n' ;;
  esac
}
'''
        self.environment = {
            "HOME": str(self.fixture_home),
            "PATH": os.defpath,
            "TRACE": str(self.trace),
            "DUMMY_BREW": str(self.brew),
            "INSTALLED": str(self.workspace / "installed"),
            "INSTALLER_STARTED": str(self.workspace / "installer-started"),
        }

    def run_script(self, answers, **environment):
        # 探索と通信を差し替えてから、適用処理全体を実行する。
        arguments = [
            "bash", "-c", 'source "$1"\n' + self.prelude + '\nmain\n',
            "--", str(SOURCE),
        ]
        settings = {**self.environment, **environment}
        if settings.get("BREW_AVAILABLE") == "1":
            settings["PATH"] = str(self.brew.parent) + os.pathsep + os.defpath
        return subprocess.run(
            arguments,
            input=answers,
            capture_output=True,
            text=True,
            env=settings,
            timeout=10,
        )

    def test_resolver_finds_brew_on_path(self):
        result = subprocess.run(
            ["bash", "-c", 'source "$1"; get_brew_path', "--", str(SOURCE)],
            capture_output=True,
            text=True,
            env={
                **self.environment,
                "PATH": str(self.brew.parent) + os.pathsep + os.defpath,
            },
            timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), str(self.brew))

    def test_installed_brew_lists_and_installs_bundle_without_download(self):
        result = self.run_script("y\n", BREW_AVAILABLE="1")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("download", self.trace.read_text())
        self.assertIn("brew <bundle> <list> <--global>", self.trace.read_text())
        self.assertIn("brew <bundle> <--file>", self.trace.read_text())
        self.assertIn("brew <bundle> <cleanup>", self.trace.read_text())

    def test_direct_execution_uses_brew_on_path(self):
        result = subprocess.run(
            ["bash", str(SOURCE)],
            input="n\n",
            capture_output=True,
            text=True,
            env={
                **self.environment,
                "PATH": str(self.brew.parent) + os.pathsep + os.defpath,
            },
            timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.trace.read_text(), "brew <bundle> <list> <--global>\n")

    def test_missing_brew_can_be_declined_without_bundle(self):
        result = self.run_script("n\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.trace.read_text(), "")

    def test_root_skips_new_installation_without_download(self):
        result = self.run_script("y\ny\n", TEST_UID="0")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("root", result.stdout)
        self.assertEqual(self.trace.read_text(), "")

    def test_root_can_use_existing_brew_without_installing_it(self):
        result = self.run_script("n\n", BREW_AVAILABLE="1", TEST_UID="0")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.trace.read_text(), "brew <bundle> <list> <--global>\n")

    def test_new_install_is_found_before_running_bundle(self):
        result = self.run_script("y\ny\n")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(self.trace.read_text().startswith("download\n"))
        self.assertIn("brew <bundle> <--file>", self.trace.read_text())

    def test_download_failure_stops_before_running_bundle(self):
        result = self.run_script("y\ny\n", INSTALL_MODE="download-failed")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.trace.read_text(), "download\n")
        self.assertFalse(Path(self.environment["INSTALLER_STARTED"]).exists())

    def test_installer_failure_stops_before_running_bundle(self):
        result = self.run_script("y\ny\n", INSTALL_MODE="installer-failed")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.trace.read_text(), "download\n")
        self.assertTrue(Path(self.environment["INSTALLER_STARTED"]).exists())

    def test_installer_without_brew_is_reported_as_failure(self):
        result = self.run_script("y\ny\n", INSTALL_MODE="missing-brew")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.trace.read_text(), "download\n")

    def test_bundle_can_be_declined_without_installing_packages(self):
        result = self.run_script("n\n", BREW_AVAILABLE="1")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.trace.read_text(), "brew <bundle> <list> <--global>\n")

    def test_bundle_failure_stops_before_cleanup(self):
        result = self.run_script("y\n", BREW_AVAILABLE="1", BREW_EXIT="17")
        self.assertEqual(result.returncode, 17, result.stderr)
        self.assertEqual(self.trace.read_text(), "brew <bundle> <list> <--global>\n")

    def test_missing_brewfile_skips_bundle(self):
        (self.fixture_home / ".Brewfile").unlink()
        result = self.run_script("", BREW_AVAILABLE="1")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.trace.read_text(), "")


if __name__ == "__main__":
    unittest.main()
