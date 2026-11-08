#!/usr/bin/env bash

set -euo pipefail

log() {
  printf "\n=== %s\n" "$*"
}

main() {
  local uid confirm package status code
  local -a apt_command=(apt)
  local -a packages=(autoconf build-essential cmake curl gpg libbz2-dev
    libcurl4-openssl-dev libreadline-dev libsqlite3-dev libssl-dev zlib1g-dev
    make tar tree unzip vim wget)
  local -a missing=()

  command -v apt >/dev/null 2>&1 || {
    log "aptが見つかりません。Ubuntu用の導入処理を停止します。" >&2
    return 1
  }
  command -v dpkg-query >/dev/null 2>&1 || {
    log "dpkg-queryが見つかりません。導入状況を確認できません。" >&2
    return 1
  }
  for package in "${packages[@]}"; do
    if status="$(dpkg-query -W '-f=${Status}' "$package" 2>/dev/null)"; then
      [[ "$status" == 'install ok installed' ]] || missing+=("$package")
    else
      code=$?
      if ((code != 1)); then
        log "パッケージの確認に失敗しました: $package" >&2
        return "$code"
      fi
      missing+=("$package")
    fi
  done
  if ((${#missing[@]} == 0)); then
    log "APTパッケージは導入済みです。"
    return 0
  fi
  uid="$(id -u)" || return 1
  if [[ "$uid" != 0 ]]; then
    command -v sudo >/dev/null 2>&1 || {
      log "非rootでのAPT実行にはsudoが必要です。" >&2
      return 1
    }
    apt_command=(sudo apt)
  fi

  log "未導入のAPTパッケージ: ${missing[*]}"
  if ! read -rp "不足パッケージを導入しますか? [y/N]: " confirm; then
    log "確認入力を取得できないため中止します。" >&2
    return 1
  fi

  if [[ "$confirm" =~ ^[Yy]$ ]]; then

    # update失敗後にinstallへ進まないよう、各処理の失敗で停止する。
    "${apt_command[@]}" update -y || return "$?"

    "${apt_command[@]}" install -y --no-upgrade "${missing[@]}" || return "$?"

    log "インストールが完了しました。"
  else
    log "導入を中止しました。次回の適用で再試行できます。"
    return 0
  fi
}

if [[ "${BASH_SOURCE[0]}" == "$0" ]]; then
  main "$@"
fi
