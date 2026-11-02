#!/usr/bin/env zsh
# Assert a configured machine has what the flake promises:
#   ~/skill-issue/bootstrap/check.sh   (or the Mac checkout's path)
# Exits non-zero and names each failure.

# The shell checks need the real shell: an interactive zsh login shell. Started
# any other way (bash, sh, a plain ./check.sh), re-run inside one.
if [ -z "${ZSH_VERSION:-}" ] || ! [[ -o interactive ]]; then
    exec zsh -lic "source '$(cd "$(dirname "$0")" && pwd)/check.sh'"
fi

fails=0
pass() { print -r -- "ok    $1"; }
fail() { print -r -- "FAIL  $1"; fails=$((fails + 1)); }
check() { local name=$1; shift; if "$@" >/dev/null 2>&1; then pass "$name"; else fail "$name"; fi; }

# Every CLI the flake installs. Each must exist and resolve into the Nix store:
# a leftover Homebrew, mise or curl-installed copy earlier on PATH would win in
# every shell without anyone noticing.
tools=(rg fd jq bat eza fzf zoxide starship atuin carapace direnv delta mergiraf
    gh git git-lfs node pnpm bun uv herdr agent-browser ffmpeg forge cast anvil
    linear tmux nh nvd)
[[ $OSTYPE == darwin* ]] && tools+=(aws bw , nix-locate)
for tool in $tools; do
    check "$tool: installed, from nix" eval '[[ ${commands[$tool]:A} == /nix/store/* ]]'
done

# Wiring that broke before, in the old setup.
check "zsh: compinit ran once, compdef exists" whence -w compdef
check "zsh: atuin owns Ctrl-R" eval '[[ $(bindkey "^R") == *atuin* ]]'
check "zsh: worktree helpers loaded" whence -w wt
check "git: delta is the diff pager" eval '[[ $(git config pager.diff) == *delta* ]]'
check "git: mergiraf merge driver" git config merge.mergiraf.driver
# check-attr needs a repository; the global attributes file applies to any.
check "git: every path merges with mergiraf" eval '_r=$(mktemp -d) && git init -q "$_r" && [[ $(git -C "$_r" check-attr merge -- x.rs) == *mergiraf ]]; _s=$?; rm -rf "$_r"; return $_s'
check "git: gh credential helper" eval '[[ $(git config --get-all credential.https://github.com.helper) == *gh* ]]'
check "git: ~/.gitconfig.local included" eval '[[ $(git config --show-origin --get-all include.path) == *gitconfig.local* ]]'
check "ssh: config.local included" eval 'grep -q "^Include .*~/.ssh/config.local" ~/.ssh/config'
check "ssh: sockets dir" test -d ~/.ssh/sockets
check "rg: config file in use" test -r "$RIPGREP_CONFIG_PATH"
check "repo tools linked" test -x ~/.local/bin/git-id
check "claude: repo skills installed" test -r ~/.claude/skills/bx-boxes/SKILL.md
if [[ $OSTYPE == linux* ]]; then
    check "herdr: socket outside the restored disk" eval '[[ $HERDR_SOCKET_PATH == /tmp/* ]]'
    check "playwright: browsers outside ~/.cache" eval '[[ $PLAYWRIGHT_BROWSERS_PATH == $HOME/.local/* ]]'
    check "nix: daemon restarts after a Boat restore" systemctl is-enabled nix-after-restore.service
fi

print
if (( fails )); then print -r -- "$fails check(s) failed"; return 1; fi
print -r -- "all checks passed"
