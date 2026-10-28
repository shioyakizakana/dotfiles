# ============================================================
# path
# ============================================================

# go
export GOPATH=$HOME/go
# pnpm
export PNPM_HOME="$HOME/.local/share/pnpm"
# fzfはプラグインディレクトリにインストール
export FZF_INSTALL=$ZDIR/plugin/plugins/fzf

path+=(
  $HOME/.local/bin(N-/)
  $HOME/bin(N-/)
  /snap/bin(N-/)
  $FZF_INSTALL/bin(N-/)
  $HOME/.cargo/bin(N-/)
  $GOPATH(N-/)
  $GOPATH/bin(N-/)
  $PNPM_HOME/bin(N-/)
)

if type nvim >/dev/null; then
  export EDITOR=nvim
else
  export EDITOR=vim
fi

# 重複排除とパスの順序維持
typeset -U path PATH

# Proton PassのSSHエージェントソックファイル
export SSH_AUTH_SOCK=$HOME/.ssh/proton-pass-agent.sock
