log() { printf '[%s] %s\n' "$1" "$2"; }
warn() { printf '[%s] %s\n' "$1" "$2" >&2; }
have() { command -v "$1" >/dev/null 2>&1; }

# Chezmoi scripts do not inherit PATH changes made by earlier scripts.
mise_path() {
    brew_path || true
    export PATH="$HOME/.local/bin:$HOME/.local/share/mise/shims:$PATH"
}

brew_path() {
    local prefix
    have brew && return 0
    for prefix in /opt/homebrew /usr/local; do
        if [ -x "$prefix/bin/brew" ]; then
            eval "$("$prefix/bin/brew" shellenv)"
            return 0
        fi
    done
    return 1
}
