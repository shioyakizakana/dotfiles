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
  local brew_path confirm installer uid
  if ! brew_path="$(get_brew_path)"; then
    uid="$(id -u)" || return 1
    if [[ "$uid" == 0 ]]; then
      log "rootではHomebrewの新規導入をスキップします。"
      return 0
    fi

    read -rp "Homebrewがインストールされていません。インストールしますか？ [y/N]" confirm

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
      log "Homebrewのインストールをスキップしました。"
      exit 0
    fi
  fi

  if [[ -f "$HOME/.Brewfile" ]]; then

    log ".Brewfileからパッケージをインストールします： $HOME/.Brewfile"
    "$brew_path" bundle list --global

    read -rp "インストールを開始しますか? [y/N]: " confirm
    if [[ "$confirm" =~ ^[Yy]$ ]]; then
      "$brew_path" bundle --file "$HOME/.Brewfile"
      "$brew_path" bundle cleanup --file "$HOME/.Brewfile"
      log "インストールが完了しました。"
    else
      log "インストールをスキップしました。"
      exit 0
    fi
  else
    log "$HOME/.Brewfileがありません。\nインストールをスキップしました。"
    exit 0
  fi
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  main "$@"
fi
