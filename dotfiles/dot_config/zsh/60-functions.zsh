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

gcm() { git commit -m "$*" }
gac() { git add -A && git commit -m "$*" }
gri() { git rebase -i HEAD~"$1" }

# Delete branches already merged into the default branch. Two things the
# obvious one-liner gets wrong: `grep -v "main\|master"` is a substring match,
# so it also spares anything merely *containing* those words (feat/domain-api),
# and `git branch --merged` with no argument means "merged into HEAD", which
# from a feature branch is the wrong question. Anchor the names, and ask about
# origin/HEAD explicitly.
gclean() {
    local base
    base=$(git symbolic-ref --quiet --short refs/remotes/origin/HEAD 2>/dev/null)
    base=${${base#origin/}:-main}
    git branch --merged "origin/$base" --format '%(refname:short)' \
        | grep -vxE "$base|master|main" \
        | xargs -r -n 1 git branch -d
}
