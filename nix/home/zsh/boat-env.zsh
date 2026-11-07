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
    # omp reads its subscription tokens from these names; Boat injects the same tokens under
    # others. Boat withholds the ChatGPT refresh token, so that one lapses after 10 days,
    # long after a box is gone. A login stored by omp still wins over both.
    [[ -n ${CLAUDE_CODE_OAUTH_TOKEN-} ]] && export ANTHROPIC_OAUTH_TOKEN=${ANTHROPIC_OAUTH_TOKEN:-$CLAUDE_CODE_OAUTH_TOKEN}
    [[ -n ${CHATGPT_ACCESS_TOKEN-} ]] && export OPENAI_CODEX_OAUTH_TOKEN=${OPENAI_CODEX_OAUTH_TOKEN:-$CHATGPT_ACCESS_TOKEN}
fi
