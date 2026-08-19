# Syntax highlighting must load after every widget it observes.
plugin="$HOME/.local/share/zsh/plugins/zsh-syntax-highlighting/zsh-syntax-highlighting.zsh"
[[ -r $plugin ]] && source "$plugin"
unset plugin
