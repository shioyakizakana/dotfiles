# ============================================================
# zsh completion
# ============================================================

# ------------------------------------------------------------
# キャッシュディレクトリ
# ------------------------------------------------------------

ZSH_CACHE_DIR="${XDG_CACHE_HOME:-$HOME/.cache}/zsh"
mkdir -p "$ZSH_CACHE_DIR"


# ------------------------------------------------------------
# 補完関数の検索パス
# compinit より前に設定する
# ------------------------------------------------------------

fpath=(
  "$ZDIR/completions"
  $fpath
)

if [[ -d $BREW_PREFIX/share/zsh/site-functions ]]; then
  fpath=($BREW_PREFIX/share/zsh/site-functions $fpath)
elif [[ -d /usr/share/zsh/site-functions ]]; then
  fpath=(/usr/share/zsh/site-functions $fpath)
fi

# ------------------------------------------------------------
# 補完システム
# ------------------------------------------------------------

autoload -Uz compinit

_zcompdump="${ZSH_CACHE_DIR}/zcompdump"

# zcompdump が24時間以内なら再スキャンを省略
if [[ -f "$_zcompdump" ]] &&
   (( $(date +%s) - $(stat -c %Y "$_zcompdump") < 86400 )); then

  compinit -C -d "$_zcompdump"

else

  compinit -d "$_zcompdump"

  # zcompdump をコンパイル
  if [[ ! -f "${_zcompdump}.zwc" ||
        "$_zcompdump" -nt "${_zcompdump}.zwc" ]]; then
    zcompile "$_zcompdump"
  fi

fi

unset _zcompdump


# ------------------------------------------------------------
# 補完候補
# ------------------------------------------------------------

# Tab連打でメニュー選択
setopt AUTO_MENU

# 単語の途中からでも補完
setopt COMPLETE_IN_WORD

# 補完候補を詰めて表示
setopt LIST_PACKED

# 大文字・小文字を区別しない
# ただし大文字を入力した場合は区別する
zstyle ':completion:*' matcher-list 'm:{a-z}={A-Z}'


# 補完候補をメニュー選択
zstyle ':completion:*:default' menu select=2

# 補完キャッシュ
zstyle ':completion::complete:*' use-cache true


# . や .. などを候補から除外
zstyle ':completion:*' ignore-parents parent pwd ..


# ------------------------------------------------------------
# ファイル・ディレクトリ補完
# ------------------------------------------------------------

# ディレクトリ補完時に末尾へ / を付ける
setopt MARK_DIRS


# ------------------------------------------------------------
# sudo の補完
# ------------------------------------------------------------

zstyle ':completion:*:sudo:*' command-path \
  /usr/local/sbin \
  /usr/local/bin \
  /usr/sbin \
  /usr/bin \
  /sbin \
  /bin


# ------------------------------------------------------------
# 履歴検索
# ------------------------------------------------------------

autoload -Uz history-search-end

zle -N history-beginning-search-backward-end \
    history-search-end

zle -N history-beginning-search-forward-end \
    history-search-end

bindkey '^P' history-beginning-search-backward-end
bindkey '^N' history-beginning-search-forward-end


# ------------------------------------------------------------
# コマンドライン編集
# ------------------------------------------------------------

autoload -Uz edit-command-line
zle -N edit-command-line

# Ctrl-O で現在のコマンドをエディタで編集
bindkey '^O' edit-command-line


# ------------------------------------------------------------
# その他
# ------------------------------------------------------------

# 対話シェルでも # によるコメントを使用可能にする
setopt INTERACTIVE_COMMENTS

# ディレクトリ移動時にシンボリックリンクを追跡
setopt CHASE_LINKS
