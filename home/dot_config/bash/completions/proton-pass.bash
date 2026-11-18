# shellcheck shell=bash
_proton_pass_complete() {
  COMPREPLY=()
  local helper="$HOME/.local/bin/proton-pass-key-cache.py" candidate index=1
  [[ -x "$helper" ]] || return 0
  # サブコマンド以降の値を、補完用プロセスの引数へ渡さない。
  while ((index < COMP_CWORD)); do
    case "${COMP_WORDS[index]}" in
    --profile) ((index += 2)) ;;
    --ttl-minutes)
      [[ "${COMP_WORDS[0]##*/}" == proton-pass-key-cache.py ]] || return 0
      ((index += 2))
      ;;
    *) return 0 ;;
    esac
  done
  while IFS= read -r candidate; do
    COMPREPLY+=("$candidate")
  done < <("$helper" complete "${COMP_WORDS[0]##*/}" "${COMP_WORDS[@]:1:COMP_CWORD}" 2>/dev/null)
}
complete -F _proton_pass_complete proton-pass proton-pass-key-cache.py setup-proton-pass-project
