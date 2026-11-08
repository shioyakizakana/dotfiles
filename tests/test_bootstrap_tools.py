"""ローカルのダミーだけでインストーラーの実行と後始末を検証する。"""

import os
from pathlib import Path
import subprocess
import tempfile
import unittest


SOURCE = Path(__file__).resolve().parents[1] / "bootstrap/bootstrap-tools.sh"

PRELUDE = r'''
source "$1"
curl() {
  local destination=''
  while (($# > 0)); do
    if [[ "$1" == -o ]]; then
      destination="$2"
      break
    fi
    shift
  done
  [[ -n "$destination" ]] || return 2
  printf '%s\n' "$destination" > "$DOWNLOAD_PATH"
  cat "$DUMMY_INSTALLER" > "$destination"
  return "${DOWNLOAD_EXIT:-0}"
}
'''

CHECK_PRELUDE = '''
check_environment() { :; }
install_base_tools() { return 97; }
install_chezmoi() { return 97; }
install_proton_pass() { return 97; }
install_mise() { return 97; }
install_homebrew() { return 97; }
'''


class BootstrapInstallerTests(unittest.TestCase):
    def setUp(self):
        workspace = tempfile.TemporaryDirectory(prefix="bootstrap tools ")
        self.addCleanup(workspace.cleanup)
        self.workspace = Path(workspace.name)
        self.download_path = self.workspace / "download-path"
        self.executed_script = self.workspace / "executed-script"
        self.arguments = self.workspace / "arguments"
        installer = self.workspace / "dummy-installer.sh"
        installer.write_text(
            'printf "%s\\n" "$0" > "$EXECUTED_SCRIPT"\n'
            'for argument do printf "%s\\n" "$argument"; done > "$ARGUMENTS"\n'
            'exit "${INSTALLER_EXIT:-0}"\n'
        )
        # 実際の認証情報を継承せず、出力先はテスト用ディレクトリに限定する。
        self.environment = {
            "PATH": os.defpath,
            "HOME": str(Path.home()),
            "TMPDIR": str(self.workspace),
            "DUMMY_INSTALLER": str(installer),
            "DOWNLOAD_PATH": str(self.download_path),
            "EXECUTED_SCRIPT": str(self.executed_script),
            "ARGUMENTS": str(self.arguments),
        }

    def run_shell(self, body, **environment):
        return subprocess.run(
            ["bash", "-c", PRELUDE + body, "--", str(SOURCE)],
            input="",
            capture_output=True,
            text=True,
            env={**self.environment, **environment},
            timeout=10,
        )

    def assert_download_removed(self):
        downloaded = Path(self.download_path.read_text().strip())
        self.assertFalse(downloaded.exists())
        return downloaded

    def test_direct_execution_still_shows_help_without_installing(self):
        result = subprocess.run(
            ["bash", str(SOURCE), "--help"],
            input="",
            capture_output=True,
            text=True,
            env=self.environment,
            timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--install", result.stdout)
        self.assertFalse(self.download_path.exists())

    def test_check_mode_reports_manual_dependencies_without_creating_home_files(self):
        home = self.workspace / "empty home"
        home.mkdir()
        result = self.run_shell(CHECK_PRELUDE + '''
has_tool() { [[ "$1" == python3 || "$1" == zsh ]]; }
get_brew_path() { return 1; }
main --check
''', HOME=str(home))
        self.assertEqual(result.returncode, 0, result.stderr)
        for tool in ("python3", "zsh"):
            self.assertIn(f"[OK] {tool}\n", result.stdout)
        for tool in ("fzf", "luarocks", "make", "openssl", "wget", "flock"):
            self.assertIn(f"[--] {tool}\n", result.stdout)
        self.assertIn("docs/setup/dependencies.md", result.stdout)
        self.assertEqual(list(home.iterdir()), [])
        self.assertFalse(self.download_path.exists())

    def test_check_mode_leaves_existing_home_files_unchanged(self):
        home = self.workspace / "existing home"
        home.mkdir()
        existing = home / "existing.txt"
        existing.write_text("keep\n")
        result = self.run_shell(CHECK_PRELUDE + '''
has_tool() { return 0; }
get_brew_path() { printf '/dummy/brew\\n'; }
main --check
''', HOME=str(home))
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotIn("[--]", result.stdout)
        self.assertEqual(list(home.iterdir()), [existing])
        self.assertEqual(existing.read_text(), "keep\n")
        self.assertFalse(self.download_path.exists())

    def test_chezmoi_installer_receives_destination(self):
        result = self.run_shell(
            '\nhas_tool() { [[ -f "$EXECUTED_SCRIPT" ]]; }\ninstall_chezmoi\n'
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            self.arguments.read_text().splitlines(),
            ["-b", str(Path.home() / ".local/bin")],
        )
        downloaded = self.assert_download_removed()
        self.assertEqual(self.executed_script.read_text().strip(), str(downloaded))

    def test_installed_chezmoi_is_not_downloaded_again(self):
        result = self.run_shell('\nhas_tool() { return 0; }\ninstall_chezmoi\n')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse(self.download_path.exists())
        self.assertFalse(self.executed_script.exists())

    def test_bash_installer_runs_without_arguments(self):
        result = self.run_shell('\nrun_installer https://example.invalid/test bash\n')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.arguments.read_text(), "")
        downloaded = self.assert_download_removed()
        self.assertEqual(self.executed_script.read_text().strip(), str(downloaded))

    def test_script_arguments_preserve_order_spaces_and_empty_values(self):
        result = self.run_shell(
            '\nrun_installer https://example.invalid/test sh "first value" --flag ""\n'
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(
            self.arguments.read_text().splitlines(), ["first value", "--flag", ""]
        )
        self.assert_download_removed()

    def test_installer_failure_is_returned_and_download_is_removed(self):
        result = self.run_shell(
            '\nrun_installer https://example.invalid/test bash\n',
            INSTALLER_EXIT="23",
        )
        self.assertEqual(result.returncode, 23, result.stderr)
        self.assertTrue(self.executed_script.exists())
        self.assert_download_removed()

    def test_failed_download_is_removed_without_running_installer(self):
        result = self.run_shell(
            '\nrun_installer https://example.invalid/test bash\n',
            DOWNLOAD_EXIT="22",
        )
        self.assertEqual(result.returncode, 1, result.stderr)
        self.assertFalse(self.executed_script.exists())
        self.assert_download_removed()


if __name__ == "__main__":
    unittest.main()
