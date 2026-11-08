"""TermuxとUbuntuの導入経路を、ダミーパッケージだけで再現する。"""

from pathlib import Path
import shlex
import shutil
import subprocess
import tempfile
import unittest


SOURCE = Path(__file__).resolve().parents[1] / "bootstrap/bootstrap-tools.sh"
BASH = shutil.which("bash")
MKDIR = shutil.which("mkdir")
CAT = shutil.which("cat")
CHMOD = shutil.which("chmod")
PACKAGES = {"ca-certificates", "curl", "git", "age", "chezmoi", "python", "make",
            "openssl-tool", "wget", "util-linux", "procps", "file", "coreutils", "mise"}


@unittest.skipUnless(BASH and MKDIR and CAT and CHMOD, "Bash・mkdir・cat・chmodが必要です")
class BootstrapPlatformTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory(prefix="bootstrap platforms ")
        self.addCleanup(directory.cleanup)
        self.base = Path(directory.name)
        self.home = self.base / "home with spaces"
        self.home.mkdir()
        self.prefix = self.base / "data/data/com.termux/files/usr"
        self.bin = self.prefix / "bin"
        self.bin.mkdir(parents=True)
        self.state = self.base / "installed"
        self.state.mkdir()
        self.trace = self.base / "trace"
        self.trace.write_text("")
        self.source = self.base / "bootstrap-tools.sh"
        # 実行中のホストがprootでも、環境判定のfixtureへ混入させない。
        self.source.write_text(SOURCE.read_text().replace(
            "/proc/1/root/.proot", shlex.quote(str(self.base / "no-proot-marker"))
        ))
        self.environment = {
            "HOME": str(self.home), "PATH": str(self.bin), "PREFIX": str(self.prefix),
            "STATE": str(self.state), "TRACE": str(self.trace), "LC_ALL": "C",
        }
        self.stub("uname", 'case "$1" in -s) printf "Linux\\n";; -m) printf "aarch64\\n";; esac\n')
        self.stub("id", 'printf "%s\\n" "${FIXTURE_UID:-1000}"\n')
        self.stub("sh", "exit 89\n")
        self.stub("mkdir", f'exec {shlex.quote(MKDIR)} "$@"\n')
        self.stub("cat", f'exec {shlex.quote(CAT)} "$@"\n')
        # 予想外の導入・ネットワーク呼び出しも、ホストの実コマンドへ渡さない。
        for name in ("curl", "apt-get", "sudo", "brew"):
            self.stub(name, f'printf "forbidden:{name}\\n" >> "$TRACE"; exit 89\n')
        self.stub("dpkg-query", '''
package="${@: -1}"
[[ -f "$STATE/$package" ]] || exit 1
printf 'install ok installed'
''')
        self.stub("pkg", '''
printf 'pkg %s\\n' "$*" >> "$TRACE"
if [[ "$1" == update ]]; then exit "${UPDATE_EXIT:-0}"; fi
[[ "$1" == install ]] || exit 89
[[ "${INSTALL_EXIT:-0}" == 0 ]] || exit "$INSTALL_EXIT"
shift 2
for package do
  [[ "${OMIT_PACKAGE:-}" == "$package" ]] && continue
  : > "$STATE/$package"
  case "$package" in
    chezmoi|mise) printf '#!%s\\nexit 0\\n' "$FIXTURE_BASH" > "$PREFIX/bin/$package"
                 "$FIXTURE_CHMOD" 755 "$PREFIX/bin/$package";;
  esac
done
''')
        self.environment["FIXTURE_BASH"] = BASH
        self.environment["FIXTURE_CHMOD"] = CHMOD

    def stub(self, name, code):
        path = self.bin / name
        path.write_text(f"#!{BASH}\n{code}")
        path.chmod(0o755)
        return path

    def run_script(self, body='main --install', **environment):
        return subprocess.run(
            [BASH, "-c", '''source "$1"
read_os_release() { ID="${FIXTURE_OS:-}"; PRETTY_NAME="${FIXTURE_OS:-Termux}"; }
''' + body, "--", str(self.source)],
            env={**self.environment, **environment}, input="",
            capture_output=True, text=True, timeout=10,
        )

    def test_termux_installs_native_packages_without_linux_installers(self):
        result = self.run_script(TERMUX_MAIN_PACKAGE_FORMAT="debian")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual({path.name for path in self.state.iterdir()}, PACKAGES)
        calls = self.trace.read_text().splitlines()
        self.assertEqual(calls.count("pkg update -y"), 1)
        self.assertEqual(len(calls), 3)
        self.assertTrue(all(call.startswith("pkg ") for call in calls))
        self.assertIn("[MANUAL] pass-cli", result.stdout)
        self.assertIn("[SKIP] Homebrew", result.stdout)
        self.assertIn("認証準備は未完了", result.stderr)
        self.assertFalse((self.home / ".local").exists())

    def test_repeated_termux_install_does_not_update_or_reinstall_packages(self):
        result = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.trace.write_text("")
        result = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.trace.read_text(), "")

    def test_termux_installs_only_missing_packages(self):
        for name in ("git", "age", "python"):
            (self.state / name).touch()
        result = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = self.trace.read_text().splitlines()
        installed = set(calls[1].split()[3:])
        self.assertEqual(installed, PACKAGES - {"git", "age", "python", "mise"})

    def test_termux_check_is_read_only_and_marks_existing_pass_cli_unverified(self):
        self.stub("pass-cli", 'printf "forbidden:pass-cli\\n" >> "$TRACE"; exit 89\n')
        result = self.run_script('main --check')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("[UNVERIFIED] pass-cli", result.stdout)
        self.assertIn("[SKIP] Homebrew", result.stdout)
        self.assertEqual(self.trace.read_text(), "")
        self.assertEqual(list(self.home.iterdir()), [])
        self.assertEqual(list(self.state.iterdir()), [])

    def test_ubuntu_guest_takes_precedence_over_inherited_termux_prefix(self):
        result = self.run_script('check_environment; printf "%s %s\\n" "$IS_TERMUX" "$IS_PROOT"',
                                 FIXTURE_OS="ubuntu", BOOTSTRAP_PROOT="1")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(result.stdout.endswith("false true\n"))

    def test_ubuntu_keeps_apt_and_proot_skips_homebrew(self):
        # 導入引数だけを記録する。rootでも非rootでも実APT・sudoを呼ばない。
        self.stub("apt-get", 'printf "apt %s\\n" "$*" >> "$TRACE"\n')
        self.stub("sudo", 'printf "sudo %s\\n" "$*" >> "$TRACE"\n')
        result = self.run_script('get_brew_path() { return 1; }; check_environment; install_base_tools; install_homebrew',
                                 FIXTURE_OS="ubuntu", BOOTSTRAP_PROOT="1")
        self.assertEqual(result.returncode, 0, result.stderr)
        calls = self.trace.read_text()
        self.assertIn("update\n", calls)
        self.assertIn("install -y ca-certificates curl git age build-essential procps file\n", calls)
        self.assertNotIn("pkg ", calls)
        self.assertNotIn("forbidden:", calls)
        self.assertIn("proot環境ではHomebrewの導入をスキップ", result.stderr)

    def test_native_ubuntu_does_not_become_termux_when_prefix_is_inherited(self):
        result = self.run_script('check_environment; printf "%s %s\\n" "$IS_TERMUX" "$IS_PROOT"',
                                 FIXTURE_OS="ubuntu")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(result.stdout.endswith("false false\n"))

    def test_other_linux_with_inherited_prefix_is_rejected(self):
        result = self.run_script(FIXTURE_OS="debian")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.trace.read_text(), "")

    def test_termux_without_pkg_or_with_forced_proot_is_rejected(self):
        (self.bin / "pkg").unlink()
        result = self.run_script()
        self.assertNotEqual(result.returncode, 0)
        self.stub("pkg", "exit 89\n")
        result = self.run_script(BOOTSTRAP_PROOT="1")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.trace.read_text(), "")

    def test_termux_without_dpkg_or_running_as_root_does_not_install(self):
        result = self.run_script(FIXTURE_UID="0")
        self.assertNotEqual(result.returncode, 0)
        result = self.run_script(TERMUX_APP_PACKAGE_MANAGER="pacman")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("APT/dpkg", result.stderr)
        result = self.run_script(TERMUX_MAIN_PACKAGE_FORMAT="pacman")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("APT/dpkg", result.stderr)
        (self.bin / "dpkg-query").unlink()
        result = self.run_script()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("APT/dpkg", result.stderr)
        self.assertEqual(self.trace.read_text(), "")

    def test_failed_package_update_stops_before_install(self):
        result = self.run_script(UPDATE_EXIT="21")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.trace.read_text(), "pkg update -y\n")
        self.assertEqual(list(self.state.iterdir()), [])

    def test_failed_install_or_missing_package_is_not_reported_as_success(self):
        for options in ({"INSTALL_EXIT": "22"}, {"OMIT_PACKAGE": "python"}):
            with self.subTest(options=options):
                result = self.run_script(**options)
                self.assertNotEqual(result.returncode, 0)
                self.assertNotIn("基礎ツールの導入が完了", result.stdout)
                self.assertNotIn("forbidden:", self.trace.read_text())

    def test_bash_c_stdin_and_file_execution_support_help(self):
        for arguments, text in (
            ([BASH, "-c", SOURCE.read_text(), "bootstrap-tools.sh", "--help"], None),
            ([BASH, "-s", "--", "--help"], SOURCE.read_text()),
            ([BASH, str(SOURCE), "--help"], None),
        ):
            with self.subTest(arguments=arguments[:2]):
                result = subprocess.run(arguments, input=text, env=self.environment,
                                        capture_output=True, text=True, timeout=10)
                self.assertEqual(result.returncode, 0, result.stderr)
                self.assertIn("--check", result.stdout)
                self.assertEqual(self.trace.read_text(), "")


if __name__ == "__main__":
    unittest.main()
