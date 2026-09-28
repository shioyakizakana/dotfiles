function run_vim() {
  LBUFFER="vim"
  zle accept-line
}
zle -N run_vim
