# ============================================================
# zeno.zsh
# ============================================================

# ------------------------------------------------------------
# 基本設定
# ------------------------------------------------------------

export ZENO_HOME="$HOME/.config/zeno"
export ZENO_GIT_CAT="bat --color=always"

export ZENO_ROOT="$HOME/.zsh/plugins/zeno"

# 先にfzfをロードする
_fzf_lazy_load
# ------------------------------------------------------------
# zeno bootstrap
# ------------------------------------------------------------
source "$ZENO_ROOT/zeno-bootstrap.zsh"

# ------------------------------------------------------------
# zenoのlazy widget
# ------------------------------------------------------------
if [[ -n $ZENO_BOOTSTRAPPED ]]; then
  zeno-register-lazy-widgets \
    zeno-auto-snippet \
    zeno-auto-snippet-and-accept-line \
    zeno-completion \
    zeno-insert-snippet \
    zeno-history-selection

# ------------------------------------------------------------
# キーバインド
# ------------------------------------------------------------
  bindkey ' '   zeno-auto-snippet
  bindkey '^m'  zeno-auto-snippet-and-accept-line
  bindkey '^i'  zeno-completion
  bindkey '^xx' zeno-insert-snippet

  bindkey '^x '  zeno-insert-space
  bindkey '^x^m' accept-line
  bindkey '^x^z' zeno-toggle-auto-snippet

  bindkey '^r' zeno-history-selection
fi
