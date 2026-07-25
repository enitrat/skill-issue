log() { printf '[%s] %s\n' "$1" "$2"; }
warn() { printf '[%s] %s\n' "$1" "$2" >&2; }
have() { command -v "$1" >/dev/null 2>&1; }

# mise shims are not on PATH inside chezmoi's non-interactive script shell.
mise_path() { export PATH="$HOME/.local/bin:$HOME/.local/share/mise/shims:$PATH"; }
