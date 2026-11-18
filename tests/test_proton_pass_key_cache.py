"""秘密情報や実プロセスを使わず、キャッシュとCLIの環境を検証する。"""

import importlib.machinery
import importlib.util
import os
import json
import fcntl
import io
from pathlib import Path
import struct
import subprocess
import tempfile
import unittest
from unittest import mock


SOURCE = (
    Path(__file__).resolve().parents[1]
    / "home/dot_local/bin/private_executable_proton-pass-key-cache.py.tmpl"
)
LOADER = importlib.machinery.SourceFileLoader("proton_pass_key_cache", str(SOURCE))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
CACHE = importlib.util.module_from_spec(SPEC)
LOADER.exec_module(CACHE)


class CurrentUserIdsTests(unittest.TestCase):
    def test_native_and_proot_ids_are_derived_only_from_current_process(self):
        for kernel_uid in (1001, 10306):
            with (
                self.subTest(kernel_uid=kernel_uid),
                mock.patch.object(CACHE.os, "getuid", return_value=1001),
                mock.patch.object(Path, "read_text", return_value=f"Name:\tpython3\nUid:\t{kernel_uid}\t{kernel_uid}\t{kernel_uid}\t{kernel_uid}\n"),
            ):
                self.assertEqual(CACHE.current_user_ids(), {1001, kernel_uid})

    def test_missing_or_malformed_proc_status_does_not_accept_another_uid(self):
        for text in ("", "Uid:\t10306\n", "Uid:\tinvalid\t0\t0\t0\n", "Uid:\t-1\t-1\t-1\t-1\n",
                     "Uid:\t4294967295\t4294967295\t4294967295\t4294967295\n"):
            with (
                self.subTest(text=text),
                mock.patch.object(CACHE.os, "getuid", return_value=1001),
                mock.patch.object(Path, "read_text", return_value=text),
            ):
                self.assertEqual(CACHE.current_user_ids(), {1001})
        for error in (FileNotFoundError(), PermissionError(), UnicodeError()):
            with (
                self.subTest(error=type(error).__name__),
                mock.patch.object(CACHE.os, "getuid", return_value=1001),
                mock.patch.object(Path, "read_text", side_effect=error),
            ):
                self.assertEqual(CACHE.current_user_ids(), {1001})


