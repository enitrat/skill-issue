# Shell Configuration Setup Guide

This guide helps you set up a fully configured zsh environment from a fresh macOS install.

## Prerequisites

Install Xcode Command Line Tools first (needed to compile native extensions,
e.g. `uv`/pip packages with C/C++ sources like `leveldb`):
```bash
xcode-select --install
```

**Known failure mode:** if this races with a concurrent background macOS
Software Update, the install can land "successfully" (`xcode-select -p`
reports a valid path) while its bundled libc++ headers are corrupted —
`usr/include/c++/v1` ends up with only `__cxx_version` instead of the ~190
real headers. Symptom: `clang++` fails with `fatal error: 'string' file not
found` on any C++ build. Fix by wiping and reinstalling:
```bash
sudo rm -rf /Library/Developer/CommandLineTools
xcode-select --install
```
`run_once_before_05-install-xcode-clt` checks header count (not just
`xcode-select -p`) so a fresh `chezmoi apply` catches this instead of just
reporting "already installed".

Install Homebrew next:
```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

## Core Shell Setup

### 1. Oh-My-Zsh
```bash
sh -c "$(curl -fsSL https://raw.github.com/ohmyzsh/ohmyzsh/master/tools/install.sh)"
```

### 2. Oh-My-Zsh Plugins
```bash
# Autosuggestions
git clone https://github.com/zsh-users/zsh-autosuggestions ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-autosuggestions

# Syntax highlighting
git clone https://github.com/zsh-users/zsh-syntax-highlighting.git ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-syntax-highlighting

# History substring search
git clone https://github.com/zsh-users/zsh-history-substring-search ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-history-substring-search
```

### 3. Starship Prompt
```bash
brew install starship font-meslo-lg-nerd-font --cask
```
Copy `dotfiles/dot_config/starship.toml` from this repo to `~/.config/starship.toml`,
and add `eval "$(starship init zsh)"` to `~/.zshrc`. Starship is actively
maintained and much faster than Powerlevel10k, which is effectively in
maintenance-only mode (no new features from upstream, per the maintainer).

The config uses plain colored text/icons on a transparent background (no
powerline blocks) to match a typical minimal p10k setup
(`POWERLEVEL9K_BACKGROUND=` transparent) — if you used p10k's default
"powerline blocks" look instead, `starship preset gruvbox-rainbow -o ~/.config/starship.toml`
gives you that denser style. Includes a custom `[custom.git_profile]` module
that shows your active `git-id` identity in the prompt — the Starship
equivalent of the old p10k `prompt_git_profile` segment.

**Nerd Font required for icons**: the `font-meslo-lg-nerd-font` cask installs
"MesloLGS NF" — you then have to manually select it in your terminal's font
setting (iTerm2: Preferences → Profiles → Text → Font). Without a Nerd Font
selected, icons render as `[?]` tofu boxes — this is a terminal-side setting,
not something Starship/p10k configure for you automatically.

### 4. Shell Enhancements
```bash
brew install zoxide fzf atuin

# FZF keybindings
$(brew --prefix)/opt/fzf/install

# Initialize Atuin
atuin register  # or atuin login
```

### 5. Modern CLI Tools
```bash
brew install bat eza fd ripgrep delta httpie mergiraf
```

| Tool | Replaces | Description |
|------|----------|-------------|
| `bat` | `cat` | Syntax highlighting, line numbers, git integration |
| `eza` | `ls` | Better output, icons, git status (note: `exa` is the abandoned predecessor — don't install it) |
| `fd` | `find` | Faster, simpler syntax |
| `ripgrep` | `grep` | Blazingly fast recursive search |
| `delta` | `diff` | Better git diffs (configure in ~/.gitconfig) |
| `httpie` | `curl` | Human-friendly HTTP client |
| `mergiraf` | — | Syntax-aware git merge driver that reduces merge conflicts |
| `difftastic` | — | Structural (AST-based) diff, complements delta for reviewing gnarly refactors: `GIT_EXTERNAL_DIFF=difft git show` |
| `carapace` | — | Unified shell completions for 1000+ commands; bridges to the existing zsh/compdef completions |

To use delta for git diffs, add to `~/.gitconfig`:
```ini
[core]
    pager = delta
[interactive]
    diffFilter = delta --color-only
