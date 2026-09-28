# ============================================================
# fzf
# ============================================================

# ------------------------------------------------------------
# 基本設定
# ------------------------------------------------------------

export FZF_DEFAULT_OPTS='
--multi
--height=60%
--select-1
--exit-0
--reverse
--bind=ctrl-d:preview-half-page-down,ctrl-u:preview-half-page-up
'

# ------------------------------------------------------------
# Ctrl-T: ファイル検索
# ------------------------------------------------------------

if type fd > /dev/null; then
  export FZF_CTRL_T_COMMAND='
    fd --type f \
      --hidden \
      --exclude .git
  '
else
  export FZF_CTRL_T_COMMAND='
    find . -type f \
      -not -path "*/.git/*"
  '
fi

# ------------------------------------------------------------
# Ctrl-T: preview
# ------------------------------------------------------------

export FZF_CTRL_T_OPTS='
--preview="
  if type bat > /dev/null; then
    bat --color=always --line-range :200 {}
  else
    head -200 {}
  fi
"
--preview-window="down,60%,wrap,+3/2,~3"
'

# ------------------------------------------------------------
# fzf completion
# ------------------------------------------------------------

export FZF_COMPLETION_TRIGGER='**'

# tmux
export FZF_TMUX=1
export FZF_TMUX_OPTS='-p 80%'

# ------------------------------------------------------------
# zeno.zshとの役割分担
# ------------------------------------------------------------

# Ctrl-Rはzenoに任せる
export FZF_CTRL_R_COMMAND=''

# Alt-Cはzshとzeno側に任せる
export FZF_ALT_C_COMMAND=''

# ------------------------------------------------------------
# lazy load
# ------------------------------------------------------------
function _fzf_lazy_load() {
  [[ -n $_FZF_LAZY_LOADED ]] && return

  _FZF_LAZY_LOADED=1
  # キーバインドと候補を有効化
  source "$HOME/.zsh/plugins/fzf/shell/key-bindings.zsh"
  source "$HOME/.zsh/plugins/fzf/shell/completion.zsh"

  # zeno completionとの循環を防ぐ
  fzf_default_completion='expand-or-complete'
}

function _fzf_stub_file() {
  _fzf_lazy_load
  zle fzf-file-widget
}

zle -N _fzf_stub_file

bindkey '^T' _fzf_stub_file