class CacheEnvironmentTests(unittest.TestCase):
    def setUp(self):
        for stream in ("stdout", "stderr"):
            patch = mock.patch.object(CACHE.sys, stream, io.StringIO())
            patch.start()
            self.addCleanup(patch.stop)
        self.environment = {
            "PATH": "/dummy/bin",
            "PROTON_PASS_PERSONAL_ACCESS_TOKEN": "dummy-pat",
            "PROTON_PASS_ENCRYPTION_KEY": "dummy-inherited-key",
            "PROTON_PASS_KEY_PROVIDER": "env",
            "PROTON_PASS_CACHE_DIR": "/dummy/cache",
            "PROTON_PASS_CACHE_TTL": "900",
            "AGE_IDENTITY_FILE": "/dummy/identity.age",
        }
        self.environment_patch = mock.patch.dict(
            os.environ, self.environment, clear=True
        )
        self.environment_patch.start()
        self.addCleanup(self.environment_patch.stop)
        self.identity = Path("/dummy/identity.age")
        self.encrypted = Path("/dummy/key.age")
        self.socket = Path("/dummy/cache/agent.sock")
        self.lock = Path("/dummy/cache/agent.lock")

    def test_new_daemon_excludes_secrets_and_preserves_runtime_settings(self):
        replies = [None, None, {"ok": False}, {"ok": True}]
        with (
            mock.patch.object(CACHE, "decrypt_key", return_value="a" * 64),
            mock.patch.object(CACHE, "try_request", side_effect=replies),
            mock.patch.object(CACHE.subprocess, "Popen") as start,
        ):
            CACHE.unlock(self.identity, self.encrypted, self.socket, self.lock, 900)

        start.assert_called_once()
        daemon_environment = start.call_args.kwargs.get("env", os.environ)
        self.assertNotIn("PROTON_PASS_PERSONAL_ACCESS_TOKEN", daemon_environment)
        self.assertNotIn("PROTON_PASS_ENCRYPTION_KEY", daemon_environment)
        for name, value in self.environment.items():
            if name not in (
                "PROTON_PASS_PERSONAL_ACCESS_TOKEN",
                "PROTON_PASS_ENCRYPTION_KEY",
            ):
                self.assertEqual(daemon_environment[name], value)
        self.assertEqual(dict(os.environ), self.environment)

    def test_unlocked_cache_does_not_start_another_daemon(self):
        with (
            mock.patch.object(CACHE, "try_request", return_value={"ok": True}),
            mock.patch.object(CACHE, "decrypt_key") as decrypt,
            mock.patch.object(CACHE.subprocess, "Popen") as start,
        ):
            CACHE.unlock(self.identity, self.encrypted, self.socket, self.lock, 900)

        decrypt.assert_not_called()
        start.assert_not_called()

    def test_login_cli_receives_pat_and_cached_encryption_key(self):
        with (
            mock.patch.object(
                CACHE.sys, "argv", [str(SOURCE), "run", "--", "login"]
            ),
            mock.patch.object(
                CACHE,
                "paths",
                return_value=(self.identity, self.encrypted, self.socket.parent),
            ),
            mock.patch.object(CACHE, "check_dir"),
            mock.patch.object(
                CACHE, "try_request", return_value={"ok": True, "key": "b" * 64}
            ),
            mock.patch.object(CACHE.os, "execvpe") as execute,
        ):
            CACHE.main()

        execute.assert_called_once()
        executable, arguments, environment = execute.call_args.args
        self.assertEqual(executable, "pass-cli")
        self.assertEqual(arguments, ["pass-cli", "login"])
        self.assertEqual(environment["PROTON_PASS_PERSONAL_ACCESS_TOKEN"], "dummy-pat")
        self.assertEqual(environment["PROTON_PASS_ENCRYPTION_KEY"], "b" * 64)
        self.assertEqual(environment["PROTON_PASS_KEY_PROVIDER"], "env")
        self.assertEqual(dict(os.environ), self.environment)

    def test_ttl_presets_and_legacy_seconds_reach_unlock(self):
        for minutes in (15, 30, 45, 60):
            with (
                self.subTest(minutes=minutes),
                mock.patch.object(CACHE.sys, "argv", [str(SOURCE), "--ttl-minutes", str(minutes), "unlock"]),
                mock.patch.object(CACHE, "paths", return_value=(self.identity, self.encrypted, self.socket.parent)),
                mock.patch.object(CACHE, "check_dir"),
                mock.patch.object(CACHE, "unlock") as unlock,
            ):
                CACHE.main()
                self.assertEqual(unlock.call_args.args[-1], minutes * 60)
        for seconds in (1, 900, 1800, 2700, 3600):
            with (
                self.subTest(seconds=seconds),
                mock.patch.dict(os.environ, {"PROTON_PASS_CACHE_TTL": str(seconds)}),
                mock.patch.object(CACHE.sys, "argv", [str(SOURCE), "unlock"]),
                mock.patch.object(CACHE, "paths", return_value=(self.identity, self.encrypted, self.socket.parent)),
                mock.patch.object(CACHE, "check_dir"),
                mock.patch.object(CACHE, "unlock") as unlock,
            ):
                CACHE.main()
                self.assertEqual(unlock.call_args.args[-1], seconds)

    def test_invalid_ttl_stops_before_files_or_decryption(self):
        for arguments, value in (([], "0"), ([], "3601"), ([], "invalid"),
                                 (["--ttl-minutes", "0"], "900"),
                                 (["--ttl-minutes", "20"], "900"),
                                 (["--ttl-minutes", "61"], "900")):
            with (
                self.subTest(arguments=arguments, value=value),
                mock.patch.dict(os.environ, {"PROTON_PASS_CACHE_TTL": value}),
                mock.patch.object(CACHE.sys, "argv", [str(SOURCE), *arguments, "unlock"]),
                mock.patch.object(CACHE, "paths") as paths,
                mock.patch.object(CACHE, "unlock") as unlock,
            ):
                with self.assertRaises(SystemExit):
                    CACHE.main()
                paths.assert_not_called()
                unlock.assert_not_called()

    def test_daemon_receives_selected_ttl_even_with_invalid_inherited_value(self):
        with (
            mock.patch.dict(os.environ, {"PROTON_PASS_CACHE_TTL": "invalid"}),
            mock.patch.object(CACHE, "decrypt_key", return_value="a" * 64),
            mock.patch.object(CACHE, "try_request", side_effect=[None, None, {"ok": False}, {"ok": True}]),
            mock.patch.object(CACHE.subprocess, "Popen") as start,
        ):
            CACHE.unlock(self.identity, self.encrypted, self.socket, self.lock, 2700)
        self.assertEqual(start.call_args.args[0][-1], "2700")
        self.assertEqual(start.call_args.kwargs["env"]["PROTON_PASS_CACHE_TTL"], "2700")

    def test_default_ttl_is_fifteen_minutes(self):
        os.environ.pop("PROTON_PASS_CACHE_TTL")
        with (
            mock.patch.object(CACHE.sys, "argv", [str(SOURCE), "unlock"]),
            mock.patch.object(CACHE, "paths", return_value=(self.identity, self.encrypted, self.socket.parent)),
            mock.patch.object(CACHE, "check_dir"),
            mock.patch.object(CACHE, "unlock") as unlock,
        ):
            CACHE.main()
        self.assertEqual(unlock.call_args.args[-1], 900)


