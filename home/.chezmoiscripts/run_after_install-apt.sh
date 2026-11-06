#!/usr/bin/env bash

set -euo pipefail

log() {
  printf "\n=== %s\n" "$*"
}

main() {
  local uid confirm
  local -a apt_command=(apt)

  command -v apt >/dev/null 2>&1 || {
    log "aptが見つかりません。Ubuntu用の導入処理を停止します。" >&2
    return 1
  }
  uid="$(id -u)" || return 1
  if [[ "$uid" != 0 ]]; then
    command -v sudo >/dev/null 2>&1 || {
      log "非rootでのAPT実行にはsudoが必要です。" >&2
      return 1
    }
    apt_command=(sudo apt)
  fi

  read -rp "標準パッケージマネージャーによるインストールを開始しますか? [y/N]: " confirm

  if [[ "$confirm" =~ ^[Yy] ]]; then

    # update失敗後にinstallへ進まないよう、各処理の失敗で停止する。
    "${apt_command[@]}" update -y
    "${apt_command[@]}" upgrade -y

    "${apt_command[@]}" install -y \
      autoconf \
      build-essential \
      cmake \
      curl \
      gpg \
      libbz2-dev \
      libcurl4-openssl-dev \
      libreadline-dev \
      libsqlite3-dev \
      libssl-dev \
      libz-dev \
      make \
      tar \
      tree \
      unzip \
      vim \
      wget

    log "インストールが完了しました。"
  else
    log "インストールをスキップしました。"
    exit 0
  fi
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  main "$@"
fi
