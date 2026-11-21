#!/usr/bin/env python3
"""Neovimのlockfileをローカル保存する。復元・更新・外部通信は行わない。"""

import argparse
from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import shutil
import stat
import subprocess
import sys
import uuid


ID_PATTERN = re.compile(r"[0-9]{8}T[0-9]{6}Z-[0-9a-f]{8}\Z")
COMMIT_PATTERN = re.compile(r"(?:[0-9a-f]{40}|[0-9a-f]{64})\Z")
LIMIT = 8 * 1024 * 1024
DIRECTORY_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
# Termuxでは親ディレクトリの通過が許可されても読み取りは拒否される。
WALK_FLAGS = getattr(os, "O_PATH", os.O_RDONLY) | os.O_DIRECTORY | os.O_NOFOLLOW


class SnapshotError(Exception):
    """利用者に内容を表示できる、秘密情報を含まないエラー。"""


def require(condition, message):
    if not condition:
        raise SnapshotError(message)


def absolute(value):
    path = Path(value)
    require(path.is_absolute() and ".." not in path.parts, "絶対パスを指定してください。")
    return path


def xdg(name, fallback):
    return absolute(os.environ.get(name) or fallback)


def paths():
    home = absolute(os.environ["HOME"])
    app = os.environ.get("NVIM_APPNAME") or "nvim"
    require(bool(re.fullmatch(r"[A-Za-z0-9_-][A-Za-z0-9_.-]*", app)), "アプリ名が不正です。")
    state = xdg("XDG_STATE_HOME", home / ".local/state")
    config = xdg("XDG_CONFIG_HOME", home / ".config")
    data = xdg("XDG_DATA_HOME", home / ".local/share")
    return app, state, state / "dotfiles/neovim-snapshots" / app, config / app / "lazy-lock.json", data / app / "lazy/lazy.nvim"


def private(info):
    require(info.st_uid == os.getuid() and not stat.S_IMODE(info.st_mode) & 0o077,
            "保存領域の所有者または権限を確認してください。ディレクトリは0700、ファイルは0600が必要です。")


@contextmanager
def storage(root, state, create=False):
    # 各階層をdir_fdとO_NOFOLLOWで開き、検証後のリンク差し替えを避ける。
    fd = os.open("/", WALK_FLAGS)
    try:
        for index, part in enumerate(root.parts[1:], 1):
            try:
                child = os.open(part, WALK_FLAGS, dir_fd=fd)
            except FileNotFoundError:
                if not create:
                    raise
                try:
                    os.mkdir(part, mode=0o700, dir_fd=fd)
                except FileExistsError:
                    pass
                child = os.open(part, WALK_FLAGS, dir_fd=fd)
            os.close(fd)
            fd = child
            info = os.fstat(fd)
            if index >= len(state.parts) + 1:
                private(info)
            elif index >= len(state.parts) - 1:
                # XDGとdotfilesの共用親は公開可能だが、他者の書き込みは拒否する。
                require(info.st_uid == os.getuid() and not stat.S_IMODE(info.st_mode) & 0o022,
                        "保存先の親ディレクトリの所有者・書き込み権限を確認してください。")
        directory = os.open(".", DIRECTORY_FLAGS, dir_fd=fd)
        try:
            yield directory
        finally:
            os.close(directory)
    finally:
        os.close(fd)


def fingerprint(info):
    return info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns


def read_regular(name, directory=None, restricted=False):
    fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=directory)
    try:
        before = os.fstat(fd)
        require(stat.S_ISREG(before.st_mode), "通常ファイルが必要です。")
        if restricted:
            private(before)
        require(before.st_size <= LIMIT, "ファイルがサイズ上限を超えています。")
        with os.fdopen(os.dup(fd), "rb") as stream:
            content = stream.read(LIMIT + 1)
        after = os.fstat(fd)
        current = os.stat(name, dir_fd=directory, follow_symlinks=False)
        require(len(content) <= LIMIT and fingerprint(before) == fingerprint(after) == fingerprint(current),
                "読み取り中にファイルが変わりました。Neovimを終了して再試行してください。")
        return content
    finally:
        os.close(fd)


