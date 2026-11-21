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
            "openssl-tool", "wget", "util-linux", "procps", "file", "coreutils", "mise",
            "proton-pass-cli", "7zip", "atuin", "bat", "biome2", "bun", "codex", "deno",
            "eza", "fd", "ffmpeg", "gh", "ghq", "git-delta", "git-lfs", "gofumpt",
            "goimports", "golang", "golangci-lint", "gopls", "imagemagick", "jq", "lazygit",
            "lua-language-server", "lua51", "marksman", "neovim", "nim", "nodejs-lts",
            "npm", "oxlint", "pnpm", "poppler", "ripgrep", "ruby", "ruff", "rust",
            "shellcheck", "shfmt", "sops", "stylua", "taplo", "tealdeer", "tmux",
            "tree-sitter", "ty", "uv", "yazi", "yq", "zoxide"}


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
    proton-pass-cli) package=pass-cli ;;
  esac
  case "$package" in
    chezmoi|mise|pass-cli) printf '#!%s\\nexit 0\\n' "$FIXTURE_BASH" > "$PREFIX/bin/$package"
                 "$FIXTURE_CHMOD" 755 "$PREFIX/bin/$package";;
  esac
done
''')
        self.environment["FIXTURE_BASH"] = BASH
        self.environment["FIXTURE_CHMOD"] = CHMOD
        self.stub("bats", 'printf "Bats 1.13.0\\n"\n')

    def stub(self, name, code):
        path = self.bin / name
        path.write_text(f"#!{BASH}\n{code}")
        path.chmod(0o755)
        return path

    def run_script(self, body='main --install', **environment):
        return subprocess.run(
            [BASH, "-c", '''source "$1"
