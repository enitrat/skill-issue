# pstack on Claude Code

pstack was written for Cursor. When a pstack skill (`/pstack:*`) is active, read it through this mapping.

- Skills live at `{{root}}/skills/<name>/SKILL.md`. They are user-invoked only, so when one routes to another pstack skill or a `principle-*` leaf, Read that file instead of calling the Skill tool.
- `Task` is the Agent tool. `generalPurpose` is `general-purpose`. `poteto-agent` and `Comment Sicko` are `pstack:poteto-agent` and `pstack:Comment Sicko`. `AskQuestion` is AskUserQuestion. Todo lists use the task tools.
- `/setup-pstack` and `~/.cursor/rules/pstack-models.mdc` do not exist here. Every model slug in these skills is `opus`: panels (arena, architect, interrogate, reflect, swarm) run as that many Opus runners, and cross-family judge rules fall back to Opus. Do not stop over unavailable models. Every subagent runs at `effort: "medium"`: skip the xhigh starting budget and the "pick each subagent's reasoning level and speed" steps, and never raise it.
- Cursor paths map to Claude Code: `~/.cursor/projects/*/agent-transcripts` is `~/.claude/projects/*/*.jsonl`, `~/.cursor/skills` is `~/.claude/skills`, `~/.cursor/rules` is CLAUDE.md.
- Skills from the `cursor-team-kit` plugin (`deslop`, `control-cli`, `control-ui`) and Bugbot are not installed. Skip those steps, or use the closest installed skill, and say which.
- `/poteto-mode` is sticky: once invoked it stays on across turns until the user opts out.
- Invoking a `/pstack:*` skill opts in to the fan-out it prescribes, on Opus, without a further confirmation. Other user and project CLAUDE.md instructions override pstack defaults.
