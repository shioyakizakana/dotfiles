#!/usr/bin/env bash
set -Eeuo pipefail

# ============================================================
# bootstrap-tools.sh
#
# dotfilesの初期構築に必要なツールをインストールする。
#
# 対応環境:
#   - Ubuntu (native)
#   - Ubuntu (WSL2)
#   - Ubuntu (Termux + proot)
#   - Termux (APT/dpkg方式)
#
# 使用方法:
#   bash bootstrap-tools.sh --check
#   bash bootstrap-tools.sh --install
#
# 注意:
#   - 一括upgradeは行わない（依存解決による更新はあり得る）
#   - Proton Passのログインは行わない
#   - Homebrewはproot環境では自動導入しない
# ============================================================

readonly SCRIPT_NAME="${0##*/}"
readonly BIN_DIR="${HOME}/.local/bin"

# TermuxではUbuntu用mise設定を除外し、Android向けのパッケージを使う。
readonly TERMUX_PACKAGES=(
  ca-certificates curl git chezmoi make openssl-tool wget util-linux procps file coreutils
  mise proton-pass-cli
  7zip age atuin bat biome2 bun codex deno eza fd ffmpeg gh ghq git-delta git-lfs
  gofumpt goimports golang golangci-lint gopls imagemagick jq lazygit
  lua-language-server lua51 marksman neovim nim nodejs-lts npm oxlint pnpm poppler
  python ripgrep ruby ruff rust shellcheck shfmt sops stylua taplo tealdeer tmux
  tree-sitter ty uv yazi yq zoxide
)

readonly BATS_VERSION="1.13.0"
readonly BATS_COMMIT="3bca150ec86275d6d9d5a4fd7d48ab8b6c6f3d87"
readonly RESVG_VERSION="0.50.0"

MODE="install"
IS_PROOT=false
IS_TERMUX=false
TERMUX_INDEX_UPDATED=0
FAILED=0

# ------------------------------------------------------------
# 共通処理
# ------------------------------------------------------------

log() {
  printf '\n==> %s\n' "$*"
}

warn() {
  printf 'WARN: %s\n' "$*" >&2
}

die() {
  printf 'ERROR: %s\n' "$*" >&2
  exit 1
}

usage() {
  cat <<EOF
Usage: ${SCRIPT_NAME} [OPTION]

Options:
  --check      インストール状況を確認
  --install    不足しているツールを導入（既定）
  --update-bats  TermuxのBatsをリポジトリ指定版に更新
  --update-resvg Termuxのresvgをリポジトリ指定版に導入・更新
  -h, --help   ヘルプを表示
EOF
}

parse_args() {
  while (($# > 0)); do
    case "$1" in
    --check)
      MODE="check"
      ;;
    --install)
      MODE="install"
      ;;
    --update-bats | --update-resvg)
      MODE="${1#--}"
      ;;
    -h | --help)
      usage
      exit 0
      ;;
    *)
      die "不明な引数: $1"
      ;;
    esac
    shift
  done
}

# 一時ファイルの作成・実行・削除
# 第1引数: URL
# 第2引数: インタープリター
# 第3引数以降: スクリプトへ渡す引数
run_installer() {
  local url="$1" interpreter="$2"
  shift 2

  local installer
  installer="$(mktemp)"

  if ! curl -fsSL --retry 3 \
    "$url" -o "$installer"; then
    command rm -f -- "$installer"
    return 1
  fi

  local status=0
  "$interpreter" "$installer" "$@" || status=$?

  command rm -f -- "$installer"
  return "$status"
}

# ------------------------------------------------------------
# 環境判定
# ------------------------------------------------------------

read_os_release() {
  ID='' PRETTY_NAME=''
  [[ -r /etc/os-release ]] || return 0
  # shellcheck disable=SC1091
  source /etc/os-release
}

