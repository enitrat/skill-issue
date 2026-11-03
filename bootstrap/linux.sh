#!/bin/bash
# Turn a fresh Ubuntu dev box (a Boat sandbox) into a configured one:
#
#   curl -fsSL https://raw.githubusercontent.com/enitrat/skill-issue/main/bootstrap/linux.sh | bash
#
# Safe to re-run. Needs passwordless sudo, which Boat sandboxes have.
set -euo pipefail

# Fixed, not configurable: nix/home/linux.nix links ~/.local/bin tools into this
# exact checkout, and the flake only defines the `user` account Boat uses.
repo_url=https://github.com/enitrat/skill-issue.git
repo_dir=$HOME/skill-issue
flake_output="user@$(uname -m)-linux"

log() { printf '[bootstrap] %s\n' "$*"; }

[ "$(id -un)" = user ] || { log "run this as the user account, the only one the flake defines"; exit 1; }

# zsh comes from apt so the login shell works even if Nix is broken; its plugins
# and config come from home-manager. Minimal images ship no generated locale,
# which makes zsh warn on every start and mangles the prompt's glyphs.
if ! command -v zsh >/dev/null || ! locale -a 2>/dev/null | grep -qi '^en_US.utf8$'; then
    log "installing zsh and the en_US.UTF-8 locale"
    sudo DEBIAN_FRONTEND=noninteractive apt-get update -qq
    # Keep any config file the image already changed (Boat's /etc/zsh/zshrc)
    # instead of stopping at dpkg's interactive prompt.
    sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq \
        -o Dpkg::Options::=--force-confdef -o Dpkg::Options::=--force-confold \
        zsh git locales >/dev/null
    sudo locale-gen en_US.UTF-8 >/dev/null
fi

if [ ! -e /nix/var/nix/profiles/default/bin/nix ]; then
    log "installing Determinate Nix"
    curl -fsSL https://install.determinate.systems/nix | sh -s -- install --no-confirm
fi
# shellcheck source=/dev/null
. /nix/var/nix/profiles/default/etc/profile.d/nix-daemon.sh

if [ ! -e "$repo_dir/flake.nix" ]; then
    log "cloning $repo_url into $repo_dir"
    git clone --quiet "$repo_url" "$repo_dir"
else
    log "updating $repo_dir"
    git -C "$repo_dir" pull --quiet --ff-only
fi

log "switching home-manager to $flake_output"
# -b moves files that home-manager would overwrite (a stock .zshrc) aside. Boat sets
# WORK_DIR=/home/user in the commands it runs, setup scripts included, and home-manager
# would leave its build links there.
env -u WORK_DIR nix run "$repo_dir#home-manager" -- switch --flake "$repo_dir#$flake_output" -b pre-nix

# This repo's skills, for Claude Code. The Nix npx by path: Boat's image puts an nvm
# Node earlier on this script's PATH.
log "installing skill-issue skills for Claude Code"
"$HOME/.nix-profile/bin/npx" -y skills add enitrat/skill-issue -g -y -a claude-code -s '*' </dev/null >/dev/null

# skills add never removes a skill the repo dropped. Remove the ones it installed
# from this repo whose SKILL.md is no longer in the checkout.
lock=$HOME/.agents/.skill-lock.json
if [ -r "$lock" ]; then
    "$HOME/.nix-profile/bin/jq" -r '.skills | to_entries[]
        | select(.value.source == "enitrat/skill-issue")
        | "\(.key)\t\(.value.skillPath)"' "$lock" |
        while IFS=$'\t' read -r name path; do
            if [ ! -e "$repo_dir/$path" ]; then
                log "removing skill $name, which skill-issue no longer has"
                "$HOME/.nix-profile/bin/npx" -y skills remove -g -y "$name" </dev/null >/dev/null
            fi
        done
fi

log "installing nix-after-restore.service"
sudo install -m 644 "$repo_dir/bootstrap/nix-after-restore.service" /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable nix-after-restore.service

if ! cmp -s "$repo_dir/bootstrap/tailscaled.service" /etc/systemd/system/tailscaled.service; then
    log "installing tailscaled.service"
    sudo install -m 644 "$repo_dir/bootstrap/tailscaled.service" /etc/systemd/system/
    sudo systemctl daemon-reload
    sudo systemctl restart tailscaled.service
fi
sudo systemctl enable --quiet tailscaled.service

if ! dpkg -s earlyoom >/dev/null 2>&1; then
    log "installing earlyoom"
    sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq earlyoom >/dev/null \
        || { sudo apt-get update -qq && sudo DEBIAN_FRONTEND=noninteractive apt-get install -y -qq earlyoom >/dev/null; }
fi
if ! cmp -s "$repo_dir/bootstrap/earlyoom.default" /etc/default/earlyoom; then
    log "configuring earlyoom"
    sudo install -m 644 "$repo_dir/bootstrap/earlyoom.default" /etc/default/earlyoom
    sudo systemctl restart earlyoom.service
fi
sudo systemctl enable --quiet earlyoom.service

zsh_path=$(command -v zsh)
if [ "$(getent passwd "$(id -un)" | cut -d: -f7)" != "$zsh_path" ]; then
    log "making zsh the login shell"
    sudo chsh -s "$zsh_path" "$(id -un)"
fi

log "done. Open a new shell."