export BATS_VERSION BATS_COMMIT RESVG_VERSION
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
        self.assertEqual(len(calls), 2)
        requested = calls[1].split()[3:]
        self.assertEqual(len(requested), len(set(requested)))
        self.assertTrue(all(call.startswith("pkg ") for call in calls))
        self.assertIn("[OK] pass-cli", result.stdout)
        self.assertIn("[OK] pkg:codex", result.stdout)
        self.assertIn("[SKIP] Homebrew", result.stdout)
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
        self.assertEqual(installed, PACKAGES - {"git", "age", "python"})

    def test_termux_check_is_read_only_and_does_not_execute_pass_cli(self):
        self.stub("pass-cli", 'printf "forbidden:pass-cli\\n" >> "$TRACE"; exit 89\n')
        result = self.run_script('main --check')
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("[OK] pass-cli", result.stdout)
        self.assertIn("[--] pkg:proton-pass-cli", result.stdout)
        self.assertIn("[--] pkg:codex", result.stdout)
        self.assertIn("[SKIP] Homebrew", result.stdout)
        self.assertIn("[OK] bats", result.stdout)
        self.assertEqual(self.trace.read_text(), "")
        self.assertEqual(list(self.home.iterdir()), [])
        self.assertEqual(list(self.state.iterdir()), [])

    def test_bats_install_and_failed_update_preserve_active_version(self):
        (self.bin / "bats").unlink()
        result = self.run_script("main --check")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("[--] bats", result.stdout)
        self.assertEqual(list(self.home.iterdir()), [])
        self.assertEqual(self.trace.read_text(), "")
        for name in ("mktemp", "rm", "ln", "mv"):
            (self.bin / name).symlink_to(shutil.which(name))
        self.stub("termux-fix-shebang", 'printf "shebang\\n" >> "$TRACE"\n')
        self.stub("git", '''
case "$1" in
  clone)
    [[ "$4" == --branch && "$5" == "v$BATS_VERSION" &&
       "$6" == https://github.com/bats-core/bats-core.git ]] || exit 89
    mkdir -p "$7"
    cat > "$7/install.sh" <<'EOF'
mkdir -p "$1/bin" "$1/libexec/bats-core"
printf '#!%s\\nprintf "Bats %%s\\\\n" "%s"\\n' "$FIXTURE_BASH" "$BATS_VERSION" > "$1/bin/bats"
"$FIXTURE_CHMOD" 755 "$1/bin/bats"
printf '#!%s\\n' "$FIXTURE_BASH" > "$1/libexec/bats-core/bats"
EOF
    ;;
  -C) printf '%s\\n' "${BATS_FIXTURE_COMMIT:-$BATS_COMMIT}" ;;
  *) exit 89 ;;
esac
''')
        result = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        entry = self.home / ".local/bin/bats"
        first = entry.resolve(strict=True)
        self.assertEqual(self.trace.read_text().splitlines().count("shebang"), 2)

        self.trace.write_text("")
        result = self.run_script()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.trace.read_text(), "")
        self.assertEqual(entry.resolve(strict=True), first)

        result = self.run_script("main --update-bats", BATS_FIXTURE_COMMIT="unexpected")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("コミットが一致しません", result.stderr)
        self.assertEqual(entry.resolve(strict=True), first)
        self.assertEqual(list(first.parents[1].parent.iterdir()), [first.parents[1]])
        self.assertEqual(list(entry.parent.iterdir()), [entry])

        result = self.run_script("main --update-bats")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotEqual(entry.resolve(strict=True), first)
        self.assertTrue(first.is_file())

    def test_ubuntu_guest_takes_precedence_over_inherited_termux_prefix(self):
        result = self.run_script('check_environment; printf "%s %s\\n" "$IS_TERMUX" "$IS_PROOT"',
                                 FIXTURE_OS="ubuntu", BOOTSTRAP_PROOT="1")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(result.stdout.endswith("false true\n"))

    def test_neovim_tools_install_missing_commands_only_on_termux(self):
        for name in ("bash-language-server", "vtsls", "vue-language-server", "svelteserver",
                     "astro-ls", "tailwindcss-language-server", "emmet-language-server",
                     "vscode-css-language-server", "vscode-html-language-server",
                     "vscode-json-language-server", "yaml-language-server",
                     "prettierd", "prettier", "tsc", "sqls"):
            self.stub(name, "exit 0\n")
        self.stub("npm", '''
[[ "$*" == "install --global --prefix $HOME/.local --no-audit --no-fund basedpyright" ]] || exit 89
printf 'npm basedpyright\\n' >> "$TRACE"
mkdir -p "$HOME/.local/bin"
printf '#!%s\\nexit 0\\n' "$FIXTURE_BASH" > "$HOME/.local/bin/basedpyright-langserver"
"$FIXTURE_CHMOD" 755 "$HOME/.local/bin/basedpyright-langserver"
''')
        self.stub("go", '''
[[ "$*" == "install github.com/nametake/golangci-lint-langserver@v0.0.12" ]] || exit 89
printf 'go golangci-lint-langserver\\n' >> "$TRACE"
printf '#!%s\\nexit 0\\n' "$FIXTURE_BASH" > "$GOBIN/golangci-lint-langserver"
"$FIXTURE_CHMOD" 755 "$GOBIN/golangci-lint-langserver"
''')
        (self.base / "install-termux-nimlsp.sh").write_text("exit 0\n")

        result = self.run_script("main --neovim-tools", FIXTURE_OS="ubuntu")
        self.assertNotEqual(result.returncode, 0)
        self.assertEqual(self.trace.read_text(), "")

        result = self.run_script("main --neovim-tools")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue((self.state / "rust-analyzer").exists())
        self.assertEqual(self.trace.read_text().splitlines()[-2:],
                         ["npm basedpyright", "go golangci-lint-langserver"])

        self.trace.write_text("")
        result = self.run_script("main --neovim-tools")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.trace.read_text(), "")

    def test_resvg_switches_only_after_native_build_and_conversion(self):
        for name in ("mktemp", "rm", "mv"):
            (self.bin / name).symlink_to(shutil.which(name))
        self.stub("rustc", '[[ "$*" == "--print host-tuple" ]] && printf "aarch64-linux-android\\n"\n')
        self.stub("cargo", '''
printf 'cargo\\n' >> "$TRACE"
[[ "$*" == "install --registry crates-io --locked --version $RESVG_VERSION --target aarch64-linux-android --bin resvg --no-track --root "* ]] || exit 89
[[ "${BUILD_EXIT:-0}" == 0 ]] || exit "$BUILD_EXIT"
root="${@: -2:1}"
mkdir -p "$root/bin"
printf '#!%s\\n' "$FIXTURE_BASH" > "$root/bin/resvg"
cat >> "$root/bin/resvg" <<'EOF'
if [[ "$1" == --version ]]; then
  printf '%s\\n' "$RESVG_VERSION"
else
  [[ -s "$1" && "${RENDER_EXIT:-0}" == 0 ]] || exit 1
  printf 'dummy png\\n' > "$2"
fi
EOF
"$FIXTURE_CHMOD" 755 "$root/bin/resvg"
''')
        self.stub("file", '[[ "$1 $2" == "-b --mime-type" && -s "$3" ]] && printf "image/png\\n"\n')
        entry = self.home / ".local/bin/resvg"
        entry.parent.mkdir(parents=True)
        entry.write_text(f'#!{BASH}\nprintf "resvg previous\\n"\n')
        entry.chmod(0o755)
        previous = entry.read_bytes()
        for options in ({"FIXTURE_OS": "ubuntu"}, {"BUILD_EXIT": "1"}, {"RENDER_EXIT": "1"}):
            with self.subTest(options=options):
                result = self.run_script("main --update-resvg", **options)
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(entry.read_bytes(), previous)
                self.assertEqual(list(entry.parent.iterdir()), [entry])
        result = self.run_script("main --update-resvg")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertNotEqual(entry.read_bytes(), previous)
        self.assertEqual(list(entry.parent.iterdir()), [entry])
        self.assertEqual(self.trace.read_text().splitlines(), ["cargo"] * 3)
        result = self.run_script("main --update-resvg")
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self.trace.read_text().splitlines(), ["cargo"] * 3)

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
        for options in ({"INSTALL_EXIT": "22"}, {"OMIT_PACKAGE": "python"},
                        {"OMIT_PACKAGE": "proton-pass-cli"}, {"OMIT_PACKAGE": "codex"}):
            with self.subTest(options=options):
                for path in self.state.iterdir():
                    path.unlink()
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