check_environment() {
  [[ "$(uname -s)" == "Linux" ]] ||
    die "Linux以外には対応していません"

  IS_PROOT=false
  IS_TERMUX=false
  read_os_release
  # prootはTermuxのPREFIXやpkgへのパスを引き継ぐため、ゲストOSを先に確認する。
  if [[ "$ID" == ubuntu ]]; then
    if [[ -d /proc/1/root/.proot || -n "${PROOT_TMP_DIR:-}" ||
      -n "${PROOT_LOADER:-}" || "${BOOTSTRAP_PROOT:-0}" == 1 ]]; then
      IS_PROOT=true
    fi
  elif [[ -z "$ID" || "$ID" == android ]] &&
    [[ "${PREFIX:-}" == /* && -x "${PREFIX}/bin/pkg" && -x "${PREFIX}/bin/sh" ]]; then
    [[ "${BOOTSTRAP_PROOT:-0}" != 1 ]] || die "proot指定時はUbuntuゲスト内で実行してください"
    IS_TERMUX=true
    PRETTY_NAME='Termux'
  else
    die "UbuntuまたはTermux以外には対応していません"
  fi

  log "OS: ${PRETTY_NAME:-Ubuntu}"
  log "Architecture: $(uname -m)"
  log "proot: ${IS_PROOT}"
}

# ------------------------------------------------------------
# インストール済み判定
# ------------------------------------------------------------

has_tool() {
  local name="$1"

  if command -v "$name" >/dev/null 2>&1; then
    return 0
  fi

  [[ -x "${BIN_DIR}/${name}" ]]
}

get_brew_path() {
  if command -v brew >/dev/null 2>&1; then
    command -v brew
  elif [[ -x /home/linuxbrew/.linuxbrew/bin/brew ]]; then
    printf '%s\n' \
      /home/linuxbrew/.linuxbrew/bin/brew
  elif [[ -x "${HOME}/.linuxbrew/bin/brew" ]]; then
    printf '%s\n' \
      "${HOME}/.linuxbrew/bin/brew"
  else
    return 1
  fi
}

check_tools() {
  local name
  local -a tools=(
    curl
    git
    age
    chezmoi
    pass-cli
    mise
    age-keygen
    make
    openssl
    wget
    flock
    python3
  )

  log "ツールのインストール状況"

  for name in "${tools[@]}"; do
    if has_tool "$name"; then
      printf '[OK] %s\n' "$name"
    else
      printf '[--] %s\n' "$name"
    fi
  done

  if [[ "$IS_TERMUX" == true ]]; then
    printf '[SKIP] Homebrew: Termuxでは対象外\n'
    if has_tool bats; then
      printf '[OK] bats\n'
    else
      printf '[--] bats\n'
    fi
    log "Termuxのpkg管理対象（バージョン・実行可否は別途確認）"
    for name in "${TERMUX_PACKAGES[@]}"; do
      if termux_package_installed "$name"; then
        printf '[OK] pkg:%s\n' "$name"
      else
        printf '[--] pkg:%s\n' "$name"
      fi
    done
  elif get_brew_path >/dev/null; then
    printf '[OK] Homebrew\n'
  else
    printf '[--] Homebrew\n'
  fi

  log "設定で使う追加ツール（自動導入対象には追加しません）"
  for name in zsh fzf luarocks deno node npm; do
    if has_tool "$name"; then
      printf '[OK] %s\n' "$name"
    else
      printf '[--] %s\n' "$name"
    fi
  done
  printf '準備方法: docs/setup/dependencies.md\n'
  printf '存在確認のみです。Python 3.11以上、Lua 5.1向けLuaRocks、各ツールの互換性は別途確認してください。\n'
}

# ------------------------------------------------------------
# Termuxパッケージ
# ------------------------------------------------------------

termux_package_installed() {
  [[ "$("${PREFIX}/bin/dpkg-query" -W -f="\${Status}" "$1" 2>/dev/null)" == 'install ok installed' ]]
}

install_termux_packages() {
  local package_manager="${TERMUX_APP_PACKAGE_MANAGER:-${TERMUX_MAIN_PACKAGE_FORMAT:-apt}}"
  # 古いTermuxはパッケージ形式名を公開する。pkgと同じ対応関係で判定する。
  if [[ "$package_manager" == debian && -z "${TERMUX_APP_PACKAGE_MANAGER:-}" ]]; then
    package_manager=apt
  fi
  [[ "$package_manager" == apt && -x "${PREFIX}/bin/dpkg-query" ]] ||
    die "現在はAPT/dpkg方式のTermuxに対応しています"
  [[ "$(id -u)" != 0 ]] || die "Termuxのpkgは通常ユーザーで実行してください"
  local package
  local -a missing=()
  for package in "$@"; do
    if ! termux_package_installed "$package"; then
      missing+=("$package")
    fi
  done
  if ((${#missing[@]} == 0)); then
    log "Termuxパッケージは導入済みです"
    return
  fi
  # Linux向け公式インストーラーにはフォールバックしない。
  if [[ "$TERMUX_INDEX_UPDATED" != 1 ]]; then
    "${PREFIX}/bin/pkg" update -y || die "Termuxのパッケージ一覧更新に失敗しました"
    TERMUX_INDEX_UPDATED=1
  fi
  "${PREFIX}/bin/pkg" install -y "${missing[@]}" || die "Termuxパッケージの導入に失敗しました"
  for package in "${missing[@]}"; do
    termux_package_installed "$package" || die "Termuxパッケージを確認できません: $package"
  done
}

# ------------------------------------------------------------
# 基礎パッケージ
# ------------------------------------------------------------

install_base_tools() {
  if [[ "$IS_TERMUX" == true ]]; then
    install_termux_packages "${TERMUX_PACKAGES[@]}"
    return
  fi
  local -a packages=(
    ca-certificates
    curl
    git
    age
    build-essential
    procps
    file
  )

  local -a apt_cmd=(apt-get)

  if ((EUID != 0)); then
    command -v sudo >/dev/null 2>&1 ||
      die "APTの実行にはsudoが必要です"
    apt_cmd=(sudo apt-get)
  fi

  log "APTパッケージを確認・インストールします"

  "${apt_cmd[@]}" update
  "${apt_cmd[@]}" install -y "${packages[@]}"
}

# ------------------------------------------------------------
# chezmoi
# ------------------------------------------------------------

install_chezmoi() {
  if [[ "$IS_TERMUX" == true ]]; then
    has_tool chezmoi || die "Termuxのchezmoiが見つかりません"
    return
  fi
  if has_tool chezmoi; then
    log "chezmoi: インストール済み"
    return
  fi

  log "chezmoiをインストールします"

  run_installer \
    "https://get.chezmoi.io" \
    sh -b "$BIN_DIR" ||
    die "chezmoiのインストールに失敗しました"

  has_tool chezmoi ||
    die "chezmoiの実行ファイルが見つかりません"
}

# ------------------------------------------------------------
# Proton Pass CLI
# ------------------------------------------------------------

install_proton_pass() {
  if [[ "$IS_TERMUX" == true ]]; then
    has_tool pass-cli || die "Termuxのpass-cliが見つかりません"
    return
  fi
  if has_tool pass-cli; then
    log "Proton Pass CLI: インストール済み"
    return
  fi

  log "Proton Pass CLIをインストールします"

  # 公式インストーラーの既定動作を使用する。
  # 配置先はインストーラーの仕様に従う。
  run_installer \
    "https://proton.me/download/pass-cli/install.sh" \
    bash ||
    die "Proton Pass CLIのインストールに失敗しました"

  if ! has_tool pass-cli; then
    warn "pass-cliがPATH上で確認できません"
    warn "インストール先を確認してください"
    FAILED=1
  fi
}

# ------------------------------------------------------------
# mise
# ------------------------------------------------------------

install_mise() {
  if [[ "$IS_TERMUX" == true ]]; then
    install_termux_packages mise
    has_tool mise || die "Termuxのmiseが見つかりません"
    return
  fi
  if has_tool mise; then
    log "mise: インストール済み"
    return
  fi

  log "miseをインストールします"

  # mise公式インストーラー
  # MISE_INSTALL_PATHでインストール先を指定する。
  MISE_INSTALL_PATH="${BIN_DIR}/mise" \
    run_installer \
    "https://mise.run" \
    sh ||
    die "miseのインストールに失敗しました"

  has_tool mise ||
    die "miseの実行ファイルが見つかりません"
}

# ------------------------------------------------------------
# Homebrew
# ------------------------------------------------------------

install_homebrew() {
  if [[ "$IS_TERMUX" == true ]]; then
    log "TermuxではHomebrewを対象外とします"
    return
  fi
  if get_brew_path >/dev/null; then
    log "Homebrew: インストール済み"
    return
  fi

  if [[ "$IS_PROOT" == true ]]; then
    warn "proot環境ではHomebrewの導入をスキップします"
    return
  fi

  if ((EUID == 0)); then
    warn "Homebrewはrootでインストールできません"
    FAILED=1
    return
  fi

  if ! command -v sudo >/dev/null 2>&1; then
    warn "Homebrew導入に必要なsudoがありません"
    FAILED=1
    return
  fi

  log "Homebrewをインストールします"

  # 公式インストーラーを非対話モードで実行する。
  # Linuxbrewの標準配置先を使用する。
  NONINTERACTIVE=1 \
    run_installer \
    "https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh" \
    bash ||
    die "Homebrewのインストールに失敗しました"

  local brew_path
  if brew_path="$(get_brew_path)"; then
    log "Homebrew: ${brew_path}"

    # 現在のプロセスにも反映
    eval "$("$brew_path" shellenv)"
  else
    warn "Homebrewの実行ファイルが見つかりません"
    FAILED=1
  fi
}

# ------------------------------------------------------------
# TermuxのBats
# ------------------------------------------------------------

install_termux_bats() (
  if [[ "$MODE" != "update-bats" ]] && has_tool bats; then
    return
  fi

  [[ "$(id -u)" != 0 ]] || die "Batsは通常ユーザーで導入してください"
  local tool active
  active="$(command -v bats || true)"
  [[ -z "$active" || "$active" == "$BIN_DIR/bats" ]] ||
    die "別の場所に導入されたBatsは、その導入元で更新してください"
  for tool in git termux-fix-shebang; do
    command -v "$tool" >/dev/null || die "Batsの導入に必要なコマンドがありません: $tool"
  done

  local releases="$HOME/.local/share/bats-core" work='' release='' entry
  trap 'if [[ -n "$work" ]]; then command rm -rf -- "$work"; fi
        if [[ -n "$release" && ! "$BIN_DIR/bats" -ef "$release/bin/bats" ]]; then
          command rm -rf -- "$release"
        fi' EXIT
  mkdir -p -- "$BIN_DIR" "$releases" || die "Batsの導入先を作成できません"
  work="$(mktemp -d "$BIN_DIR/.bats-XXXXXXXX")" || die "Batsの作業領域を作成できません"
  release="$(mktemp -d "$releases/$BATS_VERSION-XXXXXXXX")" || die "Batsの版別領域を作成できません"
  log "Bats $BATS_VERSION を準備"
  git clone --depth 1 --branch "v$BATS_VERSION" \
    https://github.com/bats-core/bats-core.git "$work/source" || die "Batsの取得に失敗しました"
  [[ "$(git -C "$work/source" rev-parse HEAD)" == "$BATS_COMMIT" ]] ||
    die "Batsのリリースコミットが一致しません"
  "$BASH" "$work/source/install.sh" "$release" || die "Batsのインストールに失敗しました"
  for entry in "$release/bin/bats" "$release/libexec/bats-core/"*; do
    termux-fix-shebang "$entry" || die "Batsのシバン補正に失敗しました"
  done
  [[ "$(TMPDIR="$PREFIX/tmp" "$release/bin/bats" --version)" == "Bats $BATS_VERSION" ]] ||
    die "導入したBatsの起動または版を確認できません"
  ln -s -- "$release/bin/bats" "$work/bats" || die "Batsのリンクを作成できません"
  if [[ "$MODE" == "update-bats" ]]; then
    mv -fT -- "$work/bats" "$BIN_DIR/bats" || die "Batsの切り替えに失敗しました"
  else
    mv -nT -- "$work/bats" "$BIN_DIR/bats" || die "Batsを配置できません"
    [[ ! -L "$work/bats" ]] || die "既存のBatsが見つかったため導入を中止しました"
  fi
  release=''
)

# ------------------------------------------------------------
# Termuxのresvg
# ------------------------------------------------------------

install_termux_resvg() (
  [[ "$(id -u)" != 0 ]] || die "resvgは通常ユーザーで導入してください"
  local active target work
  active="$(command -v resvg || true)"
  [[ -z "$active" || "$active" == "$BIN_DIR/resvg" ]] ||
    die "別の場所に導入されたresvgは、その導入元で更新してください"
  if [[ -n "$active" && "$("$active" --version)" == "$RESVG_VERSION" ]]; then
    log "resvg $RESVG_VERSION は導入済みです"
    return
  fi

  [[ -x "$PREFIX/bin/cargo" && -x "$PREFIX/bin/rustc" ]] ||
    die "Termuxのcargoとrustcが必要です"
  target="$("$PREFIX/bin/rustc" --print host-tuple)" || die "Rustの対象環境を確認できません"
  [[ "$target" == *-linux-android || "$target" == *-linux-androideabi ]] ||
    die "Termux本体向けのRustが必要です"
  mkdir -p -- "$BIN_DIR" || die "resvgの導入先を作成できません"
  work="$(mktemp -d "$BIN_DIR/.resvg-XXXXXXXX")" || die "resvgの作業領域を作成できません"
  trap 'command rm -rf -- "$work"' EXIT
  log "resvg $RESVG_VERSION を準備"
  RUSTC="$PREFIX/bin/rustc" TMPDIR="$PREFIX/tmp" "$PREFIX/bin/cargo" install \
    --registry crates-io --locked --version "$RESVG_VERSION" --target "$target" \
    --bin resvg --no-track --root "$work" resvg || die "resvgのビルドに失敗しました"
  [[ "$("$work/bin/resvg" --version)" == "$RESVG_VERSION" ]] ||
    die "ビルドしたresvgの版を確認できません"
  printf '%s\n' '<svg xmlns="http://www.w3.org/2000/svg" width="2" height="2"><rect width="2" height="2" fill="black"/></svg>' >"$work/test.svg" ||
    die "resvgの確認用SVGを作成できません"
  "$work/bin/resvg" "$work/test.svg" "$work/test.png" &&
    [[ "$(file -b --mime-type "$work/test.png")" == image/png ]] ||
    die "resvgのSVG変換を確認できません"
  mv -fT -- "$work/bin/resvg" "$BIN_DIR/resvg" || die "resvgの切り替えに失敗しました"
)

# ------------------------------------------------------------
# メイン処理
# ------------------------------------------------------------

main() {
  parse_args "$@"
  check_environment

  if [[ "$IS_TERMUX" == true ]]; then
    export PATH="${PREFIX}/bin:${BIN_DIR}:${PATH}"
  else
    export PATH="${BIN_DIR}:${PATH}"
  fi

  if [[ "$MODE" == "check" ]]; then
    check_tools
    return
  fi
  if [[ "$MODE" == "update-bats" ]]; then
    [[ "$IS_TERMUX" == true ]] || die "--update-batsはTermux本体専用です"
    install_termux_bats
    return
  fi
  if [[ "$MODE" == "update-resvg" ]]; then
    [[ "$IS_TERMUX" == true ]] || die "--update-resvgはTermux本体専用です"
    install_termux_resvg
    return
  fi

  if [[ "$IS_TERMUX" != true ]]; then
    mkdir -p "$BIN_DIR"
  fi
  install_base_tools
  install_chezmoi
  install_proton_pass
  install_mise
  install_homebrew
  if [[ "$IS_TERMUX" == true ]]; then
    install_termux_bats
  fi

  check_tools

  if ((FAILED != 0)); then
    die "一部のツールを確認できませんでした"
  fi

  log "基礎ツールの導入が完了しました（認証・dotfiles適用は含みません）"
  log "次にdotfilesの初期化を行ってください"
}

if [[ "${BASH_SOURCE[0]:-$0}" == "$0" ]]; then
  main "$@"
fi
