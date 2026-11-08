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
    [[ -n "${PREFIX:-}" && -x "${PREFIX}/bin/pkg" && -x "${PREFIX}/bin/sh" ]]; then
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
    if [[ "$IS_TERMUX" == true && "$name" == pass-cli ]]; then
      if has_tool "$name"; then
        printf '[UNVERIFIED] pass-cli: 存在のみ確認。Termuxでの実行可否は手動確認\n'
      else
        printf '[MANUAL] pass-cli: Termux向け自動導入は対象外\n'
      fi
    elif has_tool "$name"; then
      printf '[OK] %s\n' "$name"
    else
      printf '[--] %s\n' "$name"
    fi
  done

  if [[ "$IS_TERMUX" == true ]]; then
    printf '[SKIP] Homebrew: Termuxでは対象外\n'
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
    install_termux_packages ca-certificates curl git age chezmoi python make \
      openssl-tool wget util-linux procps file coreutils
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
    warn "TermuxのProton Pass CLIは手動準備・実行確認が必要です。認証準備は未完了です"
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

  if [[ "$IS_TERMUX" != true ]]; then
    mkdir -p "$BIN_DIR"
  fi
  install_base_tools
  install_chezmoi
  install_proton_pass
  install_mise
  install_homebrew

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
