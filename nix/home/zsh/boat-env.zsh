# Boat injects its sandbox environment through blocks in ~/.bashrc, which zsh never
# reads: the box's own `boat` on PATH, the loader for Boat environment variables and
# secrets, and ASCII_TOKEN, which lets `boat host`, `boat extend` or `boat fork self`
# act on this sandbox. Evaluate those blocks as Boat wrote them. Not on Boat: no-op.
if [[ -r ~/.bashrc ]] && grep -q '^# ASCII TOKEN START' ~/.bashrc; then
    eval "$(sed -n \
        -e '/^# ASCII CLI PATH START/,/^# ASCII CLI PATH END/p' \
        -e '/^# ASCII SECRET ENV LOADER START/,/^# ASCII SECRET ENV LOADER END/p' \
        -e '/^# ASCII TOKEN START/,/^# ASCII TOKEN END/p' \
        ~/.bashrc)"
fi
