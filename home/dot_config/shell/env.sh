# shellcheck shell=sh
# BashとZshの両方から読み込むため、POSIX構文だけを使う。

export TMPDIR="${TMPDIR:-$HOME/tmp}"
if [ ! -d "$TMPDIR" ]; then
  command mkdir -p -- "$TMPDIR"
fi

export SCRIPTS_DIR="$HOME/scripts"
# 旧構成の手動配置を維持する。管理対象の設定はこのファイルへ集約する。
if [ -r "$SCRIPTS_DIR/shell/funciton.sh" ]; then
  # shellcheck source=/dev/null
  . "$SCRIPTS_DIR/shell/funciton.sh"
fi

export GOPATH="$HOME/go"
export PNPM_HOME="$HOME/.local/share/pnpm"
export FZF_INSTALL="${ZDIR:-$HOME/.zsh}/plugin/plugins/fzf"

for _dotfiles_dir in \
  "$HOME/.local/bin" \
  "$HOME/bin" \
  "/snap/bin" \
  "$FZF_INSTALL/bin" \
  "$HOME/.cargo/bin" \
  "$GOPATH" \
  "$GOPATH/bin" \
  "$PNPM_HOME/bin"; do
  if [ -d "$_dotfiles_dir" ]; then
    case ":${PATH:-}:" in
    *":$_dotfiles_dir:"*) ;;
    *) PATH="${PATH:+$PATH:}$_dotfiles_dir" ;;
    esac
  fi
done
unset _dotfiles_dir
export PATH

if command -v nvim >/dev/null 2>&1; then
  export EDITOR=nvim
else
  export EDITOR=vim
fi

export LANG=ja_JP.UTF-8
export LANGUAGE=ja_JP:ja
