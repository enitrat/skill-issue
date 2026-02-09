# eni-skills Marketplace

Personal Claude Code marketplace containing productivity skills, hooks, and developer tools.

## Installation

### Add the Marketplace

```bash
# In Claude Code CLI
/plugin marketplace add enitrat/skill-issue

# Or via command
claude plugin marketplace add enitrat/skill-issue
```

### Install Plugin

```bash
# Install the base-config plugin (skills + hooks)
/plugin install base-config@eni-skills
```

## Available Plugins

### base-config

Personal Claude Code configuration with productivity skills and hooks.

**Skills included:**
- `/base-config:pr-creator` - Guide PR authoring from creation through review completion
- `/base-config:pr-review` - Perform thorough, constructive pull request reviews
- `/base-config:github-issue` - Comprehensive GitHub issue lifecycle management
- `/base-config:skill-creator` - Guide for creating effective Claude Code skills
- `/base-config:ask-questions-if-underspecified` - Clarify requirements before implementing

**Hooks included:**
- `env-protection` (PreToolUse) - Prevents reading `.env` files with secrets
- `tts-notify` (Stop) - Converts Claude's responses to speech using Kyutai Pocket TTS

## Repository Structure

```
skill-issue/
├── .claude-plugin/
│   └── marketplace.json          # Marketplace catalog
├── plugins/
│   └── base-config/
│       ├── .claude-plugin/
│       │   └── plugin.json       # Plugin manifest
│       ├── skills/               # Skill definitions
│       │   ├── pr-creator/
│       │   ├── pr-review/
│       │   ├── github-issue/
│       │   ├── skill-creator/
│       │   └── ask-questions-if-underspecified/
│       └── hooks/                # Hook definitions
│           ├── hooks.json        # Hook configuration
│           ├── env-protection/
│           └── tts-notify/
├── rules/                        # Claude Code behavior rules
│   └── no-plan-mode.md          # Disable automatic plan mode
├── subagents/                    # Subagent definitions
│   ├── claude/                  # Claude Code agents
│   └── codex/                   # Codex prompts
└── tools/
    └── skills-sync              # Auto-sync script
```

## Development

### Auto-Sync Setup

The `tools/skills-sync` script automatically syncs:
- **Claude Code plugins** - Ensures plugins are installed
- **Rules** - Syncs `.md` files from `rules/` to `~/.claude/rules/`
- **Skills** - Copies to `~/.codex/skills/`
- **Subagents** - Syncs to `~/.claude/agents/` and `~/.codex/prompts/`

```bash
# Sync everything
./tools/skills-sync

# Preview changes without applying
./tools/skills-sync --dry-run
```

### Local Testing

```bash
# Test the marketplace locally
/plugin marketplace add /path/to/skill-issue

# Install from local marketplace
/plugin install base-config@eni-skills
```

### Adding New Skills

1. Create a new skill directory in `plugins/base-config/skills/`
2. Write `SKILL.md` with YAML frontmatter and instructions
3. Test locally with `/plugin install base-config@eni-skills`
4. Commit and push to GitHub

### Adding New Hooks

1. Create a new hook directory in `plugins/base-config/hooks/`
2. Add `hook.py` (or script) and `wrapper.sh`
3. Register in `plugins/base-config/hooks/hooks.json`
4. Test locally by reinstalling the plugin

### Adding New Rules

Rules override Claude Code's default behavior:

1. Create a new `.md` file in `rules/`
2. Write clear instructions for Claude to follow
3. Run `./tools/skills-sync` to sync to `~/.claude/rules/`
4. Restart Claude Code or `/clear` to load the new rule

**Example rule:**
```markdown
# No Automatic Plan Mode

**NEVER use the EnterPlanMode tool automatically.**

## What to Do Instead
- Implement changes directly
- Only create plans if explicitly requested
```

## License

Personal use. See individual skill/hook files for details.
