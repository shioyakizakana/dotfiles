"""秘密情報や実プロセスを使わず、キャッシュとCLIの環境を検証する。"""

import importlib.machinery
import importlib.util
import os
from pathlib import Path
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


class CacheEnvironmentTests(unittest.TestCase):
    def setUp(self):
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


if __name__ == "__main__":
    unittest.main()