class ProjectCacheTests(unittest.TestCase):
    def setUp(self):
        for stream in ("stdout", "stderr"):
            patch = mock.patch.object(CACHE.sys, stream, io.StringIO())
            patch.start()
            self.addCleanup(patch.stop)
        directory = tempfile.TemporaryDirectory(prefix="pass profile ")
        self.addCleanup(directory.cleanup)
        self.home = Path(directory.name)
        self.env = {"HOME": str(self.home), "PATH": "/dummy/bin"}
        patch = mock.patch.dict(os.environ, self.env, clear=True)
        patch.start()
        self.addCleanup(patch.stop)
        self.identity = self.home / ".local/share/age/id_proton_pat.age"
        self.identity.parent.mkdir(parents=True)
        self.identity.write_text("dummy encrypted identity")
        self.identity.chmod(0o600)

    def register(self, name):
        data, identity, runtime = CACHE.project_paths(name, create=True)
        for file in (data / "token.age", data / "encryption-key.age"):
            file.write_text("dummy ciphertext " + name)
            file.chmod(0o600)
        return data, identity, runtime

    def run_cli(self, name, *arguments, exit_code=0):
        def execute(command, **kwargs):
            if command[0] == "age":
                return subprocess.CompletedProcess(command, 0, stdout=("dummy-pat-" + name).encode())
            return subprocess.CompletedProcess(command, exit_code)

        with (
            mock.patch.dict(os.environ, self.env, clear=True),
            mock.patch.object(CACHE.sys, "argv", [str(SOURCE), "--profile", name, "run", "--", *arguments]),
            mock.patch.object(CACHE, "try_request", return_value={"ok": True, "key": name[0] * 64}),
            mock.patch.object(CACHE.subprocess, "run", side_effect=execute) as run,
        ):
            with self.assertRaises(SystemExit) as result:
                CACHE.main()
            return result.exception.code, run

    def test_projects_use_independent_paths_and_private_permissions(self):
        first = self.register("alpha")
        second = self.register("beta")
        self.assertNotEqual(first[0], second[0])
        self.assertNotEqual(first[2], second[2])
        self.assertEqual(first[1], second[1])
        for data, _, runtime in (first, second):
            self.assertEqual(data.stat().st_mode & 0o777, 0o700)
            self.assertEqual(runtime.stat().st_mode & 0o777, 0o700)
            self.assertEqual(CACHE.project_paths(data.name), (data, self.identity, runtime))

    def test_proot_kernel_uid_is_accepted_for_own_ciphertexts(self):
        data, _, runtime = self.register("alpha")
        host_uid = os.getuid() + 10000
        original = Path.lstat
        def mapped_lstat(path, *args, **kwargs):
            info = original(path, *args, **kwargs)
            if path in (data / "token.age", data / "encryption-key.age"):
                values = list(info)
                values[4] = host_uid
                return os.stat_result(values)
            return info
        with (
            mock.patch.object(Path, "lstat", mapped_lstat),
            mock.patch.object(Path, "read_text", return_value=f"Uid:\t{host_uid}\t{host_uid}\t{host_uid}\t{host_uid}\n"),
        ):
            self.assertEqual(CACHE.project_paths("alpha"), (data, self.identity, runtime))

    def test_proot_kernel_uid_does_not_allow_foreign_owners_or_open_permissions(self):
        data, _, _ = self.register("alpha")
        host_uid = os.getuid() + 10000
        original = Path.lstat
        for owner, mode in ((host_uid + 1, 0o600), (host_uid, 0o640)):
            def mapped_lstat(path, *args, **kwargs):
                info = original(path, *args, **kwargs)
                if path == data / "token.age":
                    values = list(info)
                    values[0] = (info.st_mode & ~0o777) | mode
                    values[4] = owner
                    return os.stat_result(values)
                return info
            with (
                self.subTest(owner=owner, mode=mode),
                mock.patch.object(Path, "lstat", mapped_lstat),
                mock.patch.object(Path, "read_text", return_value=f"Uid:\t{host_uid}\t{host_uid}\t{host_uid}\t{host_uid}\n"),
            ):
                with self.assertRaises(SystemExit):
                    CACHE.project_paths("alpha")

    def test_kernel_uid_supports_private_runtime_directory(self):
        _, _, runtime = self.register("alpha")
        host_uid = os.getuid() + 10000
        original = Path.lstat
        def mapped_lstat(path, *args, **kwargs):
            info = original(path, *args, **kwargs)
            if path == runtime:
                values = list(info)
                values[4] = host_uid
                return os.stat_result(values)
            return info
        with (
            mock.patch.object(Path, "lstat", mapped_lstat),
            mock.patch.object(Path, "read_text", return_value=f"Uid:\t{host_uid}\t{host_uid}\t{host_uid}\t{host_uid}\n"),
        ):
            CACHE.check_dir(runtime)

    def test_kernel_uid_peer_is_accepted_and_another_peer_is_rejected(self):
        host_uid = os.getuid() + 10000
        incoming = iter(((host_uid + 1, {"op": "get"}),
                         (host_uid, {"op": "put", "key": "a" * 64}),
                         (host_uid, {"op": "get"}),
                         (host_uid, {"op": "lock"})))
        connections = []
        replies = []
        def accept():
            uid, request = next(incoming)
            conn = mock.MagicMock()
            conn.__enter__.return_value = conn
            conn.getsockopt.return_value = struct.pack("3i", 1, uid, 1)
            conn.recv.return_value = json.dumps(request).encode() + b"\n"
            conn.sendall.side_effect = lambda message: replies.append(json.loads(message))
            connections.append(conn)
            return conn, None
        server = mock.MagicMock()
        server.__enter__.return_value = server
        server.accept.side_effect = accept
        with (
            mock.patch.object(Path, "read_text", return_value=f"Uid:\t{host_uid}\t{host_uid}\t{host_uid}\t{host_uid}\n"),
            mock.patch.object(CACHE.socket, "socket", return_value=server),
            mock.patch.object(CACHE.os, "chmod"),
        ):
            CACHE.serve(self.home / "agent.sock", 900, self.home / "agent.lock")
        connections[0].recv.assert_not_called()
        connections[0].sendall.assert_not_called()
        self.assertEqual(replies, [{"ok": True}, {"ok": True, "key": "a" * 64}, {"ok": True}])

    def test_invalid_and_unregistered_names_stop_without_creating_storage(self):
        for name in ("", "../alpha", "a/b", "UPPER", "global", "a" * 65, "not-registered"):
            with self.subTest(name=name), self.assertRaises(SystemExit):
                CACHE.project_paths(name)
        self.assertFalse((self.home / ".cache").exists())

    def test_login_and_queries_keep_pat_and_session_separate(self):
        for name in ("alpha", "beta"):
            data, _, runtime = self.register(name)
            code, run = self.run_cli(name, "login")
            self.assertEqual(code, 0)
            self.assertEqual(run.call_args_list[0].args[0][-1], str(data / "token.age"))
            env = run.call_args.kwargs["env"]
            self.assertEqual(env["PROTON_PASS_PERSONAL_ACCESS_TOKEN"], "dummy-pat-" + name)
            self.assertEqual(env["PROTON_PASS_SESSION_DIR"], str(data / "cli"))
            self.assertEqual(env["PROTON_PASS_CACHE_DIR"], str(runtime))
            self.assertEqual(env["PROTON_PASS_KEY_PROVIDER"], "env")
            self.assertEqual(env["PROTON_PASS_ENCRYPTION_KEY"], name[0] * 64)
            self.env["PROTON_PASS_PERSONAL_ACCESS_TOKEN"] = "inherited-dummy-pat"
            self.env["PROTON_PASS_ENCRYPTION_KEY"] = "inherited-dummy-key"
            code, run = self.run_cli(name, "info", exit_code=17)
            self.assertEqual(code, 17)
            run.assert_called_once()
            self.assertNotIn("PROTON_PASS_PERSONAL_ACCESS_TOKEN", run.call_args.kwargs["env"])
            self.assertEqual(run.call_args.kwargs["env"]["PROTON_PASS_ENCRYPTION_KEY"], name[0] * 64)

    def test_unsafe_login_and_logout_stop_before_decryption_or_cli(self):
        self.register("alpha")
        for arguments in (("login", "--pat", "dummy"), ("logout", "--force"),
                          ("logout", "-f"), ("logout", "--force=true"), ("--profile", "beta")):
            with self.subTest(arguments=arguments):
                code, run = self.run_cli("alpha", *arguments)
                self.assertNotEqual(code, 0)
                run.assert_not_called()

    def test_conflicting_overrides_stop_before_decryption(self):
        self.register("alpha")
        for key, value in (("PROTON_PASS_KEY_PROVIDER", "keyring"),
                           ("PROTON_PASS_SESSION_DIR", str(self.home / "elsewhere")),
                           ("PROTON_PASS_CACHE_DIR", str(self.home / "elsewhere")),
                           ("AGE_IDENTITY_FILE", str(self.home / "elsewhere"))):
            with self.subTest(key=key), mock.patch.dict(os.environ, {key: value}):
                with self.assertRaises(SystemExit):
                    CACHE.project_paths("alpha")

    def test_ciphertext_symlinks_and_permissions_are_rejected_without_changes(self):
        data, _, _ = self.register("alpha")
        token = data / "token.age"
        token.chmod(0o644)
        with self.assertRaises(SystemExit):
            CACHE.project_paths("alpha")
        self.assertEqual(token.stat().st_mode & 0o777, 0o644)
        token.unlink()
        token.symlink_to(self.identity)
        with self.assertRaises(SystemExit):
            CACHE.project_paths("alpha")

    def test_writable_parent_and_repository_storage_are_rejected(self):
        data, _, _ = self.register("alpha")
        data.parent.chmod(0o777)
        with self.assertRaises(SystemExit):
            CACHE.project_paths("alpha")
        self.assertEqual(data.parent.stat().st_mode & 0o777, 0o777)
        data.parent.chmod(0o700)
        (self.home / ".git").mkdir()
        with self.assertRaises(SystemExit):
            CACHE.project_paths("alpha")

    def test_project_lock_conflicts_without_waiting_and_releases_after_cli(self):
        data, _, _ = self.register("alpha")
        with (data / ".cli.lock").open("a+b") as lock:
            (data / ".cli.lock").chmod(0o600)
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
            code, run = self.run_cli("alpha", "login")
            self.assertNotEqual(code, 0)
            run.assert_not_called()
        code, _ = self.run_cli("alpha", "info")
        self.assertEqual(code, 0)

    def test_project_lock_symlink_is_never_followed(self):
        data, _, _ = self.register("alpha")
        (data / ".cli.lock").symlink_to(self.identity)
        code, run = self.run_cli("alpha", "login")
        self.assertNotEqual(code, 0)
        run.assert_not_called()
        self.assertEqual(self.identity.read_text(), "dummy encrypted identity")

    def test_failed_pat_decryption_never_runs_cli_and_releases_lock(self):
        data, _, _ = self.register("alpha")
        with (
            mock.patch.object(CACHE.sys, "argv", [str(SOURCE), "--profile", "alpha", "run", "--", "login"]),
            mock.patch.object(CACHE.subprocess, "run", return_value=subprocess.CompletedProcess([], 1, b"dummy-private-value")) as run,
        ):
            with self.assertRaises(SystemExit):
                CACHE.main()
            run.assert_called_once()
            self.assertNotIn("dummy-private-value", CACHE.sys.stderr.getvalue())
        with (data / ".cli.lock").open("a+b") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)

    def test_missing_or_empty_ciphertext_does_not_regenerate_keys(self):
        data, _, _ = self.register("alpha")
        key = data / "encryption-key.age"
        key.write_text("")
        with self.assertRaises(SystemExit):
            CACHE.project_paths("alpha", create=True)
        self.assertEqual(key.read_text(), "")
        key.unlink()
        with self.assertRaises(SystemExit):
            CACHE.project_paths("alpha")
        self.assertFalse(key.exists())

    def test_long_socket_path_fails_before_registration(self):
        with self.assertRaises(SystemExit):
            CACHE.project_paths("a" * 64, create=True)
        self.assertFalse((self.home / ".cache").exists())

    def test_existing_session_prevents_replacing_a_missing_database_key(self):
        data, _, _ = self.register("alpha")
        (data / "cli/.session").mkdir(mode=0o700)
        (data / "encryption-key.age").unlink()
        with self.assertRaises(SystemExit):
            CACHE.project_paths("alpha", create=True)
        self.assertFalse((data / "encryption-key.age").exists())

    def test_session_symlink_is_rejected_before_decryption(self):
        data, _, _ = self.register("alpha")
        (data / "cli/.session").symlink_to(self.home)
        code, run = self.run_cli("alpha", "login")
        self.assertNotEqual(code, 0)
        run.assert_not_called()

    def test_repeated_profile_is_rejected_before_path_validation(self):
        with (
            mock.patch.object(CACHE.sys, "argv", [str(SOURCE), "--profile", "alpha", "--profile", "beta", "status"]),
            mock.patch.object(CACHE, "project_paths") as paths,
        ):
            with self.assertRaises(SystemExit):
                CACHE.main()
            paths.assert_not_called()

    def test_daemon_rejects_ttl_outside_maximum_before_serving(self):
        for value in ("0", "3601", "invalid"):
            with (
                self.subTest(value=value),
                mock.patch.object(CACHE.sys, "argv", [str(SOURCE), "_serve", value]),
                mock.patch.object(CACHE, "check_dir"),
                mock.patch.object(CACHE, "serve") as serve,
            ):
                with self.assertRaises(SystemExit):
                    CACHE.main()
                serve.assert_not_called()

    def test_cache_management_selects_project_without_pat_decryption(self):
        _, _, runtime = self.register("alpha")
        for command in ("status", "lock", "unlock"):
            with (
                self.subTest(command=command),
                mock.patch.dict(os.environ, self.env, clear=True),
                mock.patch.object(CACHE.sys, "argv", [str(SOURCE), "--profile", "alpha", command]),
                mock.patch.object(CACHE, "try_request", return_value={"ok": True, "remaining": 10}) as request,
                mock.patch.object(CACHE, "unlock") as unlock,
                mock.patch.object(CACHE.subprocess, "run") as run,
            ):
                CACHE.main()
                run.assert_not_called()
                if command == "unlock":
                    self.assertEqual(unlock.call_args.args[2], runtime / "agent.sock")
                else:
                    self.assertEqual(request.call_args.args[0], runtime / "agent.sock")

    def test_cache_expiry_uses_selected_ttl_and_reads_do_not_extend_it(self):
        for ttl in (900, 1800, 2700, 3600):
            with self.subTest(ttl=ttl):
                now = [0]
                replies = []
                incoming = iter(((0, {"op": "put", "key": "a" * 64}),
                                 (ttl - 1, {"op": "get"}),
                                 (ttl - 1, {"op": "status"}),
                                 (ttl, {"op": "status"})))
                def accept():
                    now[0], request = next(incoming)
                    conn = mock.MagicMock()
                    conn.__enter__.return_value = conn
                    conn.getsockopt.return_value = struct.pack("3i", 1, os.getuid(), 1)
                    conn.recv.return_value = json.dumps(request).encode() + b"\n"
                    conn.sendall.side_effect = lambda message: replies.append(json.loads(message))
                    return conn, None
                server = mock.MagicMock()
                server.__enter__.return_value = server
                server.accept.side_effect = accept
                with (
                    mock.patch.object(CACHE.socket, "socket", return_value=server),
                    mock.patch.object(CACHE.time, "monotonic", side_effect=lambda: now[0]),
                    mock.patch.object(CACHE.os, "chmod"),
                ):
                    CACHE.serve(self.home / "agent.sock", ttl, self.home / "agent.lock")
                self.assertEqual(replies[1], {"ok": True, "key": "a" * 64})
                self.assertEqual(replies[2], {"ok": True, "remaining": 1})
                self.assertEqual(replies[3], {"ok": False, "remaining": 0})


if __name__ == "__main__":
    unittest.main()
