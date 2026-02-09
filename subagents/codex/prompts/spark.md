---
description: Run Spark sub-agent (mapped to worker)
argument-hint: "<small implementation task>"
---
Use `spawn_agent` with `agent_type:"worker"` for this task:

$ARGUMENTS

Requirements:
- Focus on small, targeted fixes and quick tweaks.
- Keep scope tight; if scope grows, stop and propose escalation.
- Write full findings to `./.codex/cache/agents/spark/latest-output.md` (project-local).
- Return a short summary here plus that output path.