def unique_object(pairs):
    result = {}
    for key, value in pairs:
        require(key not in result, "JSONに重複キーがあります。")
        result[key] = value
    return result


def decode(content):
    try:
        return json.loads(content, object_pairs_hook=unique_object,
                          parse_constant=lambda _: invalid_json())
    except (ValueError, UnicodeError, RecursionError):
        raise SnapshotError("JSON形式が不正です。") from None


def invalid_json():
    raise SnapshotError("JSONの数値が不正です。")


def lock_data(content):
    value = decode(content)
    require(isinstance(value, dict), "lockfileにはJSONオブジェクトが必要です。")
    for name, entry in value.items():
        require(bool(name) and isinstance(entry, dict)
                and isinstance(entry.get("branch"), str) and bool(entry["branch"])
                and isinstance(entry.get("commit"), str) and bool(COMMIT_PATTERN.fullmatch(entry["commit"])),
                "lockfileのbranchまたはcommitが不正です。")
    return value


def run(command):
    # 認証情報・Gitの環境変数を継承せず、stderrに含まれる私的情報も表示しない。
    environment = {"PATH": os.environ.get("PATH", os.defpath), "LC_ALL": "C",
                   "GIT_CONFIG_NOSYSTEM": "1", "GIT_CONFIG_GLOBAL": os.devnull,
                   "GIT_OPTIONAL_LOCKS": "0", "GIT_TERMINAL_PROMPT": "0"}
    try:
        result = subprocess.run(command, env=environment, capture_output=True, timeout=10, check=True)
        return result.stdout.decode("utf-8", errors="replace")
    except (OSError, subprocess.SubprocessError):
        raise SnapshotError("ローカルの版情報を取得できません。") from None


def git(source, *arguments):
    return run(["git", "--no-optional-locks", "-c", "core.fsmonitor=false",
                "-c", "core.hooksPath=" + os.devnull, "-C", str(source), *arguments])


def revision(source):
    require(Path(git(source, "rev-parse", "--show-toplevel").strip()).resolve() == source.resolve(),
            "Gitリポジトリのルートを指定してください。")
    commit = git(source, "rev-parse", "--verify", "HEAD").strip()
    require(bool(COMMIT_PATTERN.fullmatch(commit)), "設定コミットを確認できません。")
    return commit


def source_info(source):
    commit = revision(source)
    records = iter(git(source, "status", "--porcelain=v1", "-z", "--untracked-files=normal").split("\0"))
    tracked = untracked = False
    for record in records:
        if not record:
            continue
        if record.startswith("??"):
            untracked = True
        else:
            tracked = True
            if "R" in record[:2] or "C" in record[:2]:
                next(records, None)
    return {"commit": commit, "tracked_changes": tracked, "untracked_files": untracked}


def versions(lazy_dir):
    warnings = []
    executable = shutil.which("nvim")
    neovim = {"path": executable, "version": None}
    try:
        require(executable is not None, "Neovimがありません。")
        lines = run([executable, "--version"]).splitlines()
        require(bool(lines), "版情報が空です。")
        neovim["version"] = lines[0]
    except SnapshotError:
        warnings.append("Neovimの版情報を取得できません。")
    lazy = {"path": str(lazy_dir), "commit": None, "reason": None}
    try:
        lazy["commit"] = revision(lazy_dir)
    except SnapshotError:
        lazy["reason"] = "lazy.nvimのコミットを取得できません。"
        warnings.append(lazy["reason"])
    return neovim, lazy, warnings


def write_file(directory, name, content):
    fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600, dir_fd=directory)
    with os.fdopen(fd, "wb") as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())


