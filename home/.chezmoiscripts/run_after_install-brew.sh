#!/usr/bin/env bash

set -euo pipefail

log() {
  printf "\n=== %s\n" "$*"
}

if ! command -v >/dev/null 2>&1; then

  read -rp "Homebrewがインストールされていません。インストールしますか？ [y/N]" confirm

  if [[ "$confirm" =~ ^[Yy]$ ]]; then
    log "Homebrewをインストールしています..."
    /bin/bash -c \
    "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  else
    log "Homebrewのインストールをスキップしました。"
    exit 0
  fi
fi

if [[ -f "$HOME/.Brewfile" ]]; then

  log ".Brewfileからパッケージをインストールします： $HOME/.Brewfile"
  brew bundle list --global

  read -rp "インストールを開始しますか? [y/N]: " confirm
  if [[ "$confirm" =~ ^[Yy]$ ]]; then
    brew bundle
    brew bundle cleanup
    log "インストールが完了しました。"
  else
    log "インストールをスキップしました。"
    exit 0
  fi
else
  log "$HOME/.Brewfileがありません。\nインストールをスキップしました。"
  exit 0
fi

