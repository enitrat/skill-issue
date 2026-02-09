---
description: Run Scout sub-agent (mapped to explorer)
argument-hint: "<task>"
---
Use `spawn_agent` with `agent_type:"explorer"` for this task:

$ARGUMENTS

Requirements:
- Focus on codebase exploration, file discovery, pattern-finding, and structure understanding.
- Ask the agent to return concise findings with paths.
- Write full findings to `./.codex/cache/agents/scout/latest-output.md` (project-local).
- Return a short summary here plus that output path.
