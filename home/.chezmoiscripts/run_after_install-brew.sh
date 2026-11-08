#!/usr/bin/env bash

set -euo pipefail

log() {
  printf "\n=== %s\n" "$*"
}

get_brew_path() {
  if command -v brew >/dev/null 2>&1; then
    command -v brew
  elif [[ -x /home/linuxbrew/.linuxbrew/bin/brew ]]; then
    printf '%s\n' /home/linuxbrew/.linuxbrew/bin/brew
  elif [[ -x "$HOME/.linuxbrew/bin/brew" ]]; then
    printf '%s\n' "$HOME/.linuxbrew/bin/brew"
  else
    return 1
  fi
}

main() {
  local brew_path confirm installer uid status check_output
  if [[ ! -f "$HOME/.Brewfile" ]]; then
    log "Brewfileがないため対象外です。"
    return 0
  fi
  export HOMEBREW_NO_AUTO_UPDATE=1 HOMEBREW_NO_INSTALL_CLEANUP=1
  unset HOMEBREW_BUNDLE_INSTALL_CLEANUP HOMEBREW_BUNDLE_FORCE_INSTALL_CLEANUP
  if ! brew_path="$(get_brew_path)"; then
    uid="$(id -u)" || return 1
    if [[ "$uid" == 0 ]]; then
      log "rootではHomebrewの新規導入をスキップします。"
      return 0
    fi

    if ! read -rp "Homebrewを導入しますか？ [y/N]: " confirm; then
      log "確認入力を取得できないため中止します。" >&2
      return 1
    fi

    if [[ "$confirm" =~ ^[Yy]$ ]]; then
      log "Homebrewをインストールしています..."
      if ! installer="$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"; then
        log "Homebrewインストーラーの取得に失敗しました。" >&2
        return 1
      fi
      if ! /bin/bash -c "$installer"; then
        log "Homebrewのインストールに失敗しました。" >&2
        return 1
      fi
      if ! brew_path="$(get_brew_path)"; then
        log "Homebrewの実行ファイルが見つかりません。配置先とPATHを確認してください。" >&2
        return 1
      fi
    else
      log "導入を中止しました。次回の適用で再試行できます。"
      return 0
    fi
  fi

  if [[ -f "$HOME/.Brewfile" ]]; then

    # 構文エラーを「不足あり」と取り違えず、導入確認より前に停止する。
    "$brew_path" bundle list --file "$HOME/.Brewfile" >/dev/null || return "$?"
    if check_output="$("$brew_path" bundle check --no-upgrade --file "$HOME/.Brewfile" 2>&1)"; then
      log "Brewfileの依存は導入済みです。"
      return 0
    else
      status=$?
      if ((status != 1)); then
        log "$check_output" >&2
        return "$status"
      fi
    fi
    log "$check_output"

    if ! read -rp "不足している依存を導入しますか? [y/N]: " confirm; then
      log "確認入力を取得できないため中止します。" >&2
      return 1
    fi
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
      "$brew_path" bundle install --no-upgrade --file "$HOME/.Brewfile" || return "$?"
      log "インストールが完了しました。"
    else
      log "導入を中止しました。次回の適用で再試行できます。"
      return 0
    fi
  else
    log "$HOME/.Brewfileがありません。\nインストールをスキップしました。"
    exit 0
  fi
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  main "$@"
fi
