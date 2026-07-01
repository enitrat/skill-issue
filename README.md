# skill-issue

Personal automation repo for developer-machine setup, AI-agent workflows, dotfiles,
and small local tools.

The repo has two main jobs:

1. **Provision machines** with `chezmoi`, `mise`, Starship, zsh config, CLI tools,
   and remote-dev helpers.
2. **Distribute agent workflows** through Claude Code plugins plus direct sync into
   Claude/Codex local config directories.

## Quick Start

```bash
# Sync Claude plugins, Codex skills, subagents, and rules on this machine
tools/skills-sync

# Preview the same sync without writing files
tools/skills-sync --dry-run

# Bootstrap a remote machine over SSH
tools/ssh-sync user@server.example.com

# Preview remote chezmoi changes without applying
tools/ssh-sync user@server.example.com --dry-run
```

## How It Fits Together

| Area | Source of truth | Applied by | Target |
|------|-----------------|------------|--------|
| Dotfiles and machine provisioning | `dotfiles/` | `chezmoi`, usually via `tools/ssh-sync` | `~/.zshrc`, `~/.config/starship.toml`, installed tools |
| Claude Code plugins | `plugins/*/.claude-plugin/plugin.json` | Claude plugin system, helped by `tools/skills-sync` | Claude Code plugin install |
| Codex skills | `plugins/*/skills/` | `tools/skills-sync` | `~/.codex/skills/` |
| Claude rules | `rules/` | `tools/skills-sync` | `~/.claude/rules/` |
| Subagents/prompts | `subagents/` | `tools/skills-sync` | `~/.claude/agents/`, `~/.codex/prompts/` |
| Custom CLIs | `tools/` | Shell `PATH` from `dotfiles/dot_zshrc.tmpl` | Local commands |
| Raycast commands | `raycast-scripts/` | Raycast script-command directory | Raycast |

## Machine Setup

Remote bootstrap is intentionally thin:

```bash
tools/ssh-sync user@host
```

`ssh-sync` installs `chezmoi` on the remote if needed, then runs
`chezmoi init --apply https://github.com/enitrat/skill-issue.git`. The real
provisioning logic lives in `dotfiles/run_once_*.sh.tmpl`, so setup is versioned,
idempotent, and testable outside the SSH wrapper.

Installed baseline:

- Shell: zsh, oh-my-zsh plugins, Starship, MesloLGS Nerd Font config.
- Runtime/tool manager: `mise` instead of separate `nvm`, `asdf`, or `pyenv`
  shell setup.
- CLI tools: `atuin`, `bat`, `delta`, `difftastic`, `eza`, `fd`, `fzf`, `gh`,
  `git-spice`, `httpie`, `mergiraf`, `ripgrep`, `sesh`, `tmux`, `zoxide`.
- Remote helpers: Tailscale, mosh, Cursor remote-server cache cleanup, iTerm2
  shell integration.

Manual post-setup stays manual by design:

- `gh auth login`
- `atuin login`
- `tailscale up`
- `git-id add ...`

Secrets are not copied into the repo or persisted onto remote machines. During
`ssh-sync`, a local `gh auth token` is forwarded only as an environment variable
for the active SSH session to avoid GitHub API rate limits during `mise` installs.

More detail: [config/others/shell-setup.md](config/others/shell-setup.md).

## Agent Workflow Setup

Claude Code marketplace install:

```bash
claude plugin marketplace add enitrat/skill-issue
claude plugin install base-config@eni-skills
claude plugin install personal-skills@eni-skills
```

Local sync, which is the usual path for this repo:

```bash
tools/skills-sync
```

`skills-sync` currently does four things:

- Ensures the `eni-skills` Claude Code marketplace and both plugins are installed.
- Copies plugin skills from `plugins/base-config/skills/` and
  `plugins/personal-skills/skills/` into `~/.codex/skills/`.
- Copies subagent definitions/prompts from `subagents/`.
- Copies Claude behavior rules from `rules/`.

## Repository Layout

```text
.claude-plugin/                 # Marketplace catalog
plugins/
  base-config/                  # General Claude workflow skills and hooks
  personal-skills/              # Personal framework/code-quality skills
dotfiles/                       # chezmoi source root
  dot_zshrc.tmpl
  dot_config/starship.toml
  run_once_*.sh.tmpl
rules/                          # Claude Code behavior rules
subagents/                      # Claude/Codex agent definitions and prompts
tools/                          # Local executable CLIs
raycast-scripts/                # Raycast script commands
config/others/                  # Human docs for third-party setup
```

## Adding Things

Add a skill:

1. Create `plugins/<plugin-name>/skills/<skill-name>/SKILL.md`.
2. Keep scripts in `scripts/` beside the skill and prefer `uv` inline
   dependencies for Python helpers.
3. Run `tools/skills-sync --dry-run`, then `tools/skills-sync`.

Add a machine setup step:

1. Put the behavior in `dotfiles/run_once_before_*.sh.tmpl` or
   `dotfiles/run_once_after_*.sh.tmpl`.
2. Keep it idempotent: check whether the package/config already exists.
3. Test with `tools/ssh-sync user@host --dry-run` or a disposable remote/container.

Add a local CLI:

1. Create `tools/<name>` with a shebang, `--help`, and `--version`.
2. Make it executable.
3. Document it here only if it is part of the standard workflow.

## Cleanup Opportunities

- `plugins/personal-skills/tdd/` is outside `plugins/personal-skills/skills/`,
  so it is not picked up by the plugin manifest or `skills-sync`. Move it under
  `skills/` or delete it if it is obsolete.
- `config/others/shell-setup.md` is useful as reference, but `dotfiles/` is the
  executable source of truth. Avoid duplicating long install procedures in docs
  unless they explain manual setup that cannot be automated.
- Keep `tools/ssh-sync` as a wrapper only. New provisioning belongs in
  `dotfiles/run_once_*.sh.tmpl`, not in SSH transport code.
- Prefer `mise` for language/runtime tools unless a tool cannot reasonably be
  managed there. This keeps shell startup simple and avoids multiple version
  managers competing in `.zshrc`.

## License

Personal use.