def save(args, app, state, root, lockfile, lazy_dir):
    require(len(args.note or "") <= 4096 and len(args.label or "") <= 256, "メモまたはラベルが長すぎます。")
    source = absolute(args.source).resolve()
    require(not root.resolve().is_relative_to(source), "dotfilesソース内には保存できません。")
    content = read_regular(lockfile)
    entries = lock_data(content)
    dotfiles = source_info(source)
    neovim, lazy, warnings = versions(lazy_dir)
    if dotfiles["tracked_changes"] or dotfiles["untracked_files"]:
        warnings.append("未コミット変更があります。設定コミットだけでは再現できません。")
    now = datetime.now(timezone.utc)
    metadata = {"schema_version": 1, "created_at": now.isoformat(), "label": args.label, "note": args.note,
                "app_name": app, "platform": platform.system(), "architecture": platform.machine(),
                "lockfile": {"path": str(lockfile), "sha256": hashlib.sha256(content).hexdigest(),
                             "bytes": len(content), "entries": len(entries)},
                "dotfiles": dotfiles, "neovim": neovim, "lazy_nvim": lazy,
                "config_application": "unverified", "warnings": warnings}
    with storage(root, state, create=True) as parent:
        # 同じ保存領域の書き手を直列化し、ID衝突時も既存ディレクトリを守る。
        fcntl.flock(parent, fcntl.LOCK_EX)
        for _ in range(10):
            identifier = now.strftime("%Y%m%dT%H%M%SZ-") + uuid.uuid4().hex[:8]
            if not exists_at(parent, identifier):
                break
        else:
            raise SnapshotError("保存IDを確保できません。再試行してください。")
        staging = ".pending-" + uuid.uuid4().hex
        os.mkdir(staging, 0o700, dir_fd=parent)
        try:
            child = os.open(staging, DIRECTORY_FLAGS, dir_fd=parent)
        except OSError:
            os.rmdir(staging, dir_fd=parent)
            raise
        published = False
        try:
            metadata["id"] = identifier
            write_file(child, "lazy-lock.json", content)
            write_file(child, "metadata.json", (json.dumps(metadata, ensure_ascii=True, indent=2) + "\n").encode())
            os.fsync(child)
            os.rename(staging, identifier, src_dir_fd=parent, dst_dir_fd=parent)
            published = True
            os.fsync(parent)
        finally:
            # 公開済みディレクトリは触らず、自分の一時領域だけを削除する。
            try:
                if not published and exists_at(parent, staging):
                    for name in ("lazy-lock.json", "metadata.json"):
                        try:
                            os.unlink(name, dir_fd=child)
                        except FileNotFoundError:
                            pass
                    os.rmdir(staging, dir_fd=parent)
            finally:
                os.close(child)
    return {"id": identifier, "path": str(root / identifier), "warnings": warnings}


def exists_at(parent, name):
    try:
        os.stat(name, dir_fd=parent, follow_symlinks=False)
        return True
    except FileNotFoundError:
        return False


def load(parent, identifier, app):
    require(bool(ID_PATTERN.fullmatch(identifier)), "保存IDが不正です。")
    child = os.open(identifier, DIRECTORY_FLAGS, dir_fd=parent)
    try:
        private(os.fstat(child))
        metadata = decode(read_regular("metadata.json", child, restricted=True))
        require(isinstance(metadata, dict) and type(metadata.get("schema_version")) is int
                and metadata["schema_version"] == 1, "未対応の記録形式です。")
        require(metadata.get("id") == identifier and metadata.get("app_name") == app
                and metadata.get("config_application") == "unverified", "保存記録の識別情報が不正です。")
        require(isinstance(metadata.get("created_at"), str)
                and all(isinstance(metadata.get(key), dict) for key in ("lockfile", "dotfiles", "neovim", "lazy_nvim"))
                and isinstance(metadata.get("warnings"), list), "保存記録の項目が不足しています。")
        info = metadata["lockfile"]
        content = read_regular("lazy-lock.json", child, restricted=True)
        entries = lock_data(content)
        require(type(info.get("bytes")) is int and type(info.get("entries")) is int
                and info["bytes"] == len(content) and info["entries"] == len(entries)
                and info.get("sha256") == hashlib.sha256(content).hexdigest(), "保存データの整合性を確認できません。")
        require(isinstance(metadata["dotfiles"].get("commit"), str)
                and bool(COMMIT_PATTERN.fullmatch(metadata["dotfiles"]["commit"]))
                and all(type(metadata["dotfiles"].get(key)) is bool for key in ("tracked_changes", "untracked_files")),
                "設定コミットの記録が不正です。")
        require(all(metadata.get(key) is None or isinstance(metadata[key], str) for key in ("label", "note"))
                and all(isinstance(metadata.get(key), str) for key in ("platform", "architecture"))
                and all(isinstance(warning, str) for warning in metadata["warnings"])
                and isinstance(info.get("path"), str), "保存記録の項目形式が不正です。")
        require(all(metadata["neovim"].get(key) is None or isinstance(metadata["neovim"][key], str)
                    for key in ("path", "version"))
                and isinstance(metadata["lazy_nvim"].get("path"), str)
                and (metadata["lazy_nvim"].get("commit") is None
                     or isinstance(metadata["lazy_nvim"]["commit"], str)
                     and bool(COMMIT_PATTERN.fullmatch(metadata["lazy_nvim"]["commit"])))
                and (metadata["lazy_nvim"].get("reason") is None or isinstance(metadata["lazy_nvim"]["reason"], str)),
                "版情報の形式が不正です。")
        require(datetime.fromisoformat(metadata["created_at"]).utcoffset() is not None, "保存日時が不正です。")
        return metadata
    finally:
        os.close(child)


def execute(args):
    app, state, root, default_lock, default_lazy = paths()
    lockfile = absolute(args.lockfile) if args.lockfile else default_lock
    lazy_dir = absolute(args.lazy_dir) if args.lazy_dir else default_lazy
    if args.action == "save":
        return save(args, app, state, root, lockfile, lazy_dir)
    try:
        with storage(root, state) as parent:
            if args.action == "list":
                result = []
                for identifier in sorted(os.listdir(parent)):
                    if ID_PATTERN.fullmatch(identifier):
                        try:
                            item = load(parent, identifier, app)
                        except FileNotFoundError:
                            raise SnapshotError("保存データのファイルが不足しています。") from None
                        summary = {key: item.get(key) for key in ("id", "created_at", "label", "note")}
                        summary["commit"] = item["dotfiles"]["commit"]
                        result.append(summary)
                return result
            metadata = load(parent, args.id, app)
    except FileNotFoundError:
        if args.action == "list":
            return []
        raise SnapshotError("指定した保存データがありません。") from None
    if args.action == "show":
        return metadata
    current = source_info(absolute(args.source))
    neovim, lazy, warnings = versions(lazy_dir)
    return {"saved": metadata, "current": {"dotfiles": current, "neovim": neovim, "lazy_nvim": lazy},
            "same_config_commit": current["commit"] == metadata["dotfiles"]["commit"], "warnings": warnings,
            "steps": ["Neovimを終了し、現在の設定変更とlockfileを退避してください。",
                      "保存したコミットの設定を確認し、レビューできる差分としてソースへ戻してください。",
                      "設定の適用とlockfileの復元、必要なプラグイン取得は別操作で行ってください。",
                      "LSP・補完・整形・DAP等を確認してください。この操作はファイルを変更していません。"]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="action", required=True)
    for action in ("save", "list", "show", "prepare"):
        command = commands.add_parser(action)
        if action in ("save", "prepare"):
            command.add_argument("--source", required=True)
        if action in ("show", "prepare"):
            command.add_argument("id")
        if action == "save":
            command.add_argument("--label")
            command.add_argument("--note")
        command.add_argument("--lockfile")
        command.add_argument("--lazy-dir")
    args = parser.parse_args(argv)
    try:
        require(sys.version_info >= (3, 11), "Python 3.11以上が必要です。")
        print(json.dumps(execute(args), ensure_ascii=True, indent=2))
        return 0
    except SnapshotError as error:
        print(str(error), file=sys.stderr)
    except (OSError, KeyError, ValueError, RecursionError):
        print("ファイル・保存先・記録形式を確認してください。処理に失敗しました。", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
