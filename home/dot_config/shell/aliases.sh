# shellcheck shell=sh
# reloadは読み込むシェルの設定ファイルで定義する。

alias cat='bat --paging=never'
alias rm='gomi'
alias grep='rg'
alias man='tldr'
alias find='fd'

alias ls='eza --group-directories-first'
alias ll='eza -alhF --group-directories-first'
alias la='eza -a --group-directories-first'
alias l='eza -lhF --group-directories-first'
alias lt='eza --tree --level=2 --group-directories-first'
alias lta='eza --tree --level=2 -a --group-directories-first'

alias upd='"$HOME/.local/bin/update_apps"'
alias homecd='cd -- "${HOME}"'
alias cmcd='cd -- "$(chezmoi source-path)"'
alias cmlg='cd -- "$(chezmoi source-path)" && nvim +LazyGit'
alias nvlg='nvim +LazyGit'
