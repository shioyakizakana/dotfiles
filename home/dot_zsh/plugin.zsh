export PLUGINS_ROOT="$ZDIR/plugin/plugins"

for _dotfiles_plugin in \
  "$PLUGINS_ROOT/powerlevel10k/powerlevel10k.zsh-theme" \
  "$PLUGINS_ROOT/fast-syntax-highlighting/fast-syntax-highlighting.plugin.zsh" \
  "$PLUGINS_ROOT/zsh-autosuggestions/zsh-autosuggestions.plugin.zsh" \
  "$PLUGINS_ROOT/zsh-completions/zsh-completions.plugin.zsh" \
  "$ZDIR/plugin/fzf.zsh" \
  "$ZDIR/plugin/zeno.zsh"; do
  if [[ -r "$_dotfiles_plugin" ]]; then
    source "$_dotfiles_plugin"
  fi
done
unset _dotfiles_plugin
