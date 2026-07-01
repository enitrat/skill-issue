# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Repository Purpose

Personal automation repo for developer-machine setup, dotfiles, agent skills,
subagent prompts, Claude rules, and small local tools.

## Directory Structure

```text
.chezmoiroot         # Points chezmoi at dotfiles/ as its source root
dotfiles/            # chezmoi source state - dotfiles + provisioning scripts
  dot_zshrc.tmpl     # -> ~/.zshrc (templated per-OS)
  dot_config/        # -> ~/.config/
  run_once_*.sh.tmpl # Idempotent provisioning scripts, applied by chezmoi

skills/              # Agent skills, one directory per skill
  <skill-name>/
    SKILL.md
    scripts/         # Optional helper scripts, preferably uv inline deps
    references/      # Optional reference docs

rules/               # Claude Code behavior rules
subagents/           # Source-of-truth subagent configs/prompts
  claude/            # Claude agent definitions
  codex/             # Codex prompts + docs

tools/               # Local executable CLIs
raycast-scripts/     # Raycast script commands
config/others/       # Human docs for third-party setup
```

## Machine Provisioning

Use chezmoi directly. Do not reintroduce a custom SSH bootstrap wrapper.

```bash
sh -c "$(curl -fsLS https://get.chezmoi.io)" -- init --apply enitrat/skill-issue
chezmoi update
```

Provisioning belongs in `dotfiles/run_once_*.sh.tmpl`. Keep those scripts
idempotent and OS-aware through chezmoi templates.

## Adding Content

### Skills

1. Create `skills/<skill-name>/SKILL.md`.
2. Follow the format: YAML frontmatter (`name`, `description`) plus markdown
   instructions.
3. Put helper scripts under `skills/<skill-name>/scripts/`.
4. Do not commit generated caches or local agent outputs inside skill
   directories.

Skills are installed via `npx skills add enitrat/skill-issue` (or
`npx skills add <owner>/<repo> -a <agent> -s <skill>` for a subset). No
manifest file is needed — the CLI walks the repo for `SKILL.md` files.

#### Skill Scripts Pattern

Scripts should use `uv` with inline script dependencies for zero-setup
execution:

```python
#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "typer>=0.9.0",
#   "rich>=13.0.0",
# ]
# ///
```

Guidelines:

- Use `typer` for CLI argument parsing.
- Use `rich` for formatted output.
- Prefer wrapping external APIs over shell commands when that is clearer and
  more testable.
- Include `--raw` JSON output where useful.
- Make scripts executable: `chmod +x scripts/*.py`.

### Tools

1. Create `tools/<tool-name>` with no extension.
2. Add a shebang.
3. Include `--help` and `--version` flags.
4. Make executable: `chmod +x tools/<tool-name>`.

### Dotfiles

1. Put managed files under `dotfiles/` using chezmoi naming.
2. Put provisioning commands in `run_once_before_*.sh.tmpl` or
   `run_once_after_*.sh.tmpl`.
3. Prefer `mise` for runtime/tool installation.
4. Test with `chezmoi diff` and `chezmoi apply --dry-run --verbose`.

### Config Docs

Place human setup docs in `config/others/`. Keep docs concise and point to the
executable source of truth rather than duplicating long install scripts.