```

## Version Manager

### mise (replaces nvm/asdf/pyenv)
```bash
brew install mise
```
Add `eval "$(mise activate zsh)"` to `~/.zshrc`. Mise is a single Rust binary
that reads existing `.nvmrc`/`.tool-versions`/`.python-version` files, activates
~10x faster than asdf, and removes the need for nvm's lazy-load shell function
workaround. It resolves `.tool-versions` at `$HOME` and per-project.

For custom asdf plugins that aren't in mise's core registry (e.g. Cairo/Starknet
tooling — `cairo-coverage`, `cairo-profiler`, `starknet-devnet`), register the
plugin's asdf-compatible git repo directly:
```bash
mise plugin install cairo-coverage https://github.com/software-mansion/asdf-cairo-coverage.git
mise plugin install cairo-profiler https://github.com/software-mansion/asdf-cairo-profiler.git
mise plugin install starknet-devnet https://github.com/ptisserand/asdf-starknet-devnet
mise install   # installs everything pinned in ~/.tool-versions
```
`scarb` and `starknet-foundry` are in mise's core registry already, no plugin needed.

## Language Runtimes

### Bun
```bash
curl -fsSL https://bun.sh/install | bash
```

### Go
```bash
brew install go
```

### pnpm
```bash
mise use -g pnpm@latest
```
`PNPM_HOME` (pnpm's own global-bin dir, used by `pnpm add -g`) is exported in
`.zshrc` regardless of how pnpm itself was installed.

## Blockchain / Web3 Tooling

### Starknet Stack
```bash
# Starkup (installs Scarb, Starknet Foundry, etc.)
curl --proto '=https' --tlsv1.2 -sSf https://sh.starkup.sh | sh
```

### LLVM
```bash
brew install llvm@19
```

## Development Tools

### GCC 15
```bash
brew install gcc@15
```

### TeX Live
Download from https://www.tug.org/texlive/

## Custom Tools

This repo includes custom CLI tools in the `tools/` directory. The zshrc adds this directory to PATH automatically.

### Available Tools

| Tool | Description |
|------|-------------|
| `git-id` | Switch git identity + SSH key with one command |
| `dev-check` | Verify dev environment is properly set up |
| `slack-sanitize` | Anonymize names & clean up Slack thread pastes from clipboard |

### Manual Setup

If setting up fresh, clone this repo and ensure tools are in PATH:
```bash
git clone https://github.com/enitrat/skill-issue.git ~/workspace/skill-issue
# The zshrc already includes ~/workspace/skill-issue/tools in PATH
```

Make tools executable:
```bash
chmod +x ~/workspace/skill-issue/tools/*
```

Verify installation:
```bash
dev-check        # Check all tools are installed
git-id --help    # Show git identity manager help
```

## Stacked PRs & tmux Sessions

```bash
brew install git-spice sesh
```

| Tool | Description |
|------|-------------|
| `git-spice` (`git-spice` command, alias `gs` if preferred) | Free, local-first stacked-branch workflow — an alternative to paid Graphite for solo work |
| `sesh` | Smart tmux session manager built on zoxide; pairs with the zoxide setup above |

### tmux config

`dotfiles/dot_tmux.conf` → `~/.tmux.conf` is a dependency-free config (no TPM,
so it works as-is on any freshly provisioned remote box). Highlights: mouse on,
vi copy mode (`v`/`y`), 50k scrollback, true-color passthrough, 1-based window
numbering, `|`/`-` splits that keep the current directory, vim-style pane
navigation (`prefix h/j/k/l`), reload with `prefix r`, and a sesh session
switcher popup on `prefix T`.

## SSH Config

`dotfiles/private_dot_ssh/private_config` → `~/.ssh/config` (mode 0600). Sets
sane global defaults under `Host *`:

- **Connection multiplexing** (`ControlMaster`/`ControlPath`/`ControlPersist`):
  the second and later ssh/scp/git-over-ssh connections to a host reuse the
  first connection and are near-instant with no re-auth round-trip.
- **Keepalives** (`ServerAliveInterval`/`TCPKeepAlive`): hold sessions open
  across Wi-Fi/NAT drops; complements mosh.
- **Hygiene**: `HashKnownHosts`, `AddKeysToAgent`, and `UseKeychain` on macOS.

Personal / host-specific `Host ...` blocks go in **`~/.ssh/config.local`**,
which is *not* managed by chezmoi. The managed config `Include`s it first, and
SSH uses the first value it finds, so anything in `config.local` overrides the
defaults. `run_once_after_60-ssh-setup` creates the `~/.ssh/sockets/`
directory (needed for multiplexing) and an empty `config.local`.

> Note: applying this replaces any existing `~/.ssh/config`. Move your current
> `Host` blocks into `~/.ssh/config.local` first to keep them.

## macOS GUI Apps (Brewfile)

GUI apps and Homebrew-only formulae are declared in
`dotfiles/dot_config/homebrew/Brewfile` → `~/.config/homebrew/Brewfile` and
installed by `run_once_after_05-brew-bundle` (or manually with
`brew bundle --file ~/.config/homebrew/Brewfile`). CLI dev tools stay in mise;
the Brewfile is only for casks (Raycast, Cursor, OrbStack, Tailscale,
Amphetamine, Hidden Bar, the Nerd Font) and formulae that don't belong in mise
(mosh, gcc@15, llvm@19).

**Container runtime:** OrbStack is installed as the Docker-compatible runtime,
and `run_once_after_05-brew-bundle` uninstalls Docker Desktop (`docker-desktop`
/ `docker` cask) if present so the two don't conflict. A manually-installed
`/Applications/Docker.app` is only flagged (not auto-deleted) — remove it
yourself. Note: OrbStack is free for personal use but requires a paid license
for commercial use.

## Git Identity Management

Use `git-id` to manage multiple git identities. Identities are stored in `~/.git-identities/`.

### Add identities:
```bash
git-id add main "Your Name" main@email.com id_main
git-id add alt "Alt Name" alt@email.com id_alt
```

### Switch identity:
```bash
git-id main      # Switch to main
git-id alt       # Switch to alt
git-id           # Show current + list all
```

### Setup new SSH key:
```bash
ssh-keygen -t ed25519 -f ~/.ssh/id_newkey -C "email@example.com"
cat ~/.ssh/id_newkey.pub  # Add to GitHub
git-id add newkey "Name" email@example.com id_newkey
```

## Remote Machine Bootstrap

Use [chezmoi](https://chezmoi.io) directly to bootstrap a fresh machine. The
official install flow supports installing chezmoi and applying a dotfiles repo
in one command:

### Full bootstrap:
```bash
sh -c "$(curl -fsLS https://get.chezmoi.io)" -- init --apply enitrat/skill-issue
```

This repo's `.chezmoiroot` points chezmoi at `dotfiles/`, where the zsh config,
Starship config, and `run_once_*` provisioning scripts live.

### Bootstrap over SSH:
```bash
ssh user@server.example.com 'sh -c "$(curl -fsLS https://get.chezmoi.io)" -- init --apply enitrat/skill-issue'
```

### Preview changes on an initialized machine:
```bash
chezmoi diff
chezmoi apply --dry-run --verbose
```

### Update an initialized machine:
```bash
chezmoi update
```

Re-running chezmoi is safe — every `run_once_*` script checks for existing
installs before doing anything.

### What gets installed (see `dotfiles/run_once_*.sh.tmpl` for exact commands):
- **Xcode Command Line Tools** (macOS): health-checked, not just presence-checked
- **Shell**: zsh, oh-my-zsh + plugins, Starship
- **Version manager**: mise — also installs node, python, go, rust, bun, uv
- **CLI tools** (via mise, same command on macOS and Linux): atuin, bat,
  carapace, delta, eza, fd, fzf, gh, ripgrep, tmux, zoxide, difftastic,
  mergiraf, git-spice, sesh, httpie
- **Runtimes** (via mise): node, python, go, rust, bun, pnpm
- **Network**: Tailscale, mosh (connection resilience for remote sessions)
- **macOS GUI apps** (via `brew bundle` from `~/.config/homebrew/Brewfile`):
  Raycast, Cursor, OrbStack, Tailscale, Amphetamine, Hidden Bar, MesloLGS Nerd
  Font, plus the Homebrew-only formulae mosh, gcc@15, llvm@19. OrbStack is the
  container runtime; Docker Desktop is uninstalled if present.
- **Extras**: iTerm2 shell integration, Cursor remote-server cache pruning

### What gets synced:
- `~/.zshrc`, `~/.config/starship.toml`, `~/.tmux.conf`, `~/.ssh/config`,
  `~/.config/homebrew/Brewfile` — templated per-OS from `dotfiles/`
- This repo itself, cloned to `~/.local/share/chezmoi` and symlinked to
  `~/workspace/skill-issue` — so `tools/` and Claude skills come along too
  (skills get copied to `~/.claude/skills/`)

### What's intentionally NOT synced (manual post-setup steps):
- `gh auth login` — no long-lived GitHub token is written to the remote box.
- `atuin login -u <username>` — shared shell history sync
- `tailscale up` — join your tailnet (interactive login required)
- `git-id add ...` — git identity (see `tools/git-id --help`)

This is a deliberate security improvement over the old custom SSH script, which
wrote your full `~/.gitconfig` (including signing key config) and `gh` OAuth
token to disk on every remote box.

### Tested with
Validated end-to-end against a real Ubuntu 24.04 container — package installs,
mise tool installs, Tailscale/mosh, and shell functionality all confirmed
working.

## Raycast Integration

This repo includes Raycast script commands in `raycast-scripts/`.

### Setup

1. Open Raycast → Settings → Extensions → Script Commands
2. Click "Add Directories" and add `~/workspace/skill-issue/raycast-scripts`
3. Scripts will appear in Raycast search

### Available Commands

| Command | Description |
|---------|-------------|
| Sanitize Slack Thread | Anonymize names & clean up clipboard content |
| Sanitize Slack Thread (Preview) | Preview without modifying clipboard |

## macOS Utilities

### Hidden Bar

Hidden Bar helps manage menu bar icons that are hidden by the MacBook notch.
It's included in the Brewfile; to install standalone:

**Installation:**
```bash
brew install --cask hiddenbar
```

**Usage:**
- After installation, launch Hidden Bar from Applications
- Configure which icons to hide/show in the menu bar
- Use the separator bar to toggle visibility of hidden icons

## Aliases & Functions Reference

The zshrc includes these productivity aliases and functions:

### Modern CLI Aliases
| Alias | Command | Description |
|-------|---------|-------------|
| `cat` | `bat` | Syntax-highlighted file viewing |
| `ls` | `eza` | Better directory listing |
| `ll` | `eza -la --git` | Long listing with git status |
| `tree` | `eza --tree` | Tree view of directories |

### Navigation
| Alias | Description |
|-------|-------------|
| `..` | Go up one directory |
| `...` | Go up two directories |
| `....` | Go up three directories |
| `-` | Go to previous directory |

### Git Shortcuts
| Alias/Function | Description |
|----------------|-------------|
| `gcm <msg>` | `git commit -m "<msg>"` |
| `gac <msg>` | `git add -A && git commit -m "<msg>"` |
| `gp` | Push current branch to origin |
| `gri <n>` | Interactive rebase last n commits |
| `gclean` | Delete merged branches |

### Utility Functions
| Function | Description |
|----------|-------------|
| `mkcd <dir>` | Create directory and cd into it |
| `extract <file>` | Extract any archive (tar, zip, gz, 7z, etc.) |
| `port <num>` | Show what's using a port |
| `serve [port]` | Start HTTP server in current dir (default: 8000) |

### Other Utilities
| Alias | Description |
|-------|-------------|
| `myip` | Show public IP address |
| `localip` | Show local IP address |
| `cpwd` | Copy current directory to clipboard |
| `reload` | Reload shell config |
| `json` | Pretty-print JSON from stdin |
| `zf` | Fuzzy-find zoxide directories |
| `please` | Run last command with sudo |
| `cp` | `cp -i` (confirm before overwrite) |
| `mv` | `mv -i` (confirm before overwrite) |
| `df` | `df -h` (human-readable) |
| `du` | `du -h` (human-readable) |

### FZF Enhancements
The zshrc configures FZF to use `fd` for faster file finding and `bat` for previews:
- `Ctrl+T`: Find files with preview
- `Alt+C`: Find directories with tree preview
- `Ctrl+R`: Search command history (via Atuin)

## Post-Installation

1. Apply the repo dotfiles with `chezmoi`
2. Select `MesloLGS NF` in your terminal font settings
3. Restart your terminal or run `source ~/.zshrc`

## File Locations

| File | Purpose |
|------|---------|
| `~/.zshrc` | Main shell config |
| `~/.config/starship.toml` | Starship prompt config |
| `~/.git-identities/` | Git identity configs (used by git-id) |
| `~/.fzf.zsh` | FZF config (auto-generated) |
| `~/workspace/skill-issue/tools/` | Custom CLI tools |

## Performance Notes

The zshrc keeps startup simple by avoiding multiple runtime managers in the
interactive path:

1. **mise activation only** - replaces separate nvm/asdf/pyenv init blocks.
2. **Starship prompt** - replaces Powerlevel10k and avoids p10k instant-prompt
   cache/state files.
3. **Lazy completions** - Scarb/snforge/sncast completions load on demand;
   `carapace` provides completions for everything else (loaded after compinit).
4. **Single compinit** - only one completion initialization call.
5. **typeset -U path** - prevents duplicate PATH entries.

To measure shell startup time:
```bash
time zsh -i -c exit
```
