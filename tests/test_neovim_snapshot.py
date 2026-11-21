"""実HOME・秘密情報・実プラグインを使わず、保存と破損検出を確認する。"""

from concurrent.futures import ThreadPoolExecutor
from contextlib import redirect_stdout, redirect_stderr
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "home/dot_local/bin/executable_nvim-snapshot.py"
spec = importlib.util.spec_from_file_location("nvim_snapshot", SCRIPT)
snapshot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(snapshot)
COMMIT = "a" * 40
RAW = ('{\n "fixture.nvim": {"branch":"main", "commit":"' + COMMIT + '", "extra":true}\n}\n').encode()


class NeovimSnapshotTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix="nvim snapshot ")
        self.addCleanup(directory.cleanup)
        self.base = Path(directory.name)
        self.home = self.base / "home with spaces"
        self.home.mkdir(mode=0o700)
        self.source = self.base / "dotfiles"
        self.source.mkdir()
        self.bin = self.base / "commands"
        self.bin.mkdir()
        # サブプロセスも実Git・Neovimを探索できないPATHで実行する。
        self.environment = {"HOME": str(self.home), "PATH": str(self.bin), "LC_ALL": "C"}
        environment = patch.dict(os.environ, self.environment, clear=True)
        environment.start()
        self.addCleanup(environment.stop)
        self.lock = self.home / ".config/nvim/lazy-lock.json"
        self.lock.parent.mkdir(parents=True)
        self.lock.write_bytes(RAW)
        for name, body in {
            "git": '''import pathlib, sys
args = sys.argv[1:]
source = args[args.index("-C") + 1]
if "--show-toplevel" in args:
    print(pathlib.Path(source).resolve())
elif "rev-parse" in args:
    print("a" * 40)
elif "status" in args:
    pass
else:
    sys.exit(1)
''',
            "nvim": '''import sys
assert sys.argv[1:] == ["--version"]
print("NVIM v0.12.6")
''',
        }.items():
            path = self.bin / name
            path.write_text(f"#!{sys.executable}\n" + body)
            path.chmod(0o700)
        self.root = self.home / ".local/state/dotfiles/neovim-snapshots/nvim"

    def invoke(self, *args, status=0):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            result = snapshot.main(list(args))
        self.assertEqual(result, status, err.getvalue())
        return json.loads(out.getvalue()) if result == 0 else err.getvalue()

    def save(self, *args):
        return self.invoke("save", "--source", str(self.source), *args)

    def saved(self):
        result = self.save()
        return result["id"], Path(result["path"])

    def rewrite_metadata(self, directory, change):
        path = directory / "metadata.json"
        value = json.loads(path.read_bytes())
        change(value)
        path.write_text(json.dumps(value))

    def test_save_preserves_original_and_records_versions_permissions_and_hash(self):
        identifier, directory = self.saved()
        self.assertEqual(self.lock.read_bytes(), RAW)
        self.assertEqual((directory / "lazy-lock.json").read_bytes(), RAW)
        metadata = self.invoke("show", identifier)
        self.assertEqual(metadata["lockfile"]["sha256"], hashlib.sha256(RAW).hexdigest())
        self.assertEqual(metadata["dotfiles"]["commit"], COMMIT)
        self.assertEqual(metadata["neovim"]["version"], "NVIM v0.12.6")
        self.assertEqual(metadata["lazy_nvim"]["commit"], COMMIT)
        self.assertEqual(metadata["config_application"], "unverified")
        for path in (self.root, directory, directory / "lazy-lock.json", directory / "metadata.json"):
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o700 if path.is_dir() else 0o600)

    def test_labels_and_notes_round_trip_without_execution(self):
        note = '$(touch forbidden)\n\x1b[31m'
        result = self.save("--label", "proot", "--note", note)
        listed = self.invoke("list")
        self.assertEqual(listed[0]["note"], note)
        self.assertEqual(self.invoke("show", result["id"])["label"], "proot")
        self.assertFalse((self.base / "forbidden").exists())

    def test_read_operations_do_not_create_missing_storage(self):
        self.assertEqual(self.invoke("list"), [])
        self.assertFalse(self.root.exists())
        self.invoke("show", "20261117T000000Z-12345678", status=1)
        self.assertFalse(self.root.exists())

    def test_custom_xdg_and_app_and_explicit_paths(self):
        for key in ("STATE", "CONFIG", "DATA"):
            os.environ[f"XDG_{key}_HOME"] = str(self.home / key)
        os.environ["NVIM_APPNAME"] = "nvim-test"
        result = self.save("--lockfile", str(self.lock), "--lazy-dir", str(self.base / "custom lazy"))
        self.assertIn("STATE/dotfiles/neovim-snapshots/nvim-test", result["path"])
        metadata = self.invoke("show", result["id"])
        self.assertEqual(metadata["app_name"], "nvim-test")
        self.assertEqual(metadata["lazy_nvim"]["path"], str(self.base / "custom lazy"))

    def test_custom_config_default_lockfile(self):
        os.environ["XDG_CONFIG_HOME"] = str(self.home / "config")
        target = self.home / "config/nvim/lazy-lock.json"
        target.parent.mkdir(parents=True)
        target.write_bytes(RAW)
        self.assertEqual(self.invoke("show", self.save()["id"])["lockfile"]["path"], str(target))

    def test_invalid_app_and_relative_xdg_are_rejected(self):
        for key, value in (("NVIM_APPNAME", "../other"), ("XDG_STATE_HOME", "relative")):
            with self.subTest(key=key), patch.dict(os.environ, {key: value}):
                self.invoke("save", "--source", str(self.source), status=1)
        self.assertFalse(self.root.exists())

    def test_storage_inside_source_is_rejected(self):
        with patch.dict(os.environ, {"XDG_STATE_HOME": str(self.source / "state")}):
            self.invoke("save", "--source", str(self.source), status=1)
        self.assertFalse((self.source / "state").exists())

    def test_invalid_lockfiles_fail_without_creating_storage_or_echoing_data(self):
        for content in (b"PRIVATE malformed", b"[]", b'{"x":{}}', b'{"x":1,"x":2}', b'{"x":NaN}'):
            with self.subTest(content=content):
                self.lock.write_bytes(content)
                error = self.invoke("save", "--source", str(self.source), status=1)
                self.assertNotIn("PRIVATE", error)
                self.assertFalse(self.root.exists())

    def test_empty_lockfile_is_valid(self):
        self.lock.write_bytes(b"{}")
        self.assertEqual(self.invoke("show", self.save()["id"])["lockfile"]["entries"], 0)

    def test_missing_lockfile_and_source_git_failure(self):
        self.lock.unlink()
        self.invoke("save", "--source", str(self.source), status=1)
        self.lock.write_bytes(RAW)
        (self.bin / "git").unlink()
        self.invoke("save", "--source", str(self.source), status=1)
        self.assertFalse(self.root.exists())

    def test_missing_optional_version_tools_produces_warnings(self):
        (self.bin / "nvim").unlink()
        original = snapshot.revision
        with patch.object(snapshot, "revision", side_effect=lambda path: original(path) if path == self.source else snapshot.require(False, "unavailable")):
            result = self.save()
        metadata = self.invoke("show", result["id"])
        self.assertIsNone(metadata["neovim"]["version"])
        self.assertIsNone(metadata["lazy_nvim"]["commit"])
        self.assertEqual(len(metadata["warnings"]), 2)

    def test_git_status_records_only_booleans_and_handles_rename(self):
        original = snapshot.git
        def fake(source, *args):
            if args[0] == "status":
                return "R  new\0?? private old\0?? private untracked\0"
            return original(source, *args)
        with patch.object(snapshot, "git", side_effect=fake):
            result = self.save()
        metadata = self.invoke("show", result["id"])
        self.assertTrue(metadata["dotfiles"]["tracked_changes"])
        self.assertTrue(metadata["dotfiles"]["untracked_files"])
        self.assertNotIn("private", json.dumps(metadata))
        self.assertTrue(metadata["warnings"])

    def test_git_commands_disable_helpers_and_secret_environment(self):
        with patch.object(snapshot.subprocess, "run") as command:
            command.return_value.stdout = b"result"
            snapshot.git(self.source, "status")
        args, kwargs = command.call_args
        self.assertIn("core.fsmonitor=false", args[0])
        self.assertIn("--no-optional-locks", args[0])
        self.assertNotIn("HOME", kwargs["env"])
        self.assertEqual(kwargs["env"]["GIT_CONFIG_GLOBAL"], os.devnull)

    def test_prepare_is_read_only_and_reports_commit_difference(self):
        identifier, directory = self.saved()
        before = {str(p): p.read_bytes() for p in directory.iterdir()}
        with patch.object(snapshot, "source_info", return_value={"commit": "b" * 40, "tracked_changes": True, "untracked_files": False}):
            report = self.invoke("prepare", identifier, "--source", str(self.source))
        self.assertFalse(report["same_config_commit"])
        self.assertTrue(report["steps"])
        self.assertEqual(before, {str(p): p.read_bytes() for p in directory.iterdir()})
        self.assertEqual(self.lock.read_bytes(), RAW)

    def test_corrupt_lock_is_rejected_by_all_read_operations(self):
        identifier, directory = self.saved()
        (directory / "lazy-lock.json").write_bytes(b"{}")
        for args in (("show", identifier), ("list",), ("prepare", identifier, "--source", str(self.source))):
            with self.subTest(args=args):
                self.invoke(*args, status=1)

    def test_schema_and_metadata_integrity_are_validated(self):
        identifier, directory = self.saved()
        original = (directory / "metadata.json").read_bytes()
        for change in (lambda m: m.update(schema_version=2), lambda m: m.update(id="wrong"),
                       lambda m: m["lockfile"].update(entries=99), lambda m: m.update(dotfiles={}),
                       lambda m: m.update(schema_version=True), lambda m: m.update(note=[]),
                       lambda m: m.update(created_at="not a date"),
                       lambda m: m.update(warnings=[{}]), lambda m: m["lazy_nvim"].update(commit=123)):
            with self.subTest(change=change):
                (directory / "metadata.json").write_bytes(original)
                self.rewrite_metadata(directory, change)
                self.invoke("show", identifier, status=1)

    def test_missing_metadata_is_not_reported_as_empty_list(self):
        _, directory = self.saved()
        (directory / "metadata.json").unlink()
        self.invoke("list", status=1)

    def test_symlink_lock_storage_and_snapshot_files_are_rejected(self):
        real = self.home / "real-lock"
        self.lock.rename(real)
        self.lock.symlink_to(real)
        self.invoke("save", "--source", str(self.source), status=1)
        self.lock.unlink()
        self.lock.write_bytes(RAW)
        state = self.home / ".local/state"
        state.parent.mkdir(exist_ok=True)
        target = self.home / "outside"
        target.mkdir(mode=0o700)
        state.symlink_to(target)
        self.invoke("save", "--source", str(self.source), status=1)
        self.assertEqual(list(target.iterdir()), [])
        state.unlink()
        identifier, directory = self.saved()
        (directory / "metadata.json").unlink()
        (directory / "metadata.json").symlink_to(real)
        self.invoke("show", identifier, status=1)

    def test_broad_permissions_are_rejected_without_chmod(self):
        identifier, directory = self.saved()
        for path, mode in ((directory, 0o755), (directory / "metadata.json", 0o644), (self.root, 0o755)):
            with self.subTest(path=path):
                previous = path.stat().st_mode & 0o777
                path.chmod(mode)
                self.invoke("show", identifier, status=1)
                self.assertEqual(path.stat().st_mode & 0o777, mode)
                path.chmod(previous)

    def test_write_failure_cleans_only_pending_directory(self):
        identifier, directory = self.saved()
        original = snapshot.write_file
        def fail(fd, name, content):
            if name == "metadata.json":
                raise OSError("simulated private error")
            original(fd, name, content)
        with patch.object(snapshot, "write_file", side_effect=fail):
            error = self.invoke("save", "--source", str(self.source), status=1)
        self.assertNotIn("private error", error)
        self.assertEqual([p.name for p in self.root.iterdir()], [identifier])
        self.assertEqual((directory / "lazy-lock.json").read_bytes(), RAW)

    def test_id_collision_never_overwrites_existing_snapshot(self):
        instant = snapshot.datetime.now(snapshot.timezone.utc)
        with patch.object(snapshot.uuid, "uuid4") as value, patch.object(snapshot, "datetime") as clock:
            clock.now.return_value = instant
            value.return_value.hex = "1" * 32
            identifier, directory = self.saved()
            before = (directory / "metadata.json").read_bytes()
            self.invoke("save", "--source", str(self.source), status=1)
        self.assertEqual((directory / "metadata.json").read_bytes(), before)
        self.assertEqual([p.name for p in self.root.iterdir()], [identifier])

    def test_incomplete_directories_are_not_listed(self):
        self.saved()
        (self.root / ".pending-fixture").mkdir(mode=0o700)
        self.assertEqual(len(self.invoke("list")), 1)

    def test_source_change_during_read_is_rejected(self):
        original = snapshot.os.stat
        def changed(path, *args, **kwargs):
            if path == self.lock:
                self.lock.write_bytes(b"{}")
            return original(path, *args, **kwargs)
        with patch.object(snapshot.os, "stat", side_effect=changed):
            self.invoke("save", "--source", str(self.source), status=1)
        self.assertFalse(self.root.exists())

    def test_parallel_cli_saves_are_complete_and_unique(self):
        def save(_):
            return subprocess.run([sys.executable, "-B", str(SCRIPT), "save", "--source", str(self.source)],
                                  env=self.environment, capture_output=True, text=True, timeout=15)
        with ThreadPoolExecutor(max_workers=4) as pool:
            results = list(pool.map(save, range(4)))
        for result in results:
            self.assertEqual(result.returncode, 0, result.stderr)
        identifiers = [json.loads(result.stdout)["id"] for result in results]
        self.assertEqual(len(set(identifiers)), 4)
        self.assertEqual(len(self.invoke("list")), 4)
        self.assertFalse(any(p.name.startswith(".pending-") for p in self.root.iterdir()))

    def test_fifo_and_oversized_lockfile_fail_without_reading(self):
        self.lock.unlink()
        os.mkfifo(self.lock)
        self.invoke("save", "--source", str(self.source), status=1)
        self.lock.unlink()
        with self.lock.open("wb") as stream:
            stream.truncate(snapshot.LIMIT + 1)
        self.invoke("save", "--source", str(self.source), status=1)
        self.assertFalse(self.root.exists())

    def test_snapshot_directory_symlink_and_traversal_are_rejected(self):
        identifier, directory = self.saved()
        alias = self.root / "20261117T000000Z-abcdef12"
        alias.symlink_to(directory, target_is_directory=True)
        self.invoke("show", alias.name, status=1)
        self.invoke("show", "../" + identifier, status=1)

    def test_json_errors_do_not_include_raw_private_values(self):
        identifier, directory = self.saved()
        (directory / "metadata.json").write_bytes(b"PRIVATE malformed")
        error = self.invoke("show", identifier, status=1)
        self.assertNotIn("PRIVATE", error)

    def test_version_timeout_is_optional_and_does_not_echo_stderr(self):
        with patch.object(snapshot.subprocess, "run", side_effect=subprocess.TimeoutExpired("private command", 10)):
            with self.assertRaisesRegex(snapshot.SnapshotError, "ローカル") as error:
                snapshot.run(["nvim", "--version"])
        self.assertNotIn("private", str(error.exception))

    def test_interrupt_after_publish_preserves_completed_snapshot(self):
        original = snapshot.os.rename
        def interrupted(*args, **kwargs):
            original(*args, **kwargs)
            raise KeyboardInterrupt
        with patch.object(snapshot.os, "rename", side_effect=interrupted):
            with self.assertRaises(KeyboardInterrupt):
                self.save()
        listed = self.invoke("list")
        self.assertEqual(len(listed), 1)
        self.assertEqual(self.invoke("show", listed[0]["id"])["lockfile"]["entries"], 1)
        self.assertFalse(any(p.name.startswith(".pending-") for p in self.root.iterdir()))

    def test_shared_parents_allow_traversal_but_snapshots_remain_private(self):
        shared = self.home / ".local/state/dotfiles"
        shared.mkdir(parents=True, mode=0o755)
        shared.chmod(0o755)
        shared.parent.chmod(0o755)
        identifier, directory = self.saved()
        self.assertEqual(shared.stat().st_mode & 0o777, 0o755)
        self.assertEqual(directory.parent.stat().st_mode & 0o777, 0o700)
        self.assertEqual(directory.stat().st_mode & 0o777, 0o700)
        self.invoke("show", identifier)

    def test_shared_parent_writable_by_others_is_rejected_without_changes(self):
        shared = self.home / ".local/state/dotfiles"
        shared.mkdir(parents=True)
        shared.chmod(0o777)
        self.invoke("save", "--source", str(self.source), status=1)
        self.assertEqual(shared.stat().st_mode & 0o777, 0o777)
        self.assertFalse((shared / "neovim-snapshots").exists())

    def test_invalid_id_and_usage_exit_codes(self):
        self.invoke("show", "../outside", status=1)
        with redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as error:
            snapshot.main(["save"])
        self.assertEqual(error.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
