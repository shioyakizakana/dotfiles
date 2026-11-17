# shellcheck shell=sh
# BashとZshの共通関数。読み込み時にはツールを起動しない。

if ! command -v nvim_snapshot >/dev/null 2>&1; then
  nvim_snapshot() {
    if ! command -v python3 >/dev/null 2>&1; then
      printf '%s\n' 'nvim_snapshot: Python 3.11以上が必要です。' >&2
      return 127
    fi
    if [ ! -r "$HOME/.local/bin/nvim-snapshot.py" ]; then
      printf '%s\n' 'nvim_snapshot: ~/.local/bin/nvim-snapshot.pyを配置してください。' >&2
      return 127
    fi
    command python3 "$HOME/.local/bin/nvim-snapshot.py" "$@"
  }
  _DOTFILES_NVIM_SNAPSHOT_LOADED=1
elif [ "${_DOTFILES_NVIM_SNAPSHOT_LOADED:-}" != 1 ]; then
  printf '%s\n' 'nvim_snapshot: 同名コマンドが存在するため定義を省略しました。' >&2
fi
:
