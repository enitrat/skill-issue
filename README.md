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

```bash
npx skills add enitrat/skill-issue
```

`npx skills` discovers every `SKILL.md` under `skills/` and installs into
the target agent (Claude Code, Codex, Cursor, etc). See `npx skills --help`
for `-a/--agent`, `-s/--skill`, and `-g/--global` flags.

## How It Fits Together

| Area | Source of truth | Applied by | Target |
|------|-----------------|------------|--------|
| Dotfiles and machine provisioning | `dotfiles/` | `chezmoi init --apply` / `chezmoi update` | `~/.zshrc`, `~/.config/starship.toml`, installed tools |
| Agent skills | `skills/` | `npx skills add enitrat/skill-issue` | Claude/Codex/Cursor skill directories |
| Claude rules | `rules/` | Local Claude configuration | `~/.claude/rules/` |
| Subagents/prompts | `subagents/` | Local Claude/Codex configuration | `~/.claude/agents/`, `~/.codex/prompts/` |
| Custom CLIs | `tools/` | Shell `PATH` from `dotfiles/dot_zshrc.tmpl` | Local commands |
| Raycast commands | `raycast-scripts/` | Raycast script-command directory | Raycast |

## Machine Setup

The recommended bootstrap path is direct chezmoi, not a custom SSH wrapper. This
matches chezmoi's documented one-command install flow: install chezmoi, clone the
repo, apply the target state, and run scripts.

This repo uses `.chezmoiroot` to point chezmoi at `dotfiles/`. The provisioning
logic lives in `dotfiles/run_once_*.sh.tmpl`, which keeps setup versioned,
idempotent, and testable without a repo-specific transport script.

Installed baseline:

- Shell: zsh, oh-my-zsh plugins, Starship, MesloLGS Nerd Font config.
- Runtime/tool manager: `mise` instead of separate `nvm`, `asdf`, or `pyenv`
  shell setup.
- CLI tools: `atuin`, `bat`, `delta`, `difftastic`, `eza`, `fd`, `fzf`, `gh`,
  `git-spice`, `httpie`, `mergiraf`, `ripgrep`, `sesh`, `tmux`, `uv`, `zoxide`.
- Remote helpers: Tailscale, mosh, Cursor remote-server cache cleanup, iTerm2
  shell integration.

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
  dot_zshrc.tmpl
  dot_config/starship.toml
  run_once_*.sh.tmpl
skills/                         # Agent skills, each with SKILL.md
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

Add a machine setup step:

1. Put the behavior in `dotfiles/run_once_before_*.sh.tmpl` or
   `dotfiles/run_once_after_*.sh.tmpl`.
2. Keep it idempotent: check whether the package/config already exists.
3. Test with `chezmoi diff`, `chezmoi apply --dry-run --verbose`, or a
   disposable remote/container.

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
