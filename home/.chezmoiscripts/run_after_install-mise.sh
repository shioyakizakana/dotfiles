#!/usr/bin/env bash
set -euo pipefail

log() {
  printf "\n=== %s\n" "$*"
}

INSTALL_APPROVED=0
INSTALL_CANCELLED=0
confirm_install() {
  local answer
  [[ "$INSTALL_APPROVED" == 1 ]] && return 0
  if ! read -rp "不足している開発ツールを導入しますか? [y/N]: " answer; then
    log "確認入力を取得できないため中止します。" >&2
    return 1
  fi
  if [[ ! "$answer" =~ ^[Yy]$ ]]; then
    log "導入を中止しました。次回の適用で再試行できます。"
    INSTALL_CANCELLED=1
    # 内部では中止を区別し、CLIでは正常な辞退として扱う。
    return 20
  fi
  INSTALL_APPROVED=1
}

# rustupコンポーネントの導入
install_rustup_component() {
  local component="$1"
  local installed name details

  if ! command -v rustup >/dev/null 2>&1; then
    log "rustupが見つかりません。"
    return 1
  fi

  if ! installed=$(rustup component list --installed); then
    log "rustupのコンポーネント一覧取得に失敗しました。"
    return 1
  fi

  # 一覧取得後に比較し、パイプの途中終了を未導入と取り違えない。
  while read -r name details; do
    if [[ "$name" == "$component" || "$name" == "$component"-* ]]; then
      log "${component} はインストール済みです。"
      return 0
    fi
  done <<<"$installed"

  log "${component} をインストールします。"
  confirm_install || return "$?"
  rustup component add "$component"
}

# LuaRocksパッケージを未インストールの場合のみ導入する
install_luarock() {
  local package="$1"
  local lua_version="${2:-5.1}"
  local installed name details

  if ! command -v luarocks >/dev/null 2>&1; then
    log "luarocksが見つかりません。Lua 5.1向けの準備手順はdocs/setup/dependencies.mdを参照してください。"
    return 1
  fi

  if ! installed=$(luarocks --lua-version="$lua_version" list --porcelain); then
    log "LuaRocksのパッケージ一覧取得に失敗しました。"
    return 1
  fi

  while read -r name details; do
    if [[ "$name" == "$package" ]]; then
      log "${package} はインストール済みです。"
      return 0
    fi
  done <<<"$installed"

  log "${package} をインストールします。"
  confirm_install || return "$?"
  luarocks --lua-version="$lua_version" install "$package"
}

install_nimlsp() {
  local installed name details
  command -v nimble >/dev/null 2>&1 || {
    log "nimbleが見つかりません。" >&2
    return 1
  }
  installed="$(nimble list --installed)" || return "$?"
  while read -r name details; do
    [[ "$name" == nimlsp ]] && return 0
  done <<<"$installed"
  confirm_install || return "$?"
  nimble install -y nimlsp
}

main() {
  local missing remaining tool_paths installer
  INSTALL_APPROVED=0
  INSTALL_CANCELLED=0
  export PATH="$HOME/.local/bin:$PATH"
  if [[ ! -f "$HOME/.config/mise/config.toml" ]]; then
    log "管理対象のmise設定がありません。設定を展開してから再実行してください。" >&2
    return 1
  fi
  if ! command -v mise >/dev/null 2>&1; then
    confirm_install || return "$?"
    mkdir -p "$HOME/.local/bin" || return "$?"
    installer="$(curl -fsSL https://mise.run)" || return "$?"
    MISE_INSTALL_PATH="$HOME/.local/bin/mise" bash -c "$installer" || return "$?"
    command -v mise >/dev/null 2>&1 || {
      log "miseの導入後に実行ファイルが見つかりません。" >&2
      return 1
    }
  fi

  # 作業中のプロジェクトに影響されず、ホームのツール設定を確認する。
  missing="$(mise --cd "$HOME" ls --missing --no-header)" || return "$?"
  if [[ -n "$missing" ]]; then
    log "未導入のmiseツール:
$missing"
    confirm_install || return "$?"
    mise --cd "$HOME" install || return "$?"
    remaining="$(mise --cd "$HOME" ls --missing --no-header)" || return "$?"
    if [[ -n "$remaining" ]]; then
      log "未導入のツールが残っています:
$remaining" >&2
      return 1
    fi
  fi

  # env全体には秘密値も含まれ得るため、PATHだけを取得する。
  tool_paths="$(mise --cd "$HOME" env --paths)" || return "$?"
  if [[ -n "$tool_paths" ]]; then
    export PATH="${tool_paths//$'\n'/:}:$PATH"
  fi
  install_rustup_component rust-analyzer || return "$?"
  install_luarock luacheck || return "$?"
  install_luarock vuseted || return "$?"
  install_nimlsp || return "$?"
  log "開発ツールの確認が完了しました。"
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  if main "$@"; then
    exit 0
  else
    status=$?
    [[ "$INSTALL_CANCELLED" == 1 ]] && exit 0
    exit "$status"
  fi
fi
