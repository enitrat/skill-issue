# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Purpose

Personal Claude Skills, developer tools, and software configurations.

## Directory Structure

```
skills/              # Claude Skills (synced to ~/.claude/skills/)
  <skill-name>/
    SKILL.md         # Skill definition

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
3. Run `tools/skills-sync` to deploy to `~/.claude/skills/`

Reference: https://github.com/anthropics/skills

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
