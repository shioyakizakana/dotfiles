#!/usr/bin/env bash
set -euo pipefail
umask 077

# Proton Pass CLIの初期構築。chezmoi applyは実行しない。
# 使用方法: LINUX_ENV=proot-ubuntu ./bootstrap/setup-proton-pass.sh [env|keyring]

CLR_RED='' CLR_GREEN='' CLR_YELLOW='' CLR_BOLD='' CLR_NORMAL=''
init_colors() {
  local ncolors
  if [[ -t 2 ]] && command -v tput >/dev/null 2>&1; then
    ncolors="$(tput colors 2>/dev/null || printf '0')"
    if [[ "$ncolors" =~ ^[0-9]+$ ]] && ((ncolors >= 8)); then
      CLR_RED="$(tput setaf 1 || true)"
      CLR_GREEN="$(tput setaf 2 || true)"
      CLR_YELLOW="$(tput setaf 3 || true)"
      CLR_BOLD="$(tput bold || true)"
      CLR_NORMAL="$(tput sgr0 || true)"
    fi
  fi
}
message() {
  local color="$1" marker="$2" fmt="$3"
  shift 3
  printf '%s%s%s ' "$color" "$marker" "$CLR_NORMAL" >&2
  printf "$fmt\n" "$@" >&2
}
info() { message "$CLR_GREEN" '[+]' "$@"; }
warn() { message "$CLR_YELLOW" '[*]' "$@"; }
error() { message "$CLR_RED" '[-]' "$@"; }
log() {
  local fmt="$1"
  shift
  printf '\n%s==>%s ' "$CLR_BOLD" "$CLR_NORMAL" >&2
  printf "$fmt\n" "$@" >&2
}
die() {
  local fmt="$1" status="${2:-1}"
  shift 2 || true
  error "$fmt" "$@"
  exit "$status"
}
has() { command -v "$1" >/dev/null 2>&1; }
require() {
  local cmd
  for cmd in "$@"; do
    has "$cmd" || die '必要なコマンドがありません: %s' 1 "$cmd"
  done
}

confirm_setup() {
  local answer
  [[ $EUID -ne 0 ]] || die 'root権限では実行しないでください'
  [[ -r /dev/tty && -w /dev/tty ]] || die '対話用端末 (/dev/tty) が必要です'
  warn '初期構築を開始しますか？ [y/N]'
  IFS= read -r -n 1 answer </dev/tty || die '確認入力を読み取れませんでした'
  printf '\n' >&2
  [[ "$answer" =~ ^[Yy]$ ]] || {
    info '中止しました'
    exit 0
  }
}

# 自動識別は補助機能。ProotやQEMUを確実に識別するにはLINUX_ENVを指定する。
detect_linux_env() {
  local release virt os_id
  if [[ -n "${LINUX_ENV:-}" ]]; then
    case "$LINUX_ENV" in
    termux | proot-ubuntu | wsl-ubuntu | qemu-ubuntu | native-ubuntu)
      printf '%s\n' "$LINUX_ENV"
      return 0
      ;;
    *)
      error '不正なLINUX_ENV: %s' "$LINUX_ENV"
      return 1
      ;;
    esac
  fi
  if [[ "${PREFIX:-}" == /data/data/com.termux/files/usr ]]; then
    printf 'termux\n'
    return 0
  fi
  release="$(cat /proc/sys/kernel/osrelease 2>/dev/null || true)"
  if [[ -n "${WSL_DISTRO_NAME:-}" || "${release,,}" == *microsoft* ]]; then
    printf 'wsl-ubuntu\n'
    return 0
  fi
  if has systemd-detect-virt; then
    virt="$(systemd-detect-virt 2>/dev/null || true)"
    case "$virt" in
    qemu | kvm)
      # KVMゲストがすべてQEMUとは限らないため、必要ならLINUX_ENVで明示する。
      printf 'qemu-ubuntu\n'
      return 0
      ;;
    none | '') ;;
    *)
      error '自動識別できない仮想環境です (%s)。LINUX_ENVを指定してください' "$virt"
      return 1
      ;;
    esac
  fi
  os_id="$(. /etc/os-release 2>/dev/null && printf '%s' "${ID:-}")" || os_id=''
  if [[ "$os_id" == ubuntu ]]; then
    # Proot等は自動識別できないことがある。初回実行時は明示指定を推奨。
    printf 'native-ubuntu\n'
    return 0
  fi
  error '実行環境を識別できません。LINUX_ENVを指定してください'
  return 1
}

