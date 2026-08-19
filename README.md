# skill-issue

Personal automation repo for machine setup, dotfiles, agent skills, subagents,
rules, and small local tools.

## Quick Start

Bootstrap a fresh machine with chezmoi:

```bash
sh -c "$(curl -fsLS https://get.chezmoi.io)" -- init --apply enitrat/skill-issue
```

Run the same bootstrap over SSH:

```bash
ssh user@server.example.com 'sh -c "$(curl -fsLS https://get.chezmoi.io)" -- init --apply enitrat/skill-issue'
```

Update an initialized machine:

```bash
chezmoi update
```

Preview changes:

```bash
chezmoi diff
chezmoi apply --dry-run --verbose
```

## Install Skills

Install all skills declared by this repo:

```bash
make skill-install
```

Useful commands:

```bash
make skill-update
make skill-list
```

Personal skills live under `skills/<name>/`. Third-party skills are downloaded
into `skills/external/<name>/` from [`skills-external.json`](skills-external.json).
Both are then exposed by the normal `npx skills add enitrat/skill-issue` flow.

## How It Fits Together

| Area | Source of truth | Applied by | Target |
|------|-----------------|------------|--------|
| Dotfiles and machine provisioning | `dotfiles/` | `chezmoi init --apply` / `chezmoi update` | `~/.zshrc`, `~/.config/starship.toml`, `~/.tmux.conf`, `~/.ssh/config`, `~/.config/homebrew/Brewfile`, installed tools |
| Agent skills | `skills/` + `skills-external.json` | `make skill-install` | Claude/Codex/Cursor skill directories |
| Claude rules | `rules/` | Local Claude configuration | `~/.claude/rules/` |
| Subagents/prompts | `subagents/` | Local Claude/Codex configuration | `~/.claude/agents/`, `~/.codex/prompts/` |
| Custom CLIs | `tools/` | Shell `PATH` from `dotfiles/dot_zshrc.tmpl` | Local commands |
| Raycast commands | `raycast-scripts/` | Raycast script-command directory | Raycast |

## Machine Setup

The recommended bootstrap path is direct chezmoi, not a custom SSH wrapper. This
matches chezmoi's documented one-command install flow: install chezmoi, clone the
repo, apply the target state, and run scripts.

This repo uses `.chezmoiroot` to point chezmoi at `dotfiles/`. The provisioning
logic lives in `dotfiles/.chezmoiscripts/`, which keeps setup versioned,
idempotent, and testable without a repo-specific transport script.

Installed baseline:

- Xcode Command Line Tools (macOS): required for compiling native extensions
  (e.g. `uv`/pip packages with C/C++ sources). Verified for health, not just
  presence — a CLT install can be silently corrupted by a racing background
  macOS Software Update, leaving `clang++` unable to find `<string>` and
  other C++ standard headers even though `xcode-select -p` reports success.
- Shell: native zsh, pinned autosuggestions/syntax-highlighting plugins,
  Starship, and MesloLGS Nerd Font config.
- Runtime/tool manager: `mise` instead of separate `nvm`, `asdf`, or `pyenv`
  shell setup.
- CLI tools: `atuin`, `bat`, `carapace`, `delta`, `difftastic`, `eza`, `fd`,
  `fzf`, `gh`, `git-lfs`, `git-spice`, `mergiraf`, `ripgrep`, `sesh`, `tmux`,
  `uv`, `zoxide`.
- Configs: `~/.tmux.conf` (remote-friendly, sesh popup) and `~/.ssh/config`
  (connection multiplexing + keepalives; personal hosts go in the unmanaged
  `~/.ssh/config.local`).
- Remote helpers: Tailscale, mosh, Cursor remote-server cache cleanup, iTerm2
  shell integration.
- macOS: GUI apps are declared in a `Brewfile` (`~/.config/homebrew/Brewfile`):
  iTerm2, Raycast, Cursor, OrbStack, Tailscale, Hidden Bar, plus the Nerd Font.
  OrbStack is the container runtime; removing Docker Desktop is an opt-in host
  policy. Raycast's Spotlight Cmd+Space binding is freed up automatically. See
  [config/others/macos-settings.md](config/others/macos-settings.md) for the
  one manual step this needs (Raycast's own hotkey preference).

Manual post-setup stays manual by design:

- `gh auth login`
- `atuin login`
- `tailscale up`
- `git-id add ...`

Secrets are not copied into the repo or persisted onto remote machines. Run
interactive auth commands on each machine that needs them.

More detail: [config/others/shell-setup.md](config/others/shell-setup.md).

## Repository Layout

```text
.chezmoiroot                    # Tells chezmoi to use dotfiles/ as source root
dotfiles/                       # chezmoi source root
  .chezmoiscripts/              # Provisioning and convergence scripts
  dot_zshrc.tmpl
  dot_config/starship.toml
skills/                         # Agent skills, segmented by ownership
  external/                     # Downloaded third-party skills
skills-external.json            # Upstream references and download sources
scripts/install-skills          # Installer used by `make skill-install`
Makefile                        # Skill commands
rules/                          # Claude Code behavior rules
subagents/                      # Claude/Codex agent definitions and prompts
tools/                          # Local executable CLIs
raycast-scripts/                # Raycast script commands
config/others/                  # Human docs for third-party setup
```

## Adding Things

Add a skill:

1. Create `skills/<skill-name>/SKILL.md`.
2. Keep helper scripts in `scripts/` beside the skill and prefer `uv` inline
   dependencies for Python helpers.
3. Include only files the skill needs at runtime; keep caches and local agent
   outputs out of skill directories.

Add a third-party skill:

1. Add its upstream source URL, skill name, and maintainer to
   `skills-external.json`.
2. Keep the upstream URL specific to the skill directory when possible.
3. Run `make skill-install` to download and install it.

Add a machine setup step:

1. Put the behavior in `dotfiles/.chezmoiscripts/` with the appropriate
   `run_`, `run_once_`, or `run_onchange_` attributes.
2. Keep it idempotent and return non-zero when incomplete work must be retried.
3. Test with `chezmoi diff`, `chezmoi apply --dry-run --verbose`, or a
   disposable remote/container.

After changing the package inventory, run `scripts/update-mise-lock` before
applying or committing it.

Add a local CLI:

1. Create `tools/<name>` with a shebang, `--help`, and `--version`.
2. Make it executable.
3. Document it here only if it is part of the standard workflow.

## Cleanup Principles

- Keep machine setup in chezmoi scripts, not in SSH transport wrappers.
- Keep `dotfiles/` as the executable source of truth; docs should summarize,
  not duplicate install scripts.
- Prefer `mise` for language/runtime tools unless a tool cannot reasonably be
  managed there.
- Avoid committing generated caches such as `.codex/`, `.tldr/`, and
  `__pycache__/` inside skills.

## License

Personal use.
