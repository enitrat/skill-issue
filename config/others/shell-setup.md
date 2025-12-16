# Shell Configuration Setup Guide

This guide helps you set up a fully configured zsh environment from a fresh macOS install.

## Prerequisites

Install Homebrew first:
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

### 3. Powerlevel10k Theme
```bash
brew install powerlevel10k
```
After installing, run `p10k configure` to set up your prompt.

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
brew install bat eza fd ripgrep delta httpie
```

| Tool | Replaces | Description |
|------|----------|-------------|
| `bat` | `cat` | Syntax highlighting, line numbers, git integration |
| `eza` | `ls` | Better output, icons, git status |
| `fd` | `find` | Faster, simpler syntax |
| `ripgrep` | `grep` | Blazingly fast recursive search |
| `delta` | `diff` | Better git diffs (configure in ~/.gitconfig) |
| `httpie` | `curl` | Human-friendly HTTP client |

To use delta for git diffs, add to `~/.gitconfig`:
```ini
[core]
    pager = delta
[interactive]
    diffFilter = delta --color-only
```

## Version Managers

### NVM (Node.js)
```bash
brew install nvm
mkdir ~/.nvm
```
Note: NVM is lazy-loaded in the zshrc for faster shell startup.

### ASDF (Universal)
```bash
git clone https://github.com/asdf-vm/asdf.git ~/.asdf --branch v0.14.0
```

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
curl -fsSL https://get.pnpm.io/install.sh | sh -
```

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

1. Copy the optimized `~/.zshrc` from this repo
2. Copy `~/.p10k.zsh` if you have a saved P10k config
3. Restart your terminal or run `source ~/.zshrc`
4. Run `p10k configure` if needed

## File Locations

| File | Purpose |
|------|---------|
| `~/.zshrc` | Main shell config |
| `~/.p10k.zsh` | Powerlevel10k theme config |
| `~/.git-identities/` | Git identity configs (used by git-id) |
| `~/.fzf.zsh` | FZF config (auto-generated) |
| `~/workspace/skill-issue/tools/` | Custom CLI tools |

## Performance Notes

The zshrc uses several optimizations for faster startup:

1. **Lazy-loaded NVM** - Node/npm/npx commands load NVM on first use (~500ms saved)
2. **Lazy completions** - Scarb/snforge/sncast completions load on demand
3. **Single compinit** - Only one completion initialization call
4. **typeset -U path** - Prevents duplicate PATH entries
5. **P10k instant prompt** - Shows prompt immediately while loading

To measure shell startup time:
```bash
time zsh -i -c exit
```
