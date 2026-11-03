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
    # Boat's loader drops CLAUDE_CODE_OAUTH_TOKEN whenever ~/.claude/.credentials.json
    # is non-empty, taking that as a Claude login. Claude Code also keeps MCP OAuth
    # logins (Figma) in that file, so one MCP login left new shells with no Claude
    # login at all. Keep Boat's token unless the file holds a real Claude login.
    creds=${CLAUDE_CONFIG_DIR:-$HOME/.claude}/.credentials.json
    if [[ -z ${CLAUDE_CODE_OAUTH_TOKEN-} && -r /run/ascii-secrets/env.sh ]] \
        && ! grep -qs '"claudeAiOauth"' "$creds"; then
        . /run/ascii-secrets/env.sh
    fi
    unset creds
fi
