log() { printf '[%s] %s\n' "$1" "$2"; }
warn() { printf '[%s] %s\n' "$1" "$2" >&2; }
have() { command -v "$1" >/dev/null 2>&1; }

# mise shims are not on PATH inside chezmoi's non-interactive script shell.
#
# The shims directory holds the tools mise manages -- never mise itself, which
# on macOS comes from Homebrew. Adding only the shims therefore leaves `have
# mise` false whenever the calling shell lacks brew's prefix, which is exactly
# chezmoi's script shell on a machine whose login shell has not been restarted
# since Homebrew was installed. Pull in the brew prefix first; on Linux, where
# mise installs to ~/.local/bin, brew_path simply returns non-zero.
mise_path() {
    brew_path || true
    export PATH="$HOME/.local/bin:$HOME/.local/share/mise/shims:$PATH"
}

# Neither is Homebrew's prefix, and on a first apply it cannot be: brew is
# installed by an earlier script in the same run, which has no way to alter
# this shell's environment. A `have brew` test alone is therefore false on
# exactly the run that most needs it to be true. Returns non-zero if brew is
# genuinely absent, so callers can tell "not installed" from "not on PATH".
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
