mkcd() { mkdir -p "$1" && cd "$1" }

extract() {
    case "$1" in
        *.tar.bz2) tar xjf "$1" ;;
        *.tar.gz)  tar xzf "$1" ;;
        *.tar.xz)  tar xJf "$1" ;;
        *.zip)     unzip "$1" ;;
        *.gz)      gunzip "$1" ;;
        *.7z)      7z x "$1" ;;
        *)         echo "Unknown format: $1" ;;
    esac
}

port() { lsof -i ":$1" }

# --no-project so a stray pyproject.toml in the cwd is not resolved and synced.
serve() { uv run --no-project python -m http.server "${1:-8000}" }

# The git plugin defines these as aliases, which cannot take arguments.
unalias gcm gac gri 2>/dev/null

gcm() { git commit -m "$*" }
gac() { git add -A && git commit -m "$*" }
gri() { git rebase -i HEAD~"$1" }
