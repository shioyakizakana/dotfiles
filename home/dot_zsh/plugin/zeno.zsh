# ============================================================
# zeno.zsh
# ============================================================

# ------------------------------------------------------------
# 基本設定
# ------------------------------------------------------------

command -v deno >/dev/null 2>&1 || return 0
command -v fzf >/dev/null 2>&1 || return 0
[[ -r "$ZDIR/plugin/plugins/zeno/zeno-bootstrap.zsh" ]] || return 0
(( $+functions[_fzf_lazy_load] )) || return 0

export ZENO_HOME="$HOME/.config/zeno"
if command -v bat >/dev/null 2>&1; then
  export ZENO_GIT_CAT="bat --color=always"
else
  export ZENO_GIT_CAT="cat"
fi

export ZENO_ROOT="$ZDIR/plugin/plugins/zeno"

# 先にfzfをロードする
_fzf_lazy_load || return 0
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
