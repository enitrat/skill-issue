# Starknet tools generate their completions on first Tab, then re-dispatch to
# themselves. Cheaper than running three generators on every shell start, and
# harmless where the tools are not installed.
for _cmd in scarb snforge sncast; do
    eval "_${_cmd}() {
        ${_cmd} completions zsh >/dev/null 2>&1 || return 0
        eval \"\$(${_cmd} completions zsh)\"
        _${_cmd} \"\$@\"
    }"
    compdef "_${_cmd}" "$_cmd"
done
unset _cmd
