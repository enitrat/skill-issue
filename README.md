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
└── plugins/
    └── base-config/
        ├── .claude-plugin/
        │   └── plugin.json       # Plugin manifest
        ├── skills/               # Skill definitions
        │   ├── pr-creator/
        │   ├── pr-review/
        │   ├── github-issue/
        │   ├── skill-creator/
        │   └── ask-questions-if-underspecified/
        └── hooks/                # Hook definitions
            ├── hooks.json        # Hook configuration
            ├── env-protection/
            └── tts-notify/
```

## Development

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

## License

Personal use. See individual skill/hook files for details.
