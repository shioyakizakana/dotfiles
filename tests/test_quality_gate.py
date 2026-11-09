"""依存不足・予期しないskip・検証コマンド失敗を成功扱いしない。"""

import contextlib
import io
from pathlib import Path
import shutil
import subprocess
import sys
import unittest
from unittest import mock

import check


class QualityGateTests(unittest.TestCase):
    def case(self, skipped=False):
        class Fixture(unittest.TestCase):
            def runTest(self):
                if skipped:
                    self.skipTest("dummy dependency")

        return Fixture()

    def result(self, cases):
        return unittest.TextTestRunner(stream=io.StringIO()).run(unittest.TestSuite(cases))

    def status(self, result):
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            return check.unit_result_status(result)

    def test_missing_required_tool_stops_before_discovery(self):
        with mock.patch.object(check.shutil, "which", side_effect=lambda name: None if name == "chezmoi" else "/dummy/tool"), \
             mock.patch.object(check.unittest.defaultTestLoader, "discover") as discover:
            with self.assertRaisesRegex(RuntimeError, "chezmoi"):
                check.run_unit()
            discover.assert_not_called()

    def test_successful_tests_pass(self):
        self.assertEqual(self.status(self.result([self.case()])), 0)

    def test_unexpected_skip_fails(self):
        self.assertEqual(self.status(self.result([self.case(skipped=True)])), 1)

    def test_explicit_optional_skip_passes_and_is_reported(self):
        case = self.case(skipped=True)
        with mock.patch.object(check, "OPTIONAL_SKIPS", {case.id()}):
            output = io.StringIO()
            with contextlib.redirect_stdout(output):
                self.assertEqual(check.unit_result_status(self.result([self.case(), case])), 0)
            self.assertIn("[任意検証skip]", output.getvalue())
            self.assertIn("dummy dependency", output.getvalue())

    def test_no_discovered_tests_fails(self):
        self.assertEqual(self.status(self.result([])), 1)

    def test_only_optional_skipped_tests_is_not_a_successful_run(self):
        case = self.case(skipped=True)
        with mock.patch.object(check, "OPTIONAL_SKIPS", {case.id()}):
            self.assertEqual(self.status(self.result([case])), 1)

    def test_main_returns_failure_when_validator_fails(self):
        with mock.patch.object(check, "run_lint", side_effect=subprocess.CalledProcessError(7, ["shellcheck"])), \
             contextlib.redirect_stderr(io.StringIO()):
            self.assertEqual(check.main(["lint"]), 1)

    def test_failed_test_is_not_accepted_with_optional_skip(self):
        result = self.result([self.case(skipped=True)])
        result.addFailure(self.case(), (AssertionError, AssertionError("dummy failure"), None))
        with mock.patch.object(check, "OPTIONAL_SKIPS", {test.id() for test, _ in result.skipped}):
            self.assertEqual(self.status(result), 1)

    def test_validator_failure_reaches_caller(self):
        with mock.patch.object(check.subprocess, "run", side_effect=subprocess.CalledProcessError(7, ["bats"])), \
             contextlib.redirect_stdout(io.StringIO()):
            with self.assertRaises(subprocess.CalledProcessError):
                check.run_command(["bats", "tests/smoke.bats"])

    def test_lint_does_not_pass_unrendered_templates_to_shell_tools(self):
        calls = []
        with mock.patch.object(check, "require_tools"), \
             mock.patch.object(check, "run_command", side_effect=lambda args: calls.append(args)), \
             contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(check.run_lint(), 0)
        for arguments in calls:
            for argument in arguments[1:]:
                self.assertFalse(str(argument).endswith(".tmpl"), arguments)

    @unittest.skipUnless(shutil.which("make"), "makeが必要です")
    def test_make_verification_targets_only_dispatch_to_checker(self):
        result = subprocess.run(
            [shutil.which("make"), "--no-print-directory", "-n", "check", f"TEST_PYTHON={sys.executable}"],
            cwd=Path(__file__).resolve().parents[1], capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        lines = result.stdout.splitlines()
        self.assertEqual(len(lines), 3)
        for line, mode in zip(lines, ("lint", "unit", "smoke")):
            self.assertIn("tests/check.py", line)
            self.assertTrue(line.endswith(" " + mode), line)


if __name__ == "__main__":
    unittest.main()
