#!/usr/bin/env bash
set -euo pipefail
umask 077

# Proton Pass CLI の初期構築。chezmoi apply は実行しない。
# 使用例: LINUX_ENV=proot-ubuntu ./bootstrap/setup-proton-pass.sh env
# AGE_IDENTITY_FILEはパスフレーズで暗号化済みのage identityを指定する。
# 既存の平文 identity は自動移行しない。

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
  error "$@"
  exit 1
}
has() { command -v "$1" >/dev/null 2>&1; }
require() {
  local cmd
  for cmd in "$@"; do
    has "$cmd" || die '必要なコマンドがありません: %s' "$cmd"
  done
}

confirm_setup() {
  local answer
  [[ $EUID -ne 0 ]] || die 'root権限では実行しないでください'
  [[ -r /dev/tty && -w /dev/tty ]] || die '/dev/tty が必要です'
  warn '初期構築を開始しますか？ [y/N]'
  IFS= read -r -n 1 answer </dev/tty || die '確認入力を読み取れませんでした'
  printf '\n' >&2
  [[ "$answer" =~ ^[Yy]$ ]] || {
    info '中止しました'
    exit 0
  }
}

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
  (($# <= 1)) || die '引数が多すぎます。使用方法: %s [env|keyring]' "$0"
  if [[ -n "$cli_provider" && -n "$env_provider" && "$cli_provider" != "$env_provider" ]]; then
    die '引数とPROTON_PASS_KEY_PROVIDERが一致しません'
  fi

  readonly REPO_ROOT="${CHEZMOI_SOURCE_DIR:-$HOME/.local/share/chezmoi}"
  [[ -f "$REPO_ROOT/.chezmoiroot" ]] || die '.chezmoiroot が見つかりません: %s' "$REPO_ROOT"
  linux_env="$(detect_linux_env)" || die '実行環境の識別に失敗しました'
  provider="$(resolve_provider "$linux_env" "${cli_provider:-$env_provider}")" || die 'プロバイダーの決定に失敗しました'
  if [[ "$provider" == keyring ]]; then
    check_keyring_environment || die 'Keyringの利用条件を満たしていません'
  fi

  readonly DATA_DIR="${XDG_DATA_HOME:-$HOME/.local/share}/proton-pass"
  readonly AGE_IDENTITY_DIR="${AGE_IDENTITY_DIR:-${XDG_DATA_HOME:-$HOME/.local/share}/age}"
  readonly AGE_IDENTITY_FILE="${AGE_IDENTITY_FILE:-$AGE_IDENTITY_DIR/id_proton_pat.age}"
  readonly RECIPIENT_FILE="${AGE_RECIPIENT_FILE:-$AGE_IDENTITY_DIR/proton-pass-recipient.txt}"
  readonly LEGACY_IDENTITY="$AGE_IDENTITY_DIR/proton-pass-identity.txt"
  readonly PAT_FILE="$DATA_DIR/token.age"
  readonly ENCRYPTION_FILE="$DATA_DIR/encryption-key.age"
  # 文字列上での保存先の重複を防ぐ（実体パスの重複は別途注意）。
  [[ "$AGE_IDENTITY_FILE" != "$RECIPIENT_FILE" &&
    "$AGE_IDENTITY_FILE" != "$PAT_FILE" &&
    "$AGE_IDENTITY_FILE" != "$ENCRYPTION_FILE" &&
    "$RECIPIENT_FILE" != "$PAT_FILE" &&
    "$RECIPIENT_FILE" != "$ENCRYPTION_FILE" &&
    "$PAT_FILE" != "$ENCRYPTION_FILE" ]] || die '秘密情報の保存先が重複しています'
  info '実行環境: %s' "$linux_env"
  info 'プロバイダー: %s' "$provider"
}

# bootstrapの同時実行を防ぐ。fd 9 は終了時に閉じられ、ロックが解除される。
acquire_setup_lock() {
  install -d -m 700 "$DATA_DIR"
  local lock_file="$DATA_DIR/.setup-proton-pass.lock"
  [[ ! -L "$lock_file" ]] || die 'ロックファイルにシンボリックリンクは使用できません'
  exec 9>"$lock_file"
  flock -n 9 || die '別のbootstrapが実行中です'
}

# 宛先が未作成の場合のみハードリンクで確定する。既存ファイルは上書きしない。
publish_once() {
  local src="$1" dest="$2"
  if ln -- "$src" "$dest" 2>/dev/null; then
    return 0
  fi
  [[ -s "$dest" && -f "$dest" && ! -L "$dest" ]] || die 'ファイルの確定に失敗しました: %s' "$dest"
  warn '既存のファイルを再利用します: %s' "$dest"
}

# 中断時にも一時ファイルを消去する。ファイル本体には平文identityを保存しない。
create_encrypted_identity() (
  local tmp=''
  trap '[[ -z "$tmp" ]] || command rm -f -- "$tmp"' EXIT
  tmp="$(mktemp "$(dirname -- "$AGE_IDENTITY_FILE")/.identity.XXXXXXXX")" || die 'identity一時ファイルを作成できません'
  age-keygen | age -p >"$tmp" || die 'identityの生成・暗号化に失敗しました'
  [[ -s "$tmp" ]] || die 'identityの暗号文が空です'
  publish_once "$tmp" "$AGE_IDENTITY_FILE"
)

write_recipient_once() (
  local value="$1" tmp=''
  trap '[[ -z "$tmp" ]] || command rm -f -- "$tmp"' EXIT
  tmp="$(mktemp "$(dirname -- "$RECIPIENT_FILE")/.recipient.XXXXXXXX")" || die '公開鍵一時ファイルを作成できません'
  printf '%s\n' "$value" >"$tmp"
  publish_once "$tmp" "$RECIPIENT_FILE"
)

initialize_age_identity() {
  local recovered first_line
  install -d -m 700 "$DATA_DIR" "$(dirname -- "$AGE_IDENTITY_FILE")" "$(dirname -- "$RECIPIENT_FILE")"
  [[ ! -L "$AGE_IDENTITY_FILE" && ! -L "$RECIPIENT_FILE" ]] || die 'identity/recipientにシンボリックリンクは使用できません'

  if [[ -e "$LEGACY_IDENTITY" && "$LEGACY_IDENTITY" != "$AGE_IDENTITY_FILE" && ! -e "$AGE_IDENTITY_FILE" ]]; then
    die '平文の旧identityを検出しました: %s。既存鍵を暗号化してから再実行してください' "$LEGACY_IDENTITY"
  fi
  if [[ ! -e "$AGE_IDENTITY_FILE" ]]; then
    if [[ -e "$RECIPIENT_FILE" || -e "$PAT_FILE" || -e "$ENCRYPTION_FILE" ]]; then
      die '公開鍵または暗号化済み認証情報が存在しますがidentityがありません。新しい鍵は生成しません'
    fi
    log '新しいパスフレーズ付きidentityを生成します'
    warn 'ageの入力画面でパスフレーズを設定し、別の安全な場所にも保存してください'
    create_encrypted_identity
  fi
  [[ -s "$AGE_IDENTITY_FILE" && -f "$AGE_IDENTITY_FILE" && -r "$AGE_IDENTITY_FILE" && ! -L "$AGE_IDENTITY_FILE" ]] || die 'identityを読み取れません: %s' "$AGE_IDENTITY_FILE"
  if [[ -e "$LEGACY_IDENTITY" && "$LEGACY_IDENTITY" != "$AGE_IDENTITY_FILE" ]]; then
    warn '平文の旧identityが残っています。移行確認後に廃止してください: %s' "$LEGACY_IDENTITY"
  fi

  # passphraseで暗号化されたageファイルのヘッダーを検証（armorは対象外）。
  IFS= read -r first_line <"$AGE_IDENTITY_FILE" || die 'identityのヘッダーを読み取れません'
  [[ "$first_line" == 'age-encryption.org/v1' ]] || die 'identityが想定したage暗号化形式ではありません: %s' "$AGE_IDENTITY_FILE"

  # bootstrapでは必ず復号して秘密鍵と公開鍵の一致を検証する。
  log 'identityを復号してrecipientを検証します'
  recovered="$(age -d "$AGE_IDENTITY_FILE" | age-keygen -y)" || die 'identityから公開鍵を取得できません'
  [[ "$recovered" == age1* && "$recovered" != *$'\n'* ]] || die '導出したrecipientの形式が不正です'
  if [[ ! -e "$RECIPIENT_FILE" ]]; then
    write_recipient_once "$recovered"
  fi
  [[ -s "$RECIPIENT_FILE" && -f "$RECIPIENT_FILE" && -r "$RECIPIENT_FILE" && ! -L "$RECIPIENT_FILE" ]] || die 'recipientを読み取れません'
  recipient="$(<"$RECIPIENT_FILE")"
  [[ "$recipient" == "$recovered" ]] || die 'identityとrecipientが一致しません'
  info '暗号化identityとrecipientの一致を確認しました'
}

encrypt_once() (
  local dest="$1" tmp=''
  if [[ -e "$dest" ]]; then
    [[ -s "$dest" && -f "$dest" && ! -L "$dest" ]] || die '既存の暗号化ファイルが不正です: %s' "$dest"
    log '既存の暗号化ファイルを利用します: %s' "$dest"
    return 0
  fi
  trap '[[ -z "$tmp" ]] || command rm -f -- "$tmp"' EXIT
  tmp="$(mktemp "$DATA_DIR/.secret.XXXXXXXX")" || die '一時ファイルを作成できません'
  age -r "$recipient" >"$tmp" || die '暗号化に失敗しました'
  [[ -s "$tmp" ]] || die '暗号化結果が空です'
  chmod 600 "$tmp"
  publish_once "$tmp" "$dest"
  log '暗号化ファイルを準備しました: %s' "$dest"
)

initialize_secrets() {
  local token
  [[ ! -L "$PAT_FILE" && ! -L "$ENCRYPTION_FILE" ]] || die '暗号化ファイルにシンボリックリンクは使用できません'
  if [[ ! -e "$PAT_FILE" ]]; then
    info 'Proton Pass PATを入力してください（入力は表示されません）:'
    IFS= read -r -s token </dev/tty || die 'PATを読み取れませんでした'
    printf '\n' >&2
    [[ -n "$token" ]] || die 'PATが空です'
    printf '%s' "$token" | encrypt_once "$PAT_FILE"
    unset token
  fi
  if [[ "$provider" == env && ! -e "$ENCRYPTION_FILE" ]]; then
    openssl rand -hex 32 | encrypt_once "$ENCRYPTION_FILE"
  fi
  [[ -s "$PAT_FILE" && -f "$PAT_FILE" && ! -L "$PAT_FILE" ]] || die 'PAT暗号化ファイルが不正です'
  if [[ "$provider" == env ]]; then
    [[ -s "$ENCRYPTION_FILE" && -f "$ENCRYPTION_FILE" && ! -L "$ENCRYPTION_FILE" ]] || die 'CLI暗号化鍵ファイルが不正です'
  fi
}

run_authenticated_setup() (
  local token encryption_key
  # bootstrapは復号結果をキャッシュしないため、envではパスフレーズ入力が複数回発生する。
  token="$(age -d -i "$AGE_IDENTITY_FILE" "$PAT_FILE")" || die 'PATの復号に失敗しました'
  [[ -n "$token" ]] || die '復号したPATが空です'
  export PROTON_PASS_KEY_PROVIDER="$provider"
  if [[ "$provider" == env ]]; then
    encryption_key="$(age -d -i "$AGE_IDENTITY_FILE" "$ENCRYPTION_FILE")" || die '暗号化鍵の復号に失敗しました'
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

verify_chezmoi_provider() {
  local actual
  actual="$(chezmoi --source "$REPO_ROOT" execute-template '{{ .protonPassProvider }}')" ||
    die 'chezmoiのprotonPassProviderを取得できません。テンプレート設定を確認してください'
  [[ "$actual" == env || "$actual" == keyring ]] || die 'chezmoiのprotonPassProviderが不正です: %s' "$actual"
  [[ "$actual" == "$provider" ]] || die 'プロバイダー不一致: Bootstrap=%s、chezmoi=%s' "$provider" "$actual"
  info 'chezmoiのプロバイダー設定との一致を確認しました'
}
print_next_steps() {
  info '差分確認: chezmoi --source %s diff' "$REPO_ROOT"
  info '適用:     chezmoi --source %s apply' "$REPO_ROOT"
}
main() {
  init_colors
  confirm_setup
  require age age-keygen pass-cli chezmoi openssl mktemp ln chmod install dirname rm flock cat
  initialize_environment "$@"
  acquire_setup_lock
  initialize_age_identity
  initialize_secrets
  run_authenticated_setup
  verify_chezmoi_provider
  print_next_steps
}
main "$@"
