# chezmoi のテンプレートを評価する。
# Usage: ctmpl <template-file> [execute-template-options...]

ctmpl() {
  if (($# == 0)); then
    print -u2 'Usage: ctmpl <template-file> [execute-template-options...]'
    return 2
  fi

  local template="$1"
  shift

  # カレントディレクトリにファイルがない場合は、
  # chezmoi のソースディレクトリから探す。
  if [[ ! -f "$template" ]]; then
    local source_dir
    source_dir="$(chezmoi source-path)" || return
    template="${source_dir}/${template}"
  fi

  if [[ ! -f "$template" ]]; then
    print -u2 "ctmpl: template not found: $template"
    return 1
  fi

  chezmoi execute-template "$@" <"$template"
}
