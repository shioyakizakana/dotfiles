"""規約の文字数・経路・リンク・上限の判定を隔離ファイルで検証する。"""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import check_instruction_budget as budget


SCRIPT = Path(budget.__file__).resolve()


class InstructionBudgetTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix="instruction budget ")
        self.addCleanup(directory.cleanup)
        self.base = Path(directory.name)
        self.root = self.base / "repository"
        self.root.mkdir()
        self.global_file = self.base / "global.md"
        self.global_file.write_text("共通\n")
        self.write("AGENTS.md", "規約\n")

    def write(self, name, text):
        path = self.root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(text.encode("utf-8"))
        return path

    def report(self):
        return budget.build_report(self.root, self.global_file)

    def cli(self, *args):
        return subprocess.run(
            [sys.executable, "-B", str(SCRIPT), "--root", str(self.root), *args],
            env={"HOME": str(self.base / "isolated-home")},
            capture_output=True, text=True, timeout=10,
        )

    def test_counts_unicode_spaces_and_original_newlines(self):
        path = self.write("AGENTS.md", "あ😀 \r\n")
        self.assertEqual(budget.characters(path), 5)
        self.assertEqual(self.report()["root_total"], 8)

    def test_file_boundary_is_inclusive(self):
        self.write("AGENTS.md", "あ" * 1000)
        self.assertEqual(self.report()["errors"], [])
        self.write("AGENTS.md", "あ" * 1001)
        self.assertIn("1ファイル上限: AGENTS.md 1001 > 1000", self.report()["errors"])

    def test_total_boundary_and_deep_scopes(self):
        self.global_file.write_text("g" * 1000)
        self.write("AGENTS.md", "a" * 1000)
        directory = Path()
        for index in range(6):
            directory /= f"level{index}"
            self.write(str(directory / "AGENTS.md"), "a" * 1000)
        self.assertEqual(self.report()["max_total"], 8000)
        self.assertEqual(self.report()["errors"], [])
        self.write(str(directory / "extra/AGENTS.md"), "a" * 1000)
        self.assertEqual(self.report()["max_total"], 9000)
        self.assertTrue(any("常時合計上限" in error for error in self.report()["errors"]))

    def test_sibling_scopes_are_not_added_together(self):
        self.global_file.write_text("g" * 1000)
        self.write("AGENTS.md", "a" * 1000)
        for sibling in ("one", "two"):
            directory = Path(sibling)
            for _ in range(4):
                self.write(str(directory / "AGENTS.md"), "a" * 1000)
                directory /= "child"
        report = self.report()
        self.assertEqual(report["max_total"], 6000)
        self.assertEqual(report["errors"], [])

    def test_overrides_and_empty_overrides_follow_discovery_order(self):
        self.write("AGENTS.md", "a" * 100)
        self.write("AGENTS.override.md", "override\n")
        self.assertEqual(self.report()["root_total"], 12)
        self.write("AGENTS.override.md", "")
        self.assertEqual(self.report()["root_total"], 103)

    def test_symlink_referent_is_counted_once(self):
        alias = self.base / "global-link.md"
        alias.symlink_to(self.global_file)
        local = self.root / "AGENTS.md"
        local.unlink()
        local.symlink_to(self.global_file)
        report = budget.build_report(self.root, alias)
        self.assertEqual(report["root_total"], 3)
        self.assertEqual(report["global"]["resolved"], str(self.global_file))

    def test_independent_copies_are_counted_even_with_equal_content(self):
        self.write("AGENTS.md", self.global_file.read_text())
        self.assertEqual(self.report()["root_total"], 6)

    def test_missing_global_and_broken_rule_link_fail(self):
        result = self.cli("--global-file", str(self.base / "missing.md"))
        self.assertEqual(result.returncode, 1)
        self.assertIn("規約検査失敗", result.stderr)
        self.write("folder/placeholder", "")
        (self.root / "folder/AGENTS.md").symlink_to(self.base / "missing.md")
        result = self.cli("--global-file", str(self.global_file))
        self.assertEqual(result.returncode, 1)

    def test_source_profile_and_baseline_do_not_require_deployed_global(self):
        self.write(str(budget.GLOBAL_SOURCE), "global source\n")
        baseline = self.write("before.json", json.dumps({"root_total": 10211}))
        result = self.cli("--global-source", "--baseline", str(baseline), "--json")
        self.assertEqual(result.returncode, 0, result.stderr)
        report = json.loads(result.stdout)
        self.assertEqual(report["profile"], "source")
        self.assertEqual(report["root_total"], 17)
        self.assertEqual(report["max_total"], 31)
        self.assertEqual(report["baseline"]["root_total"], 10211)

    def test_skills_have_file_limits_but_are_not_always_loaded(self):
        self.write(".agents/skills/fixture/SKILL.md", "s" * 1001)
        report = self.report()
        self.assertEqual(report["root_total"], 6)
        self.assertTrue(any("SKILL.md 1001" in error for error in report["errors"]))
        result = self.cli("--global-file", str(self.global_file), "--json")
        self.assertEqual(result.returncode, 1)

    def test_directory_symlinks_do_not_expand_discovery(self):
        (self.root / "loop").symlink_to(self.root, target_is_directory=True)
        self.assertEqual(len(self.report()["files"]), 1)

    def test_missing_root_rule_is_an_error(self):
        (self.root / "AGENTS.md").unlink()
        with self.assertRaisesRegex(ValueError, "ルート規約"):
            self.report()


if __name__ == "__main__":
    unittest.main()
