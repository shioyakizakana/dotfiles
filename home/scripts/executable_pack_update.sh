#!/usr/bin/env bash

set -euo pipefail

###############################################################################
# Common
###############################################################################

TMP_WORK_DIR=$(mktemp -d)
trap 'rm -rf "$TMP_WORK_DIR"'  EXIT

log() {
    printf "\n==> %s\n" "$*"
}

get_latest_github_release() {
    curl -fsSL "https://api.github.com/repos/$1/releases/latest" |
        sed -n 's/.*"tag_name":[[:space:]]*"v\{0,1\}\([^"]*\)".*/\1/p' |
        head -n1
}

check_update() {
    CURRENT="$1"
    LATEST="$2"

    [ "$CURRENT" != "$LATEST" ]
}

###############################################################################
# apt
###############################################################################
log "Updating apt..."
# 最新のアップデートを確認

sudo apt-get update
# 最新のアップデートを適用
sudo apt-get -y upgrade
# ディストリビューションを最新のものに更新
sudo apt-get -y dist-upgrade
# 使われなくなったパッケージを削除
sudo apt-get -y autoremove
# aptキャッシュを削除
sudo apt-get -y autoclean

###############################################################################
# Desktop launchers
###############################################################################

log "Checking VS Code launcher..."

CODE_DESKTOP="/usr/share/applications/code.desktop"

if [[ -f $CODE_DESKTOP ]]; then
  # VS Codeへのno-sandboxオプション追記（必要なら）
  if grep -q 'Exec=/usr/share/code/code %F' $CODE_DESKTOP; then
    sudo sed -i 's#Exec=/usr/share/code/code %F#Exec=/usr/share/code/code --unity-launch --no-sandbox --disable-gpu %F#' $CODE_DESKTOP
  fi
else
  log "VS Code Desktop not found."
fi
log "Checking Vivaldi launcher..."

VIVALDI_DESKTOP="/usr/share/applications/vivaldi-stable.desktop"

if [[ -f $VIVALDI_DESKTOP ]]; then
  # Vivaldiへのno-sandboxとdisable-gpuオプションの再追記（必要なら）
  if grep -qE '^Exec=/usr/bin/vivaldi-stable( |\t)' $VIVALDI_DESKTOP; then
    sudo sed -i -E '/^Exec=\/usr\/bin\/vivaldi-stable( |\t)/ {
      /--no-sandbox/! s#^Exec=/usr/bin/vivaldi-stable#Exec=/usr/bin/vivaldi-stable --no-sandbox --disable-gpu#
    }' $VIVALDI_DESKTOP
  fi
else
  log "Vivaldi not found."
fi
###############################################################################
# brew
###############################################################################
if command -v brew >/dev/null 2>&1; then
  log "Update brew..."
  # 最新のアップデートを確認
  brew update
  # 最新のアップデートを適用
  brew upgrade -y
  # 使われなくなったパッケージを削除
  brew cleanup
fi
###############################################################################
# mise
###############################################################################
if command -v mise >/dev/null 2>&1; then
    log "=== mise outdated ==="
    mise outdated

    log "Update mise..."
    mise upgrade
fi

###############################################################################
# zsh plugins
###############################################################################
ZSH_PLUGIN_DIR="${HOME}/zsh/plugins"

if [[ -d "${ZSH_PLUGIN_DIR}" ]]; then
    log "=== Zsh plugins ==="

    for plugin_dir in "${ZSH_PLUGIN_DIR}"/*; do
        # ディレクトリ以外を無視
        [[ -d "${plugin_dir}" ]] || continue

        # Gitリポジトリでなければ無視
        [[ -d "${plugin_dir}/.git" ]] || continue

        plugin_name="$(basename "${plugin_dir}")"

        log "--- ${plugin_name} ---"

        if git -C "${plugin_dir}" pull --ff-only; then
            log "${plugin_name}: OK"
        else
            log "${plugin_name}: FAILED"
        fi
    done
else
    log "Zsh plugin directory not found: ${ZSH_PLUGIN_DIR}"
fi


log "All updates completed."
