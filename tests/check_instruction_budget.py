"""規則の文字数と、フォルダごとの常時読込合計を検査する。"""

import argparse
import json
import os
from pathlib import Path
import sys


FILE_LIMIT = 1000
TOTAL_LIMIT = 8000
AGENT_NAMES = ("AGENTS.override.md", "AGENTS.md")
GLOBAL_SOURCE = Path("home/dot_config/ai-agents/AGENTS.md")
SKILL_ROOTS = (Path(".agents/skills"), Path("home/dot_agents/skills"))
EXCLUDED_DIRS = {".git", "node_modules", ".venv", "__pycache__"}


def characters(path):
    # 改行の変換をせず、空白・記号・改行もUnicodeの文字として数える。
    return len(path.read_bytes().decode("utf-8"))


def discover(root):
    paths = []
    def fail(error):
        raise error

    for directory, dirs, files in os.walk(root, followlinks=False, onerror=fail):
        dirs[:] = sorted(name for name in dirs if name not in EXCLUDED_DIRS)
        for name in sorted(files):
            path = Path(directory) / name
            relative = path.relative_to(root)
            if name in AGENT_NAMES or (
                name == "SKILL.md" and any(prefix in relative.parents for prefix in SKILL_ROOTS)
            ):
                paths.append(path)
    return sorted(paths)


def build_report(root, global_file, source_mode=False):
    root = root.resolve()
    paths = discover(root)
    sizes = {path: characters(path) for path in paths}
    if not any(sizes.get(root / name, 0) for name in AGENT_NAMES):
        raise ValueError(f"ルート規約がありません: {root}")
    global_size = characters(global_file)
    if global_size == 0:
        raise ValueError(f"グローバル規約が空です: {global_file}")
    rules = [path for path in paths if path.name in AGENT_NAMES]
    rows = [{"path": str(path.relative_to(root)), "resolved": str(path.resolve(strict=True)),
             "symlink": path.is_symlink(),
             "characters": sizes[path]} for path in paths]
    errors = [f"1ファイル上限: {row['path']} {row['characters']} > {FILE_LIMIT}"
              for row in rows if row["characters"] > FILE_LIMIT]
    if global_size > FILE_LIMIT:
        errors.append(f"1ファイル上限: GLOBAL {global_size} > {FILE_LIMIT}")
    contexts = []
    for directory in sorted({root, *(path.parent for path in rules)}):
        chain = [root]
        for part in directory.relative_to(root).parts:
            chain.append(chain[-1] / part)
        total = global_size
        loaded = ["GLOBAL"]
        # 配布元モードでは、GLOBALは将来の展開先コピーとして別に数える。
        seen = set() if source_mode else {global_file.resolve(strict=True)}
        for folder in chain:
            for name in AGENT_NAMES:
                path = folder / name
                if not sizes.get(path, 0):
                    continue
                resolved = path.resolve(strict=True)
                if resolved not in seen:
                    total += sizes[path]
                    loaded.append(str(path.relative_to(root)))
                    seen.add(resolved)
                break
        context = str(directory.relative_to(root))
        contexts.append({"directory": context, "characters": total, "loaded": loaded})
        if total > TOTAL_LIMIT:
            errors.append(f"常時合計上限: {context} {total} > {TOTAL_LIMIT}")
    return {"profile": "source" if source_mode else "live", "file_limit": FILE_LIMIT,
            "total_limit": TOTAL_LIMIT, "files": rows,
            "global": {"path": str(global_file), "resolved": str(global_file.resolve(strict=True)),
                       "characters": global_size},
            "contexts": contexts, "root_total": contexts[0]["characters"],
            "max_total": max(context["characters"] for context in contexts), "errors": errors}


def print_report(report, baseline):
    print("対象:", "配布元（適用予定）" if report["profile"] == "source" else "展開済み（現在）")
    print("文字数: UTF-8のUnicode文字数（空白・改行・Markdown記号を含む）")
    print("ファイル\t変更前\t現在")
    old = baseline.get("files", {})
    for row in report["files"]:
        print(f"{row['path']}\t{old.get(row['path'], 0)}\t{row['characters']}")
    current = report["global"]
    print(f"GLOBAL\t{baseline.get('global_characters', '-')}\t{current['characters']}")
    print(f"GLOBAL参照: {current['path']} -> {current['resolved']}（1回計上）")
    for row in report["files"]:
        if row["symlink"]:
            # 相対パスと実体を並べ、リンク先を別の入力として加算しない。
            print(f"規約参照: {row['path']} -> {row['resolved']}")
    print(f"ルート常時合計\t{baseline.get('root_total', '-')}\t{report['root_total']}")
    print(f"最大常時合計\t{baseline.get('max_total', '-')}\t{report['max_total']}")
    for context in report["contexts"]:
        print(f"経路 {context['directory']}: {context['characters']}字 / " + " + ".join(context["loaded"]))
    for error in report["errors"]:
        print("超過:", error)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, default=Path(__file__).resolve().parents[1])
    profiles = parser.add_mutually_exclusive_group()
    profiles.add_argument("--global-source", action="store_true", help="配布元を将来のGLOBALとして検証")
    profiles.add_argument("--global-file", type=Path, help="展開済みグローバル規約のパス")
    parser.add_argument("--baseline", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)
    root = args.root.resolve()
    global_file = root / GLOBAL_SOURCE if args.global_source else (
        args.global_file or Path.home() / ".codex/AGENTS.md")
    try:
        report = build_report(root, global_file, args.global_source)
        baseline_file = args.baseline or root / "docs/agents/instruction-budget-baseline.json"
        baseline = json.loads(baseline_file.read_text()) if baseline_file.exists() else {}
        if args.baseline and not baseline_file.is_file():
            raise ValueError(f"比較元がありません: {baseline_file}")
        report["baseline"] = baseline
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            print_report(report, baseline)
        return int(bool(report["errors"]))
    except (OSError, UnicodeError, ValueError, RuntimeError) as error:
        print(f"規約検査失敗: {error}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
