fpath=(~/.zfunc(N) $fpath)

# Stubs that generate the real completions on first Tab, then re-dispatch to
# themselves. Cheaper than running three generators on every shell start.
for _cmd in scarb snforge sncast; do
    eval "_${_cmd}() {
        ${_cmd} completions zsh >/dev/null 2>&1 || return 0
        eval \"\$(${_cmd} completions zsh)\"
        _${_cmd} \"\$@\"
    }"
done
unset _cmd

autoload -Uz compinit && compinit

compdef _scarb scarb
compdef _snforge snforge
compdef _sncast sncast

# Must come after compinit; CARAPACE_BRIDGES keeps the compdef stubs working.
if command -v carapace >/dev/null 2>&1; then
    export CARAPACE_BRIDGES='zsh'
    zstyle ':completion:*' format $'\e[2;37mCompleting %d\e[m'
    source <(carapace _carapace)
fi
