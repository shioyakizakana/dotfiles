_extract() {
  _files \
    -g '*.(tar|tar.bz2|tbz2|tar.gz|tgz|tar.xz|txz|tar.zst|tzst|zip|7z|rar|gz|bz2|xz|zst)'
}

compdef _extract extract
