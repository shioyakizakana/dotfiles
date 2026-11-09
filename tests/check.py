"""実環境への適用を呼ばない、ローカルとCI共通の検証入口。"""

import argparse
import ast
from pathlib import Path
import shutil
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
UNIT_TOOLS = ("bash", "zsh", "chezmoi", "lua", "make", "mkdir", "cat", "chmod", "dirname", "git", "lefthook")
OPTIONAL_SKIPS = {
    "test_yazi_config.YaziConfigTests.test_yazi_loads_keymap_in_isolated_terminal",
}
BASH_FILES = (
    "bootstrap/bootstrap-tools.sh",
    "bootstrap/setup-proton-pass.sh",
    "home/.chezmoiscripts/run_after_install-apt.sh",
    "home/.chezmoiscripts/run_after_install-brew.sh",
    "home/.chezmoiscripts/run_after_install-mise.sh",
    "home/dot_config/shell/env.sh",
    "home/dot_config/shell/aliases.sh",
    "home/dot_local/bin/executable_update_apps",
    "home/dot_local/bin/executable_update-agent-skills",
    "home/dot_local/bin/executable_textlint-ja",
)


def require_tools(names):
    missing = [name for name in names if shutil.which(name) is None]
    if missing:
        raise RuntimeError("必須の検証ツールがありません: " + ", ".join(missing))


def unit_result_status(result):
    unexpected = []
    for test, reason in result.skipped:
        if test.id() in OPTIONAL_SKIPS:
            print(f"[任意検証skip] {test.id()}: {reason}", flush=True)
        else:
            unexpected.append(test.id())
            print(f"[必須検証skip] {test.id()}: {reason}", file=sys.stderr, flush=True)
    print(f"unittest: {result.testsRun}件、skip {len(result.skipped)}件", flush=True)
    if result.testsRun <= len(result.skipped):
        print("実行済みのテストがありません", file=sys.stderr)
    return int(not result.wasSuccessful() or bool(unexpected) or result.testsRun <= len(result.skipped))


def run_unit():
    require_tools(UNIT_TOOLS)
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_*.py")
    return unit_result_status(unittest.TextTestRunner(verbosity=2).run(suite))


def run_command(arguments):
    print("+ " + " ".join(str(value) for value in arguments), flush=True)
    subprocess.run(arguments, cwd=ROOT, check=True)


def run_smoke():
    require_tools(("bats", "bash", "cat"))
    run_command(["bats", "tests/smoke.bats"])
    return 0


def run_lint():
    import tomllib

    require_tools(("bash", "zsh", "shellcheck", "shfmt", "git", "lefthook"))
    run_command(["lefthook", "validate"])
    for name in (*BASH_FILES, "home/dot_bashrc", "home/dot_bash_aliases"):
        run_command(["bash", "-n", name])
    for path in sorted((ROOT / "home/dot_zsh").rglob("*.zsh")):
        run_command(["zsh", "-dfn", str(path.relative_to(ROOT))])
    for name in BASH_FILES:
        arguments = ["shellcheck"]
        if name == "bootstrap/setup-proton-pass.sh":
            # ログ関数が受け取る固定の書式をprintfへ渡す仕様のため、このファイルだけ除外する。
            arguments.append("--exclude=SC2059")
        run_command([*arguments, name])
        if name != "home/dot_local/bin/executable_update-agent-skills":
            # 既存の整形差分は別途扱い、実行される処理は変更しない。
            run_command(["shfmt", "-i", "2", "-d", name])
    for path in sorted((ROOT / "tests").glob("*.py")):
        ast.parse(path.read_text(), filename=str(path))
    for path in [ROOT / "home/dot_config/mise/config.toml", *sorted((ROOT / "home/dot_config/yazi").glob("*.toml"))]:
        tomllib.loads(path.read_text())
    # Go templateを静的検査へ直接渡さない。ダミー展開は既存unittestが担当する。
    run_command(["git", "diff", "--check"])
    print("Python構文・対象TOMLの解析: 成功", flush=True)
    return 0


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("unit", "smoke", "lint"))
    arguments = parser.parse_args(argv)
    if sys.version_info < (3, 11):
        print("Python 3.11以上が必要です", file=sys.stderr)
        return 1
    try:
        return {"unit": run_unit, "smoke": run_smoke, "lint": run_lint}[arguments.mode]()
    except (RuntimeError, OSError, subprocess.CalledProcessError, ValueError, SyntaxError) as error:
        print(f"検証失敗: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
