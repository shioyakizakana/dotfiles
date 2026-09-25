# ============================================================
# alias
# ============================================================

# ------------------------------------------------------------
# replace
# ------------------------------------------------------------
alias cat='bat --paging=never'
alias rm='gomi'
alias grep='rg'
alias man='tldr'
alias find='fd'

# ------------------------------------------------------------
# ls alias
# ------------------------------------------------------------
alias ls='eza --group-directories-first'
alias ll='eza -alhF --group-directories-first'
alias la='eza -a --group-directories-first'
alias l='eza -lhF --group-directories-first'
alias lt='eza --tree --level=2 --group-directories-first'
alias lta='eza --tree --level=2 -a --group-directories-first'

# ------------------------------------------------------------
# commands
# ------------------------------------------------------------
alias reload='source ~/.zshrc'
alias desk='~/scripts/x11'
alias upd='~/scripts/pack_update.sh'

alias cmcd='cd -- "$(chezmoi source-path)"'