resolve_provider() {
  local linux_env="$1" requested="${2:-}"
  case "$linux_env" in
  termux | proot-ubuntu)
    [[ -z "$requested" || "$requested" == env ]] || {
      error '%sではenvのみを使用します' "$linux_env"
      return 1
    }
    printf 'env\n'
    ;;
  wsl-ubuntu | qemu-ubuntu | native-ubuntu)
    case "$requested" in
    env | keyring) printf '%s\n' "$requested" ;;
    *)
      error '%sではenvまたはkeyringを明示してください' "$linux_env"
      return 1
      ;;
    esac
    ;;
  *)
    error '未対応の実行環境: %s' "$linux_env"
    return 1
    ;;
  esac
}

check_keyring_environment() {
  [[ -n "${DBUS_SESSION_BUS_ADDRESS:-}" ]] || {
    error 'D-Busセッションが見つかりません'
    return 1
  }
  has busctl || {
    error 'busctlが見つかりません'
    return 1
  }
  busctl --user --timeout=5 introspect \
    org.freedesktop.secrets /org/freedesktop/secrets \
    org.freedesktop.Secret.Service >/dev/null 2>&1 || {
    error 'Secret Serviceにアクセスできません'
    return 1
  }
}

initialize_environment() {
  local cli_provider="${1:-}" env_provider="${PROTON_PASS_KEY_PROVIDER:-}"
  (($# <= 1)) || die '引数が多すぎます。使用方法: %s [env|keyring]' 1 "$0"
  if [[ -n "$cli_provider" && -n "$env_provider" && "$cli_provider" != "$env_provider" ]]; then
    die '引数とPROTON_PASS_KEY_PROVIDERが一致しません'
  fi
  repo_root="${CHEZMOI_SOURCE_DIR:-$HOME/.local/share/chezmoi}"
  [[ -f "$repo_root/.chezmoiroot" ]] || die '.chezmoiroot が見つかりません: %s' 1 "$repo_root"
  linux_env="$(detect_linux_env)" || die '実行環境の識別に失敗しました'
  provider="$(resolve_provider "$linux_env" "${cli_provider:-$env_provider}")" ||
    die 'プロバイダーの決定に失敗しました'
  if [[ "$provider" == keyring ]]; then
    check_keyring_environment || die 'Keyringの利用条件を満たしていません'
  fi
  data_dir="${XDG_DATA_HOME:-$HOME/.local/share}/proton-pass"
  identity_dir="${XDG_DATA_HOME:-$HOME/.local/share}/age"
  identity="${AGE_IDENTITY_FILE:-$identity_dir/proton-pass-identity.txt}"
  token_file="$data_dir/token.age"
  encryption_file="$data_dir/encryption-key.age"
  info '実行環境: %s' "$linux_env"
  info 'プロバイダー: %s' "$provider"
}

initialize_age_identity() {
  install -d -m 700 "$data_dir" "$(dirname -- "$identity")"
  if [[ ! -e "$identity" ]]; then
    age-keygen -o "$identity"
    chmod 600 "$identity"
    log 'age identityを生成しました: %s' "$identity"
    warn 'identityをこの環境とは別の安全な場所へバックアップしてください'
  fi
  [[ -s "$identity" && -r "$identity" ]] || die 'age identityを読み取れません: %s' 1 "$identity"
  recipient="$(age-keygen -y "$identity")" || die 'age identityの公開鍵を取得できません'
}

# サブシェルとEXITトラップで、失敗・中断時にも暗号文の一時ファイルを削除する。
# stdinの秘密情報を暗号化し、宛先が存在しない場合のみハードリンクで確定する。
encrypt_once() (
  local dest="$1" tmp
  if [[ -e "$dest" ]]; then
    [[ -s "$dest" ]] || die '既存の暗号化ファイルが空です: %s' 1 "$dest"
    log '既存の暗号化ファイルを利用します: %s' "$dest"
    return 0
  fi
  tmp="$(mktemp "$data_dir/.secret.XXXXXXXX")"
  trap 'command rm -f -- "$tmp"' EXIT
  age -r "$recipient" -o "$tmp" || die '暗号化に失敗しました'
  chmod 600 "$tmp"
  if ln -- "$tmp" "$dest" 2>/dev/null; then
    log '暗号化ファイルを作成しました: %s' "$dest"
  elif [[ ! -s "$dest" ]]; then
    die '暗号化ファイルを保存できません: %s' 1 "$dest"
  else
    log '他の処理が作成した暗号化ファイルを利用します: %s' "$dest"
  fi
)

initialize_secrets() {
  local token
  if [[ ! -e "$token_file" ]]; then
    info 'Proton Pass PATを入力してください（入力は表示されません）:'
    IFS= read -r -s token </dev/tty || die 'PATを読み取れませんでした'
    printf '\n' >&2
    [[ -n "$token" ]] || die 'PATが空です'
    printf '%s' "$token" | encrypt_once "$token_file"
    unset token
  fi
  if [[ "$provider" == env && ! -e "$encryption_file" ]]; then
    openssl rand -hex 32 | encrypt_once "$encryption_file"
  fi
  [[ -s "$token_file" ]] || die 'PATの暗号化ファイルがありません、または空です'
  if [[ "$provider" == env ]]; then
    [[ -s "$encryption_file" ]] || die '暗号化鍵ファイルがありません、または空です'
  fi
}

# 秘密情報を使うコマンドをサブシェルに閉じ込める。
run_authenticated_setup() (
  local token encryption_key
  token="$(age -d -i "$identity" "$token_file")" || die 'PATの復号に失敗しました'
  [[ -n "$token" ]] || die '復号したPATが空です'
  export PROTON_PASS_KEY_PROVIDER="$provider"
  if [[ "$provider" == env ]]; then
    encryption_key="$(age -d -i "$identity" "$encryption_file")" || die '暗号化鍵の復号に失敗しました'
    [[ "$encryption_key" =~ ^[[:xdigit:]]{64}$ ]] || die '暗号化鍵の形式が不正です'
    export PROTON_PASS_ENCRYPTION_KEY="$encryption_key"
  else
    unset PROTON_PASS_ENCRYPTION_KEY
  fi
  log 'PATでログインします (provider=%s)' "$provider"
  PROTON_PASS_PERSONAL_ACCESS_TOKEN="$token" pass-cli login || die 'Proton Passへのログインに失敗しました'
  unset token
  pass-cli info || die 'Proton Passの認証状態を確認できませんでした'
)

# chezmoi側の[data].protonPassProviderを参照し、実行環境と設定の不一致を検出する。
verify_chezmoi_provider() {
  local actual
  actual="$(chezmoi --source "$repo_root" execute-template '{{ .protonPassProvider }}')" ||
    die 'chezmoiのprotonPassProviderを取得できません。テンプレート設定を確認してください'
  [[ "$actual" == env || "$actual" == keyring ]] ||
    die 'chezmoiのprotonPassProviderが不正です: %s' 1 "$actual"
  [[ "$actual" == "$provider" ]] ||
    die 'プロバイダー不一致: Bootstrap=%s、chezmoi=%s' 1 "$provider" "$actual"
  info 'chezmoiのプロバイダー設定との一致を確認しました'
}

print_next_steps() {
  info '差分確認: chezmoi --source %s diff' "$repo_root"
  info '適用:     chezmoi --source %s apply' "$repo_root"
}

main() {
  init_colors
  confirm_setup
  require \
    age \
    age-keygen \
    pass-cli \
    chezmoi \
    openssl \
    mktemp \
    ln \
    chmod \
    install \
    dirname \
    rm

  initialize_environment "$@"
  initialize_age_identity
  initialize_secrets
  run_authenticated_setup
  verify_chezmoi_provider

  print_next_steps
}

main "$@"
