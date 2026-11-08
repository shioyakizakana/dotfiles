"""providerの一致と初回導入を、秘密情報や実際の認証なしで検証する。"""

import json
from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
BASH = shutil.which("bash")
CHEZMOI = shutil.which("chezmoi")
MAKE = shutil.which("make")


class ProtonPassSetupTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix="provider setup ")
        self.addCleanup(directory.cleanup)
        self.base = Path(directory.name)
        self.bin = self.base / "bin"
        self.bin.mkdir()
        self.repo = self.base / "repository"
        (self.repo / "bootstrap").mkdir(parents=True)
        (self.repo / ".chezmoiroot").write_text("home\n")
        self.script = self.repo / "bootstrap/setup-proton-pass.sh"
        shutil.copyfile(ROOT / "bootstrap/setup-proton-pass.sh", self.script)
        self.trace = self.base / "trace"
        self.trace.write_text("")
        self.stub("chezmoi", 'printf "%s\\n" "$SETTINGS"; exit "${CONFIG_EXIT:-0}"\n')
        self.env = {
            "HOME": str(self.base / "home"), "PATH": str(self.bin),
            "TRACE": str(self.trace), "SETTINGS": "wsl-ubuntu env",
            "CHEZMOI_BIN": str(self.bin / "chezmoi"),
            # prootでもこの値を継承することがある。設定された環境を優先する。
            "PREFIX": "/data/data/com.termux/files/usr",
        }
        self.stub("dirname", 'exec "' + shutil.which("dirname") + '" "$@"\n')

    def stub(self, name, body):
        path = self.bin / name
        path.write_text(f"#!{BASH}\n{body}")
        path.chmod(0o755)
        return path

    def run_setup(self, *arguments, **environment):
        # 副作用を持つ関数はすべて置換する。mainの呼び出し順序と設定検証は実装を使う。
        runner = r'''
source "$1"
shift
confirm_setup() { :; }
require() { :; }
check_keyring_environment() { printf 'keyring-check\n' >> "$TRACE"; return "${KEYRING_EXIT:-0}"; }
acquire_setup_lock() { printf 'lock\n' >> "$TRACE"; }
initialize_age_identity() { printf 'identity\n' >> "$TRACE"; }
initialize_secrets() { printf 'secrets\n' >> "$TRACE"; }
run_authenticated_setup() { printf 'login\n' >> "$TRACE"; }
print_next_steps() { printf '%s %s %s\n' "$linux_env" "$provider" "$REPO_ROOT"; }
main "$@"
'''
        return subprocess.run(
            [BASH, "-c", runner, "test", str(self.script), *arguments],
            env={**self.env, **environment}, capture_output=True, text=True, timeout=10,
        )

    def assert_stopped_before_secrets(self, result):
        self.assertNotEqual(result.returncode, 0)
        self.assertNotIn("lock", self.trace.read_text())
        self.assertNotIn("identity", self.trace.read_text())
        self.assertNotIn("secrets", self.trace.read_text())
        self.assertNotIn("login", self.trace.read_text())
        self.assertFalse((self.base / "home/.local/share/proton-pass").exists())

    def test_no_arguments_use_configured_environment_and_provider(self):
        for linux_env in ("termux", "proot-ubuntu", "native-ubuntu", "wsl-ubuntu", "qemu-ubuntu"):
            for provider in (("env",) if linux_env in ("termux", "proot-ubuntu") else ("env", "keyring")):
                with self.subTest(linux_env=linux_env, provider=provider):
                    self.trace.write_text("")
                    result = self.run_setup(SETTINGS=f"{linux_env} {provider}")
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertIn(f"{linux_env} {provider} {self.repo}", result.stdout)
                    self.assertEqual(self.trace.read_text().splitlines()[-4:],
                                     ["lock", "identity", "secrets", "login"])

    def test_explicit_matching_provider_is_accepted(self):
        result = self.run_setup("env", PROTON_PASS_KEY_PROVIDER="env", LINUX_ENV="wsl-ubuntu")
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_provider_mismatch_stops_before_secret_operations(self):
        self.assert_stopped_before_secrets(self.run_setup("keyring"))

    def test_inherited_provider_mismatch_stops_before_secret_operations(self):
        self.assert_stopped_before_secrets(self.run_setup(PROTON_PASS_KEY_PROVIDER="keyring"))

    def test_argument_and_environment_conflict_stops(self):
        self.assert_stopped_before_secrets(self.run_setup("env", PROTON_PASS_KEY_PROVIDER="keyring"))

    def test_environment_mismatch_stops(self):
        self.assert_stopped_before_secrets(self.run_setup(LINUX_ENV="termux"))

    def test_termux_and_proot_reject_keyring(self):
        for linux_env in ("termux", "proot-ubuntu"):
            with self.subTest(linux_env=linux_env):
                self.assert_stopped_before_secrets(self.run_setup(SETTINGS=f"{linux_env} keyring"))

    def test_invalid_or_missing_configuration_stops(self):
        for settings in ("unknown env", "wsl-ubuntu invalid", "", "wsl-ubuntu"):
            with self.subTest(settings=settings):
                self.assert_stopped_before_secrets(self.run_setup(SETTINGS=settings))
        self.assert_stopped_before_secrets(self.run_setup(CONFIG_EXIT="23"))

    def test_unavailable_keyring_stops_before_secret_operations(self):
        self.assert_stopped_before_secrets(self.run_setup(SETTINGS="wsl-ubuntu keyring", KEYRING_EXIT="1"))

    @unittest.skipUnless(CHEZMOI, "chezmoiが必要です")
    def test_bootstrap_reads_real_chezmoi_data_from_isolated_configuration(self):
        (self.repo / "home").mkdir()
        config = self.base / "config.json"
        command = [CHEZMOI, "--config", str(config),
                   "--destination", self.env["HOME"], "--cache", str(self.base / "cache"),
                   "--persistent-state", str(self.base / "state.db")]
        self.stub("chezmoi", "exec " + shlex.join(command) + ' "$@"\n')
        for flag, linux_env in (
            ("termux", "termux"), ("prootUbuntu", "proot-ubuntu"),
            ("wslUbuntu", "wsl-ubuntu"), ("qemuUbuntu", "qemu-ubuntu"),
            ("nativeUbuntu", "native-ubuntu"),
        ):
            with self.subTest(flag=flag):
                config.write_text(json.dumps({"data": {
                    **{name: False for name in ("termux", "prootUbuntu", "wslUbuntu", "qemuUbuntu", "nativeUbuntu")},
                    flag: True, "protonPassProvider": "env",
                }}))
                result = self.run_setup()
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn(f"{linux_env} env {self.repo}", result.stdout)

    @unittest.skipUnless(CHEZMOI, "chezmoiが必要です")
    def test_normal_wrapper_keeps_matching_provider_for_cli_and_cache(self):
        source = self.base / "empty-source"
        source.mkdir()
        config = self.base / "config.json"
        self.stub("age", 'printf "unexpected-age\\n" >> "$TRACE"; exit 99\n')
        self.stub("pass-cli", 'printf "cli %s %s\\n" "$PROTON_PASS_KEY_PROVIDER" "$*" >> "$TRACE"\n')
        cache = Path(self.env["HOME"]) / ".local/bin/proton-pass-key-cache.py"
        cache.parent.mkdir(parents=True)
        cache.write_text(f'#!{BASH}\nprintf "cache %s %s\\n" "$PROTON_PASS_KEY_PROVIDER" "$*" >> "$TRACE"\n')
        cache.chmod(0o755)
        for provider in ("env", "keyring"):
            for explicit in (False, True):
                with self.subTest(provider=provider, explicit=explicit):
                    self.trace.write_text("")
                    config.write_text(json.dumps({"data": {"protonPassProvider": provider}}))
                    rendered = subprocess.run(
                        [CHEZMOI, "--config", str(config), "--source", str(source),
                         "--destination", self.env["HOME"], "--cache", str(self.base / "cache"),
                         "--persistent-state", str(self.base / "state.db"),
                         "--refresh-externals=never", "execute-template"],
                        input=(ROOT / "home/dot_local/bin/executable_proton-pass.tmpl").read_text(),
                        env=self.env, capture_output=True, text=True, timeout=10,
                    )
                    self.assertEqual(rendered.returncode, 0, rendered.stderr)
                    wrapper = self.base / "wrapper"
                    wrapper.write_text(rendered.stdout)
                    environment = {**self.env}
                    if explicit:
                        environment["PROTON_PASS_KEY_PROVIDER"] = provider
                    result = subprocess.run(
                        [BASH, str(wrapper), "info"], env=environment,
                        capture_output=True, text=True, timeout=10,
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)
                    self.assertEqual(self.trace.read_text(),
                                     "cache env run -- info\n" if provider == "env" else "cli keyring info\n")

    @unittest.skipUnless(CHEZMOI, "chezmoiが必要です")
    def test_wrappers_reject_provider_override_before_decryption(self):
        source = self.base / "empty-source"
        source.mkdir()
        config = self.base / "config.json"
        self.stub("age", 'printf "age\\n" >> "$TRACE"; exit 99\n')
        self.stub("pass-cli", 'printf "pass-cli\\n" >> "$TRACE"; exit 99\n')
        for name in ("proton-pass", "init-proton-pass"):
            for provider, requested in (("env", "keyring"), ("keyring", "env")):
                with self.subTest(name=name, provider=provider):
                    config.write_text(json.dumps({"data": {"protonPassProvider": provider}}))
                    template = ROOT / f"home/dot_local/bin/executable_{name}.tmpl"
                    result = subprocess.run(
                        [CHEZMOI, "--config", str(config), "--source", str(source),
                         "--destination", self.env["HOME"], "--cache", str(self.base / "cache"),
                         "--persistent-state", str(self.base / "state.db"),
                         "--refresh-externals=never", "execute-template"],
                        input=template.read_text(), env=self.env, capture_output=True,
                        text=True, timeout=10,
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)
                    wrapper = self.base / name
                    wrapper.write_text(result.stdout)
                    subprocess.run([BASH, "-n", str(wrapper)], check=True)
                    arguments = ["login"] if name == "proton-pass" else []
                    execution = subprocess.run(
                        [BASH, str(wrapper), *arguments],
                        env={**self.env, "PROTON_PASS_KEY_PROVIDER": requested},
                        capture_output=True, text=True, timeout=10,
                    )
                    self.assertNotEqual(execution.returncode, 0)
                    self.assertIn("一致しません", execution.stderr)
                    self.assertEqual(self.trace.read_text(), "")

    @unittest.skipUnless(MAKE, "makeが必要です")
    def test_make_wrapper_deploys_only_wrapper_and_cache_without_scripts_or_externals(self):
        wrapper = self.base / "proton-pass"
        wrapper.write_text("fixture\n")
        wrapper.chmod(0o755)
        cache = self.base / "proton-pass-key-cache.py"
        cache.write_text("fixture\n")
        cache.chmod(0o755)
        self.stub("chezmoi", 'printf "%s\\n" "$@" >> "$TRACE"\n')
        result = subprocess.run(
            [MAKE, "--no-print-directory", "-f", str(ROOT / "Makefile"), "wrapper",
             f"CHEZMOI_BIN={self.bin / 'chezmoi'}", f"PROTON_PASS_WRAPPER={wrapper}",
             f"PROTON_PASS_CACHE={cache}", "--assume-old=require"],
            env=self.env, capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.trace.read_text().splitlines(), [
            "--source", str(ROOT), "apply", "--include=files", "--refresh-externals=never",
            str(wrapper), str(cache),
        ])

    @unittest.skipUnless(MAKE, "makeが必要です")
    def test_make_bootstrap_does_not_apply_and_passes_checkout_and_binary(self):
        bootstrap = self.repo / "bootstrap/mock.sh"
        bootstrap.write_text('printf "%s\\n" "$CHEZMOI_SOURCE_DIR" "$CHEZMOI_BIN" "$#"\n')
        result = subprocess.run(
            [MAKE, "--no-print-directory", "-f", str(ROOT / "Makefile"), "bootstrap",
             f"BOOTSTRAP={bootstrap}", f"CHEZMOI_BIN={self.bin / 'chezmoi'}",
             # requireだけを成功させ、bootstrapのレシピを実行する。
             "--assume-old=require"],
            env={**self.env, "PATH": str(Path(BASH).parent)},
            capture_output=True, text=True, timeout=10,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn(str(ROOT), result.stdout)
        self.assertIn(str(self.bin / "chezmoi"), result.stdout)
        self.assertTrue(result.stdout.rstrip().endswith("0"))
        self.assertNotIn("apply", result.stdout)


if __name__ == "__main__":
    unittest.main()
