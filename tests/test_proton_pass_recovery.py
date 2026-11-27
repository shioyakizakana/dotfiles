"""偽age・偽CLIと隔離HOMEで、実プロセスの復旧・排他・TTLを検証する。"""

import json
import os
from pathlib import Path
import runpy
import shutil
import signal
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest
from unittest import mock


ROOT = Path(__file__).resolve().parents[1]
CHEZMOI = shutil.which("chezmoi")
BASH = shutil.which("bash")


@unittest.skipUnless(CHEZMOI and BASH, "chezmoi・Bashが必要です")
class ProtonPassRecoveryTests(unittest.TestCase):
    def setUp(self):
        # Termuxでもプロジェクト用Unixソケットの107バイト制限に収める。
        directory = tempfile.TemporaryDirectory(prefix="")
        self.addCleanup(directory.cleanup)
        self.base = Path(directory.name)
        self.home = self.base / "home space"
        self.bin = self.home / ".local/bin"
        self.bin.mkdir(parents=True)
        self.source = self.base / "source"
        self.source.mkdir()
        self.control = self.base / "control"
        self.control.mkdir()
        self.trace = self.base / "trace.jsonl"
        self.env = {
            "HOME": str(self.home), "PATH": str(self.bin),
            "XDG_DATA_HOME": str(self.home / ".local/share"),
            "XDG_CONFIG_HOME": str(self.home / ".config"),
            "XDG_CACHE_HOME": str(self.home / ".cache"),
            "PYTHONDONTWRITEBYTECODE": "1", "PROTON_PASS_CACHE_TTL": "60",
            "TEST_CONTROL": str(self.control), "TEST_TRACE": str(self.trace),
            "PREFIX": str(self.base / "prefix"),
        }
        prefix_bin = self.base / "prefix/bin"
        prefix_bin.mkdir(parents=True)
        (prefix_bin / "env").symlink_to(shutil.which("env"))
        for name in ("bash", "dirname", "flock", "install", "mktemp", "mv", "chmod", "rm"):
            executable = shutil.which(name)
            self.assertIsNotNone(executable, name)
            (self.bin / name).symlink_to(executable)
        (self.bin / "python3").symlink_to(sys.executable)
        self.config = self.base / "config.json"
        self.config.write_text(json.dumps({"data": {
            "protonPassProvider": "env", "termux": sys.platform == "android",
        }}))
        self.helper = self.render("private_executable_proton-pass-key-cache.py.tmpl",
                                  "proton-pass-key-cache.py")
        self.wrapper = self.render("executable_proton-pass.tmpl", "proton-pass")
        self.cache_module = runpy.run_path(str(self.helper))
        self.processes = []
        self.servers = {}
        self.data = {}
        self.runtime = {}
        self.addCleanup(self.stop_processes)
        self.stub("age", '''
            import sys
            from pathlib import Path
            if sys.argv[1] == "-r":
                print("fixture encrypted:" + sys.stdin.read(), end="")
            elif sys.argv[1] == "-d":
                value = Path(sys.argv[-1]).read_text()
                print(value.removeprefix("fixture encrypted:"), end="")
            else:
                raise SystemExit(90)
        ''')
        self.stub("age-keygen", '''
            import sys
            if sys.argv[1:] != ["-y"]:
                raise SystemExit(91)
            sys.stdin.read()
            print("age1fixture")
        ''')
        self.stub("chezmoi", '''
            import sys
            print("termux env" if sys.platform == "android" else "proot-ubuntu env")
        ''')
        self.stub("pass-cli", '''
            import json
            import os
            from pathlib import Path
            import sys
            import time

            directory = Path(os.environ.get("PROTON_PASS_SESSION_DIR") or
                             Path.home() / ".local/share/proton-pass/cli")
            profile = directory.parent.name if directory.parent.parent.name == "projects" else "global"
            control = Path(os.environ["TEST_CONTROL"])
            command = sys.argv[1]
            key = os.environ.get("PROTON_PASS_ENCRYPTION_KEY")
            token = os.environ.get("PROTON_PASS_PERSONAL_ACCESS_TOKEN")
            with Path(os.environ["TEST_TRACE"]).open("a") as log:
                log.write(json.dumps({"profile": profile, "command": command,
                                      "session": str(directory), "key": key, "token": token}) + "\\n")
            session = directory / ".session"
            state = session / "state.json"
            if command == "info" and (control / (profile + ".hold")).exists():
                (control / (profile + ".ready")).touch()
                deadline = time.monotonic() + 20
                while not (control / (profile + ".release")).exists():
                    if time.monotonic() >= deadline:
                        raise SystemExit(92)
                    time.sleep(0.02)
            if command == "login":
                if not token or (control / (profile + ".reject-login")).exists():
                    print("fixture authentication failed", file=sys.stderr)
                    raise SystemExit(23)
                if state.exists() and json.loads(state.read_text())["key"] != key:
                    raise SystemExit(24)
                session.mkdir(mode=0o700, parents=True, exist_ok=True)
                state.write_text(json.dumps({"token": token, "key": key}))
                state.chmod(0o600)
                (control / (profile + ".expired")).unlink(missing_ok=True)
            elif command in ("info", "logout"):
                if not state.exists() or (control / (profile + ".expired")).exists():
                    print("fixture session expired", file=sys.stderr)
                    raise SystemExit(23)
                if token is not None or json.loads(state.read_text())["key"] != key:
                    raise SystemExit(24)
                if command == "logout":
                    state.unlink()
                    session.rmdir()
            else:
                raise SystemExit(93)
            print(profile)
        ''')
        self.identity = self.home / ".local/share/age/id_proton_pat.age"
        self.identity.parent.mkdir(parents=True)
        self.identity.write_text("age-encryption.org/v1\nfixture identity\n")
        self.identity.chmod(0o600)
        self.recipient = self.identity.with_name("proton-pass-recipient.txt")
        self.recipient.write_text("age1fixture\n")
        self.recipient.chmod(0o600)
        for index, profile in enumerate(("global", "alpha", "beta"), 1):
            data = self.home / ".local/share/proton-pass"
            runtime = self.home / ".cache/proton-pass-key-cache"
            if profile != "global":
                result = self.invoke(self.helper, "--profile", profile, "configure")
                self.assertEqual(result.returncode, 0, result.stderr)
                data = Path(result.stdout.strip())
                runtime = runtime / "projects" / profile
            data.mkdir(mode=0o700, parents=True, exist_ok=True)
            self.data[profile], self.runtime[profile] = data, runtime
            for name, value in (("token.age", "fixture-pat-" + profile),
                                ("encryption-key.age", str(index) * 64)):
                path = data / name
                path.write_text("fixture encrypted:" + value)
                path.chmod(0o600)

    def render(self, source_name, destination_name):
        result = subprocess.run(
            [CHEZMOI, "--config", str(self.config), "--source", str(self.source),
             "--destination", str(self.home), "--cache", str(self.base / "chezmoi-cache"),
             "--persistent-state", str(self.base / "state.db"),
             "--refresh-externals=never", "--no-tty", "execute-template"],
            input=(ROOT / "home/dot_local/bin" / source_name).read_text(),
            env=self.env, capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        path = self.bin / destination_name
        path.write_text(result.stdout)
        path.chmod(0o700)
        return path

    def stub(self, name, body):
        path = self.bin / name
        path.write_text(f"#!{sys.executable}\n" + textwrap.dedent(body).lstrip())
        path.chmod(0o700)

    def invoke(self, *arguments, **environment):
        return subprocess.run(arguments, env={**self.env, **environment},
                              capture_output=True, text=True, timeout=15)

    def spawn(self, arguments, **options):
        process = subprocess.Popen(arguments, **options)
        self.processes.append(process)
        return process

    def stop_processes(self):
        for runtime in self.runtime.values():
            self.cache_module["try_request"](runtime / "agent.sock", {"op": "lock"})
        for process in reversed(self.processes):
            try:
                process.communicate(timeout=2)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGTERM)
                try:
                    process.communicate(timeout=2)
                except subprocess.TimeoutExpired:
                    os.killpg(process.pid, signal.SIGKILL)
                    process.communicate(timeout=2)

    def wait_for(self, predicate):
        deadline = time.monotonic() + 10
        while not predicate():
            if time.monotonic() >= deadline:
                self.fail("検証用プロセスの準備が時間内に完了しませんでした")
            time.sleep(0.02)

    def start_cache(self, profile):
        if profile not in self.servers or self.servers[profile].poll() is not None:
            self.servers[profile] = self.spawn(
                [sys.executable, "-B", str(self.helper), "--profile", profile, "_serve", "60"],
                env=self.env, start_new_session=True,
                stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True,
            )
            process = self.servers[profile]
            def ready():
                if process.poll() is not None:
                    self.fail(f"検証用キャッシュが終了しました: {process.returncode}: {process.stderr.read()}")
                return self.cache_module["try_request"](
                    self.runtime[profile] / "agent.sock", {"op": "status"}) is not None
            self.wait_for(ready)

    def cli(self, profile, command):
        self.start_cache(profile)
        return self.invoke(self.wrapper, "--profile", profile, command)

    def login_all(self):
        for profile in self.data:
            result = self.cli(profile, "login")
            self.assertEqual(result.returncode, 0, result.stderr)

    def snapshots(self, *profiles):
        paths = [self.identity, self.recipient]
        for profile in profiles:
            data = self.data[profile]
            paths.extend((data / "token.age", data / "encryption-key.age"))
            paths.extend(path for path in (data / "cli").rglob("*") if path.is_file())
        return {path: (path.read_bytes(), path.stat().st_mode & 0o777) for path in paths}

    def bootstrap(self, profile, token):
        # 対話入力だけをダミー値へ置換し、配置・検証・暗号化・ログインは管理ソースを使う。
        runner = '''
source "$1"
initialize_environment --profile "$2" env
acquire_setup_lock
initialize_age_identity
[[ -s "$ENCRYPTION_FILE" ]] || die '既存のCLI暗号化鍵がありません'
printf '%s' "$TEST_NEW_PAT" | encrypt_once "$PAT_FILE"
run_authenticated_setup
'''
        return self.invoke(BASH, "-c", runner, "test", str(ROOT / "bootstrap/setup-proton-pass.sh"),
                           profile, TEST_NEW_PAT=token)

    def assert_no_credentials(self, result):
        output = result.stdout + result.stderr
        self.assertNotIn("fixture-pat-", output)
        for digit in "123":
            self.assertNotIn(digit * 64, output)

    def test_expired_session_recovers_only_by_explicit_login(self):
        self.login_all()
        before = self.snapshots("global", "alpha", "beta")
        (self.control / "alpha.expired").touch()
        result = self.cli("alpha", "info")
        self.assertEqual(result.returncode, 23, result.stderr)
        self.assert_no_credentials(result)
        self.assertEqual(self.snapshots("global", "alpha", "beta"), before)
        self.assertEqual(self.cli("alpha", "login").returncode, 0)
        self.assertEqual(self.cli("alpha", "info").stdout.strip(), "alpha")
        self.assertEqual(self.snapshots("global", "alpha", "beta"), before)

    def test_failed_login_releases_lock_without_replacing_session(self):
        self.login_all()
        before = self.snapshots("global", "alpha", "beta")
        reject = self.control / "alpha.reject-login"
        reject.touch()
        result = self.cli("alpha", "login")
        self.assertEqual(result.returncode, 23, result.stderr)
        self.assert_no_credentials(result)
        self.assertEqual(self.snapshots("global", "alpha", "beta"), before)
        reject.unlink()
        self.assertEqual(self.cli("alpha", "login").returncode, 0)
        self.assertEqual(self.snapshots("global", "alpha", "beta"), before)

    def renew_pat(self, logout_fails):
        self.login_all()
        others = self.snapshots("global", "beta")
        key = self.data["alpha"] / "encryption-key.age"
        previous_key = key.read_bytes()
        if logout_fails:
            (self.control / "alpha.expired").touch()
        result = self.cli("alpha", "logout")
        self.assertEqual(result.returncode, 23 if logout_fails else 0, result.stderr)
        result = self.invoke(self.helper, "--profile", "alpha", "lock")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.servers["alpha"].wait(timeout=5)
        archive = self.base / "archive"
        archive.mkdir(mode=0o700)
        token = self.data["alpha"] / "token.age"
        previous_token = token.read_bytes()
        token.rename(archive / "token.age")
        if logout_fails:
            # セッションが残る場合、PAT欠落を再生成で回避しない。
            result = self.bootstrap("alpha", "fixture-pat-alpha-new")
            self.assertNotEqual(result.returncode, 0)
            self.assertFalse(token.exists())
            session = self.data["alpha"] / "cli/.session"
            session.rename(archive / "session")
        else:
            reject = self.control / "alpha.reject-login"
            reject.touch()
            result = self.bootstrap("alpha", "fixture-pat-alpha-new")
            self.assertNotEqual(result.returncode, 0)
            self.assert_no_credentials(result)
            self.assertEqual(token.read_text(), "fixture encrypted:fixture-pat-alpha-new")
            self.assertEqual(key.read_bytes(), previous_key)
            self.assertEqual(self.snapshots("global", "beta"), others)
            reject.unlink()
        result = self.bootstrap("alpha", "fixture-pat-alpha-new")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assert_no_credentials(result)
        self.assertEqual(token.read_text(), "fixture encrypted:fixture-pat-alpha-new")
        self.assertEqual((archive / "token.age").read_bytes(), previous_token)
        self.assertEqual(key.read_bytes(), previous_key)
        self.assertEqual(self.snapshots("global", "beta"), others)
        before = self.snapshots("alpha")
        result = self.bootstrap("alpha", "fixture-pat-must-not-replace")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.snapshots("alpha"), before)
        self.assertEqual(self.snapshots("global", "beta"), others)
        self.assertEqual(self.cli("alpha", "info").stdout.strip(), "alpha")

    def test_pat_update_preserves_shared_identity_key_and_other_profiles(self):
        self.renew_pat(logout_fails=False)

    def test_failed_logout_recovers_after_explicit_session_backup(self):
        self.renew_pat(logout_fails=True)

    def test_parallel_profiles_and_lock_logout_remain_independent(self):
        self.login_all()
        before = self.snapshots("global", "beta")
        running = {}
        for profile in ("alpha", "beta"):
            (self.control / f"{profile}.hold").touch()
            running[profile] = self.spawn(
                [str(self.wrapper), "--profile", profile, "info"],
                env=self.env, start_new_session=True, stdout=subprocess.PIPE,
                stderr=subprocess.PIPE, text=True,
            )
        self.wait_for(lambda: all((self.control / f"{profile}.ready").exists() for profile in running))
        self.assertTrue(all(process.poll() is None for process in running.values()))
        result = self.cli("alpha", "info")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("同じプロジェクトの処理が実行中", result.stderr)
        self.assertNotEqual(self.bootstrap("alpha", "fixture-pat-unused").returncode, 0)
        self.assertEqual(self.cli("global", "info").stdout.strip(), "global")
        (self.control / "alpha.release").touch()
        stdout, stderr = running["alpha"].communicate(timeout=5)
        self.assertEqual(running["alpha"].returncode, 0, stderr)
        self.assertEqual(stdout.strip(), "alpha")
        self.assertEqual(self.cli("alpha", "logout").returncode, 0)
        self.assertEqual(self.invoke(self.helper, "--profile", "alpha", "lock").returncode, 0)
        self.assertIsNone(running["beta"].poll())
        (self.control / "beta.release").touch()
        stdout, stderr = running["beta"].communicate(timeout=5)
        self.assertEqual(running["beta"].returncode, 0, stderr)
        self.assertEqual(stdout.strip(), "beta")
        self.assertEqual(self.snapshots("global", "beta"), before)
        for event in map(json.loads, self.trace.read_text().splitlines()):
            index = ("global", "alpha", "beta").index(event["profile"]) + 1
            self.assertEqual(event["key"], str(index) * 64)
            self.assertEqual(Path(event["session"]), self.data[event["profile"]] / "cli")
            self.assertEqual(event["token"], "fixture-pat-" + event["profile"]
                             if event["command"] == "login" else None)

    def test_expired_cache_removes_socket_and_unlock_starts_new_process(self):
        runtime = self.runtime["alpha"]
        socket_path = runtime / "agent.sock"
        unlock = self.cache_module["unlock"]
        for attempt in range(2):
            # Popenは実行し、生成したPIDだけを追跡して失敗時にも回収する。
            with mock.patch.dict(os.environ, {**self.env, "PROTON_PASS_CACHE_DIR": str(runtime)}, clear=True), \
                    mock.patch("subprocess.Popen", side_effect=self.spawn_unmocked):
                unlock(self.identity, self.data["alpha"] / "encryption-key.age",
                       socket_path, runtime / "agent.lock", 2)
            self.assertEqual(len(self.processes), attempt + 1)
            process = self.processes[-1]
            reply = self.cache_module["request"](socket_path, {"op": "get"})
            self.assertEqual(reply, {"ok": True, "key": "2" * 64})
            self.assertEqual(socket_path.stat().st_mode & 0o777, 0o600)
            process.wait(timeout=6)
            self.assertEqual(process.returncode, 0)
            self.assertFalse(socket_path.exists())
            self.assertEqual(self.invoke(self.helper, "--profile", "alpha", "status").stdout.strip(), "ロック中")

    def spawn_unmocked(self, *arguments, **options):
        process = REAL_POPEN(*arguments, **options)
        if "_serve" in arguments[0]:
            self.processes.append(process)
        return process


REAL_POPEN = subprocess.Popen


if __name__ == "__main__":
    unittest.main()
