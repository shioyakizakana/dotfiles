# ============================================================
# path
# ============================================================

# fzfはプラグインディレクトリにインストール
export FZF_INSTALL=$ZDIR/plugin/plugins/fzf
path+=(
  $HOME/.local/bin(N-/)
  $HOME/bin(N-/)
  /snap/bin(N-/)
  $FZF_INSTALL/bin(N-/)
  $HOME/.cargo/bin(N-/)
)

if type nvim > /dev/null; then
  export EDITOR=nvim
else
  export EDITOR=vim
fi

# 重複排除とパスの順序維持
typeset -U path PATH
