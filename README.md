# eni-skills Marketplace

Personal Claude Code skills marketplace containing productivity workflows for GitHub, code review, and development tasks.

## Installation

### Add the Marketplace

```bash
# In Claude Code CLI
/plugin marketplace add enitrat/skill-issue

# Or via command
claude plugin marketplace add enitrat/skill-issue
```

### Install Plugins

```bash
# Install all skills from the personal-skills plugin
/plugin install personal-skills@eni-skills
```

## Available Plugins

### personal-skills

Collection of productivity skills for GitHub workflows, PR management, and code quality.

**Skills included:**
- `/personal-skills:pr-creator` - Guide PR authoring from creation through review completion
- `/personal-skills:pr-review` - Perform thorough, constructive pull request reviews
- `/personal-skills:github-issue` - Comprehensive GitHub issue lifecycle management
- `/personal-skills:skill-creator` - Guide for creating effective Claude Code skills
- `/personal-skills:ask-questions-if-underspecified` - Clarify requirements before implementing

## Development

### Repository Structure

```
skill-issue/
├── .claude-plugin/
│   └── marketplace.json          # Marketplace catalog
├── plugins/
│   └── personal-skills/
│       ├── .claude-plugin/
│       │   └── plugin.json       # Plugin manifest
│       └── skills/               # Skill definitions
│           ├── pr-creator/
│           ├── pr-review/
│           ├── github-issue/
│           ├── skill-creator/
│           └── ask-questions-if-underspecified/
├── hooks/                        # Development hooks (not part of plugin)
│   └── env-protection/
├── tools/                        # Development utilities
│   └── skills-sync              # Sync skills to local ~/.claude/
└── config/                       # Configuration files
```

### Local Development

For local testing before publishing:

```bash
# Test the marketplace locally
/plugin marketplace add /Users/msaug/workspace/skill-issue

# Install from local marketplace
/plugin install personal-skills@eni-skills
```

### Adding New Skills

1. Create a new skill directory in `plugins/personal-skills/skills/`
2. Write `SKILL.md` with YAML frontmatter and instructions
3. Test locally with `/plugin install personal-skills@eni-skills`
4. Commit and push to GitHub

### Direct Sync to ~/.claude/skills/ (Alternative)

If you prefer to use skills without the plugin system:

```bash
# Copy skills directly to ~/.claude/skills/ and hooks to ~/.claude/hooks/
tools/skills-sync
tools/skills-sync --dry-run  # Preview changes

# Skills available without plugin namespace
/pr-creator
/github-issue
```

## License

Personal use. See individual skill files for details.
