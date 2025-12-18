# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Purpose

Personal Claude Skills, developer tools, and software configurations.

## Directory Structure

```
skills/              # Claude Skills (synced to ~/.claude/skills/)
  <skill-name>/
    SKILL.md         # Skill definition
    scripts/         # Python scripts with uv inline dependencies
    references/      # Reference documentation (optional)

tools/               # Shell scripts and CLI utilities
  <tool-name>        # Executable script (no extension)

config/
  claude/            # Claude Code configuration files
  others/            # Third-party software configs (zsh, plugins, apps)
```

## Adding Content

### Skills

1. Create `skills/<skill-name>/SKILL.md`
2. Follow the format: YAML frontmatter (`name`, `description`) + markdown body
3. Add `scripts/` directory with Python scripts using uv inline dependencies
4. Run `tools/skills-sync` to deploy to `~/.claude/skills/`

Reference: https://github.com/anthropics/skills

#### Skill Scripts Pattern

Scripts should use `uv` with inline script dependencies for zero-setup execution:

```python
#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "ghapi>=1.0.5",
#   "typer>=0.9.0",
#   "rich>=13.0.0",
# ]
# ///
```

Guidelines:
- Use `typer` for CLI argument parsing
- Use `rich` for formatted output
- Prefer wrapping external APIs (GitHub, etc.) over shell commands
- Include `--raw` flag for JSON output where applicable
- Make scripts executable: `chmod +x scripts/*.py`

Usage in SKILL.md:
```bash
uv run scripts/my_script.py command --option value
```

### Tools

1. Create `tools/<tool-name>` (no extension)
2. Add shebang (`#!/bin/bash`)
3. Include `--help` and `--version` flags
4. Make executable: `chmod +x tools/<tool-name>`

Style: See existing tools for consistent patterns (colors, help format, version).

### Configs

1. Place in `config/claude/` for Claude-specific or `config/others/` for third-party
2. Document setup steps if manual intervention required

## Syncing Skills

```bash
tools/skills-sync           # Copy skills to ~/.claude/skills/
tools/skills-sync --dry-run # Preview without changes
```
