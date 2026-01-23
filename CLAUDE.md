# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Purpose

Personal Claude Code skills marketplace (`eni-skills`) containing productivity workflows, developer tools, and software configurations.

## Directory Structure

```
.claude-plugin/
  marketplace.json   # Marketplace catalog definition

plugins/             # Claude Code plugins
  personal-skills/
    .claude-plugin/
      plugin.json    # Plugin manifest
    skills/          # Skill definitions (SKILL.md format)
      <skill-name>/
        SKILL.md     # Skill definition
        scripts/     # Python scripts with uv inline dependencies
        references/  # Reference documentation (optional)

hooks/               # Claude Code hooks (not part of plugin)
  <hook-name>/
    hook.py          # Hook implementation (Python with uv)
    wrapper.sh       # Shell wrapper for Claude Code
    hook.json        # Hook configuration for skills-sync
    README.md        # Installation instructions

tools/               # Shell scripts and CLI utilities
  <tool-name>        # Executable script (no extension)
  skills-sync        # Sync skills/hooks to ~/.claude/ (legacy)

config/
  claude/            # Claude Code configuration files
  others/            # Third-party software configs (zsh, plugins, apps)
```

## Adding Content

### Skills

1. Create `plugins/personal-skills/skills/<skill-name>/SKILL.md`
2. Follow the format: YAML frontmatter (`name`, `description`) + markdown body
3. Add `scripts/` directory with Python scripts using uv inline dependencies

Skills can be used via two methods:
- **Plugin-based**: Users install via `/plugin install personal-skills@eni-skills` and invoke with `/personal-skills:<skill-name>`
- **Direct sync**: Users run `tools/skills-sync` to copy to `~/.claude/skills/` and invoke without namespace (e.g., `/pr-creator`)

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

### Hooks

1. Create `hooks/<hook-name>/` directory
2. Write hook script (`hook.py`) using uv inline dependencies
3. Create shell wrapper (`wrapper.sh`) that pipes stdin to the script
4. Add `README.md` with installation instructions
5. Make scripts executable: `chmod +x hooks/<hook-name>/*.py hooks/<hook-name>/*.sh`

Installation: Add hook config to `~/.claude/settings.json` or `.claude/settings.json`

### Configs

1. Place in `config/claude/` for Claude-specific or `config/others/` for third-party
2. Document setup steps if manual intervention required

## Using Skills

### Option 1: Plugin System

Install from the marketplace:

```bash
# Add marketplace (one-time setup)
/plugin marketplace add enitrat/skill-issue

# Install skills plugin
/plugin install personal-skills@eni-skills

# Use skills with plugin namespace
/personal-skills:pr-creator
```

### Option 2: Direct Sync

Copy skills directly to `~/.claude/skills/`:

```bash
tools/skills-sync           # Copy skills and hooks to ~/.claude/
tools/skills-sync --dry-run # Preview without changes

# Use skills without namespace
/pr-creator
```

## Local Development Testing

Test changes locally before pushing:

```bash
# Add local marketplace
/plugin marketplace add /Users/msaug/workspace/skill-issue

# Install from local
/plugin install personal-skills@eni-skills
```
