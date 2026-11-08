# shellcheck shell=sh
# reloadは読み込むシェルの設定ファイルで定義する。

command -v bat >/dev/null 2>&1 && alias cat='bat --paging=never'
command -v gomi >/dev/null 2>&1 && alias rm='gomi'
command -v rg >/dev/null 2>&1 && alias grep='rg'
command -v tldr >/dev/null 2>&1 && alias man='tldr'
command -v fd >/dev/null 2>&1 && alias find='fd'

if command -v eza >/dev/null 2>&1; then
  alias ls='eza --group-directories-first'
  alias ll='eza -alhF --group-directories-first'
  alias la='eza -a --group-directories-first'
  alias l='eza -lhF --group-directories-first'
  alias lt='eza --tree --level=2 --group-directories-first'
  alias lta='eza --tree --level=2 -a --group-directories-first'
fi

alias upd='"$HOME/.local/bin/update_apps"'
alias homecd='cd -- "${HOME}"'
if command -v chezmoi >/dev/null 2>&1; then
  alias cmcd='cd -- "$(chezmoi source-path)"'
  if command -v nvim >/dev/null 2>&1; then
    alias cmlg='cd -- "$(chezmoi source-path)" && nvim +LazyGit'
  fi
fi
command -v nvim >/dev/null 2>&1 && alias nvlg='nvim +LazyGit'
# 任意依存の欠落を起動設定の失敗として扱わない。
:
