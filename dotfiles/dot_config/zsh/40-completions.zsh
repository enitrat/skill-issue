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

# oh-my-zsh already ran compinit against $ZSH_COMPDUMP. Running it a second time
# here does not pick up anything new -- it writes a whole separate dump under a
# different name on every shell start, and re-audits all of fpath to do it. The
# guard is for the half-provisioned case 00-omz allows for: if oh-my-zsh is not
# installed its source was skipped, so nothing has defined compdef yet.
(( $+functions[compdef] )) || {
    autoload -Uz compinit
    # ZSH_COMPDUMP is oh-my-zsh's own variable, so it may well be unset here --
    # spelled out rather than as a ${:+} expansion, which zsh would hand to
    # compinit as the single argument "-d /path" and silently ignore.
    if [[ -n $ZSH_COMPDUMP ]]; then
        compinit -d "$ZSH_COMPDUMP"
    else
        compinit
    fi
}

compdef _scarb scarb
compdef _snforge snforge
compdef _sncast sncast

# Must come after compinit; CARAPACE_BRIDGES keeps the compdef stubs working.
if command -v carapace >/dev/null 2>&1; then
    export CARAPACE_BRIDGES='zsh'
    zstyle ':completion:*' format $'\e[2;37mCompleting %d\e[m'
    source <(carapace _carapace)
fi
