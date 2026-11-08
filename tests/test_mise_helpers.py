"""実際の導入をせず、補助ツールの一覧判定と失敗時の停止を検証する。"""

from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest


SOURCE = (
    Path(__file__).resolve().parents[1]
    / "home/.chezmoiscripts/run_after_install-mise.sh"
)
BASH = shutil.which("bash")


class MiseHelperTests(unittest.TestCase):
    def setUp(self):
        workspace = tempfile.TemporaryDirectory(prefix="mise helpers ")
        self.addCleanup(workspace.cleanup)
        self.base = Path(workspace.name)
        self.bin = self.base / "bin"
        self.bin.mkdir()
        self.trace = self.base / "trace"
        self.list_file = self.base / "list"
        self.trace.write_text("")
        self.list_file.write_text("")
        self.state = self.base / "state"
        self.state.mkdir()
        config = self.base / ".config/mise/config.toml"
        config.parent.mkdir(parents=True)
        config.write_text('[tools]\nnode = "24"\n')
        for name, operation in (("rustup", "$2"), ("luarocks", "$2"), ("nimble", "$1")):
            command = self.bin / name
            command.write_text(
                f"#!{BASH}\n"
                f'printf "%s\\n" "{name} $*" >> "$TRACE"\n'
                f'if [[ "{operation}" == list ]]; then\n'
                '  while IFS= read -r line; do printf "%s\\n" "$line"; done < "$LIST_FILE"\n'
                '  for package in rust-analyzer luacheck vuseted nimlsp; do\n'
                '    [[ ! -f "$STATE_DIR/$package" ]] || printf "%s\\n" "$package"\n'
                '  done\n'
                '  exit "${LIST_EXIT:-0}"\n'
                'fi\n'
                '[[ "${INSTALL_EXIT:-0}" == 0 ]] && : > "$STATE_DIR/${@: -1}"\n'
                'exit "${INSTALL_EXIT:-0}"\n'
            )
            command.chmod(0o755)
        mise = self.bin / "mise"
        mise.write_text(f"#!{BASH}\n" + r'''
printf 'mise %s\n' "$*" >> "$TRACE"
[[ "$1" != --cd ]] || shift 2
request="${TOOL_REQUEST:-node24}"
case "$1" in
  ls)
    [[ "${QUERY_EXIT:-0}" == 0 ]] || exit "$QUERY_EXIT"
    if [[ ! -f "$STATE_DIR/mise" || "$(<"$STATE_DIR/mise")" != "$request" ]]; then
      printf '%s\n' "$request"
    fi
    ;;
  install)
    [[ "${MISE_INSTALL_EXIT:-0}" == 0 ]] || exit "$MISE_INSTALL_EXIT"
    [[ "${NO_MARKER:-0}" == 1 ]] || printf '%s' "$request" > "$STATE_DIR/mise"
    ;;
  env)
    [[ "$2" == --paths ]] || exit 99
    [[ "${PATH_EXIT:-0}" == 0 ]] || exit "$PATH_EXIT"
    printf '%s\n' "$MOCK_BIN"
    ;;
  *) exit 99 ;;
esac
''')
        mise.chmod(0o755)
        self.mise_fixture = self.base / "mise-fixture"
        self.mise_fixture.write_text(mise.read_text())
        for utility in ("bash", "mkdir", "chmod"):
            (self.bin / utility).symlink_to(shutil.which(utility))
        installer = self.base / "installer"
        installer.write_text(
            '[[ "${CREATE_MISE:-1}" == 1 ]] || exit 0\n'
            'while IFS= read -r line; do printf "%s\\n" "$line"; done '
            '< "$MISE_FIXTURE" > "$MISE_INSTALL_PATH"\n'
            'chmod +x "$MISE_INSTALL_PATH"\n'
        )
        curl = self.bin / "curl"
        curl.write_text(
            f"#!{BASH}\n"
            'if [[ "${DOWNLOAD_EXIT:-0}" != 0 ]]; then\n'
            '  printf ": > \\"$BOOTSTRAP_MARKER\\"\\n"\n'
            '  exit "$DOWNLOAD_EXIT"\n'
            'fi\n'
            'while IFS= read -r line; do printf "%s\\n" "$line"; done < "$INSTALLER_FIXTURE"\n'
        )
        curl.chmod(0o755)
        # ホストのツールや認証情報を使わず、ダミーだけを探索する。
        self.environment = {
            "HOME": str(self.base),
            "PATH": str(self.bin),
            "TRACE": str(self.trace),
            "LIST_FILE": str(self.list_file),
            "STATE_DIR": str(self.state),
            "MOCK_BIN": str(self.bin),
            "MISE_FIXTURE": str(self.mise_fixture),
            "INSTALLER_FIXTURE": str(installer),
            "BOOTSTRAP_MARKER": str(self.base / "bootstrap-marker"),
        }

    def call_helper(self, helper, package, *arguments, **environment):
        self.trace.write_text("")
        return subprocess.run(
            [
                BASH, "-c", 'source "$1"; confirm_install() { return 0; }; shift; "$@"',
                "--", str(SOURCE), helper, package, *arguments,
            ],
            input="",
            capture_output=True,
            text=True,
            env={**self.environment, **environment},
            timeout=10,
        )

    def assert_no_install(self):
        trace = self.trace.read_text()
        self.assertNotIn("component add", trace)
        self.assertNotIn(" install ", trace)
        self.assertNotIn(" install\n", trace)

    def test_rust_component_exact_name_and_target_suffix_are_installed(self):
        for name in ("rust-analyzer", "rust-analyzer-aarch64-unknown-linux-gnu"):
            with self.subTest(name=name):
                self.list_file.write_text(name + "\n")
                result = self.call_helper("install_rustup_component", "rust-analyzer")
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assert_no_install()

    def test_missing_rust_component_is_installed(self):
        self.list_file.write_text("rustfmt-aarch64-unknown-linux-gnu\n")
        result = self.call_helper("install_rustup_component", "rust-analyzer")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("rustup component add rust-analyzer\n", self.trace.read_text())

    def test_luarocks_package_is_matched_by_first_column(self):
        self.list_file.write_text("luacheck\t1.2.0-1\tinstalled\t/dummy/tree\n")
        result = self.call_helper("install_luarock", "luacheck")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_no_install()

    def test_luarocks_similar_package_name_is_not_a_match(self):
        self.list_file.write_text("luacheck-extra\t1.0-1\tinstalled\n")
        result = self.call_helper("install_luarock", "luacheck")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("install luacheck\n", self.trace.read_text())

    def test_empty_list_installs_requested_tool(self):
        for helper, package in (
            ("install_rustup_component", "rust-analyzer"),
            ("install_luarock", "luacheck"),
        ):
            with self.subTest(helper=helper):
                result = self.call_helper(helper, package)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(package + "\n", self.trace.read_text())

    def test_failed_list_does_not_install_even_with_partial_output(self):
        for helper, package in (
            ("install_rustup_component", "rust-analyzer"),
            ("install_luarock", "luacheck"),
        ):
            with self.subTest(helper=helper):
                self.list_file.write_text(package + "\n")
                result = self.call_helper(helper, package, LIST_EXIT="23")
                self.assertNotEqual(result.returncode, 0)
                self.assert_no_install()

    def test_missing_tool_is_reported_without_installation(self):
        for helper, command, package in (
            ("install_rustup_component", "rustup", "rust-analyzer"),
            ("install_luarock", "luarocks", "luacheck"),
        ):
            with self.subTest(helper=helper):
                (self.bin / command).unlink()
                result = self.call_helper(helper, package)
                self.assertNotEqual(result.returncode, 0)
                self.assert_no_install()

    def test_installation_failure_is_returned(self):
        for helper, package in (
            ("install_rustup_component", "rust-analyzer"),
            ("install_luarock", "luacheck"),
        ):
            with self.subTest(helper=helper):
                result = self.call_helper(helper, package, INSTALL_EXIT="17")
                self.assertEqual(result.returncode, 17, result.stderr)

    def test_large_list_does_not_reinstall_first_matching_tool(self):
        for helper, package in (
            ("install_rustup_component", "rust-analyzer"),
            ("install_luarock", "luacheck"),
        ):
            with self.subTest(helper=helper):
                self.list_file.write_text(
                    package + "\t1.0\n"
                    + "".join(f"other-{number}\t1.0\n" for number in range(10000))
                )
                result = self.call_helper(helper, package)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assert_no_install()

    def test_luarocks_uses_requested_lua_version(self):
        result = self.call_helper("install_luarock", "luacheck", "5.4")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("--lua-version=5.4 list --porcelain\n", self.trace.read_text())
        self.assertIn("--lua-version=5.4 install luacheck\n", self.trace.read_text())

    def test_direct_execution_can_decline_bulk_installation(self):
        result = subprocess.run(
            [BASH, str(SOURCE)],
            input="n\n",
            capture_output=True,
            text=True,
            env=self.environment,
            timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_no_install()

    def test_failed_component_query_stops_later_bulk_installation(self):
        result = subprocess.run(
            [BASH, str(SOURCE)],
            input="y\n",
            capture_output=True,
            text=True,
            env={**self.environment, "LIST_EXIT": "23"},
            timeout=10,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("rustup component list --installed\n", self.trace.read_text())
        self.assertNotIn("luarocks", self.trace.read_text())

    def run_main(self, answers="y\n", **environment):
        return subprocess.run(
            [BASH, str(SOURCE)], input=answers, capture_output=True, text=True,
            env={**self.environment, **environment}, timeout=10,
        )

    def test_reapply_installed_configuration_needs_no_input(self):
        first = self.run_main()
        self.assertEqual(first.returncode, 0, first.stderr)
        self.trace.write_text("")
        second = self.run_main("")
        self.assertEqual(second.returncode, 0, second.stderr)
        self.assert_no_install()
        self.assertIn(" env --paths\n", self.trace.read_text())

    def test_decline_and_eof_allow_retry(self):
        declined = self.run_main("n\n")
        self.assertEqual(declined.returncode, 0, declined.stderr)
        self.assert_no_install()
        eof = self.run_main("")
        self.assertNotEqual(eof.returncode, 0)
        accepted = self.run_main()
        self.assertEqual(accepted.returncode, 0, accepted.stderr)

    def test_changed_request_is_rechecked(self):
        self.assertEqual(self.run_main().returncode, 0)
        config = self.base / ".config/mise/config.toml"
        config.write_text('[tools]\nnode = "26"\n')
        before = config.read_bytes()
        self.trace.write_text("")
        result = self.run_main(TOOL_REQUEST="node26")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(" install\n", self.trace.read_text())
        self.assertNotIn(" use ", self.trace.read_text())
        self.assertEqual(config.read_bytes(), before)

    def test_mise_query_failure_does_not_install(self):
        result = self.run_main(QUERY_EXIT="2")
        self.assertEqual(result.returncode, 2)
        self.assert_no_install()

    def test_mise_install_failure_allows_retry(self):
        failed = self.run_main(MISE_INSTALL_EXIT="17")
        self.assertEqual(failed.returncode, 17)
        self.assertNotIn("rustup", self.trace.read_text())
        accepted = self.run_main()
        self.assertEqual(accepted.returncode, 0, accepted.stderr)

    def test_remaining_missing_tools_are_not_success(self):
        result = self.run_main(NO_MARKER="1")
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("rustup", self.trace.read_text())

    def test_path_query_failure_stops_supplementary_tools(self):
        result = self.run_main(PATH_EXIT="23")
        self.assertEqual(result.returncode, 23)
        self.assertNotIn("rustup", self.trace.read_text())

    def test_exit_twenty_from_installer_is_not_a_decline(self):
        result = self.run_main(MISE_INSTALL_EXIT="20")
        self.assertEqual(result.returncode, 20)

    def test_missing_managed_config_stops_before_any_installation(self):
        (self.base / ".config/mise/config.toml").unlink()
        result = self.run_main()
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.trace.read_text(), "")

    def test_missing_mise_can_be_declined_or_retried(self):
        (self.bin / "mise").unlink()
        self.assertEqual(self.run_main("n\n").returncode, 0)
        self.assertNotEqual(self.run_main("").returncode, 0)
        accepted = self.run_main()
        self.assertEqual(accepted.returncode, 0, accepted.stderr)
        self.assertTrue((self.base / ".local/bin/mise").exists())

    def test_failed_bootstrap_download_does_not_execute_partial_script(self):
        (self.bin / "mise").unlink()
        result = self.run_main(DOWNLOAD_EXIT="22")
        self.assertEqual(result.returncode, 22, result.stderr)
        self.assertFalse(Path(self.environment["BOOTSTRAP_MARKER"]).exists())

    def test_successful_installer_without_mise_is_failure(self):
        (self.bin / "mise").unlink()
        result = self.run_main(CREATE_MISE="0")
        self.assertNotEqual(result.returncode, 0)
        self.assert_no_install()

    def test_nimble_query_error_does_not_install_nimlsp(self):
        result = self.call_helper("install_nimlsp", "nimlsp", LIST_EXIT="23")
        self.assertEqual(result.returncode, 23)
        self.assert_no_install()


if __name__ == "__main__":
    unittest.main()
