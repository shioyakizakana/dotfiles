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
#
# 使用方法:
#   bash bootstrap-tools.sh --check
#   bash bootstrap-tools.sh --install
#
# 注意:
#   - 既存ツールの更新は行わない
#   - Proton Passのログインは行わない
#   - Homebrewはproot環境では自動導入しない
# ============================================================

readonly SCRIPT_NAME="${0##*/}"
readonly BIN_DIR="${HOME}/.local/bin"

MODE="install"
IS_PROOT=false
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

check_environment() {
  [[ "$(uname -s)" == "Linux" ]] ||
    die "Linux以外には対応していません"

  [[ -r /etc/os-release ]] ||
    die "/etc/os-releaseが見つかりません"

  # shellcheck disable=SC1091
  source /etc/os-release

  [[ "${ID:-}" == "ubuntu" ]] ||
    die "Ubuntu以外には対応していません"

  if [[ -d /proc/1/root/.proot ]] ||
    [[ -n "${PROOT_TMP_DIR:-}" ]] ||
    [[ -n "${PROOT_LOADER:-}" ]]; then
    IS_PROOT=true
  fi

  # prootの環境変数は常に設定されるとは限らないため、
  # proot実行時は明示的な指定も許可する。
  if [[ "${BOOTSTRAP_PROOT:-0}" == "1" ]]; then
    IS_PROOT=true
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
  )

  log "ツールのインストール状況"

  for name in "${tools[@]}"; do
    if has_tool "$name"; then
      printf '[OK] %s\n' "$name"
    else
      printf '[--] %s\n' "$name"
    fi
  done

  if get_brew_path >/dev/null; then
    printf '[OK] Homebrew\n'
  else
    printf '[--] Homebrew\n'
  fi
}

# ------------------------------------------------------------
# APT
# ------------------------------------------------------------

install_base_tools() {
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

  mkdir -p "$BIN_DIR"
  export PATH="${BIN_DIR}:${PATH}"

  if [[ "$MODE" == "check" ]]; then
    check_tools
    return
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

  log "初期ツールのセットアップが完了しました"
  log "次にdotfilesの初期化を行ってください"
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  main "$@"
fi
