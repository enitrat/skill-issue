# Claude -> Codex sub-agent migration

## Codex role mapping
- scout -> explorer (Codex currently hardcodes explorer reasoning to medium)
- oracle -> default (inherits active Codex config)
- spark -> worker (inherits active Codex config)

## Output cache targets (project-local)
- ./.codex/cache/agents/scout/latest-output.md
- ./.codex/cache/agents/oracle/latest-output.md
- ./.codex/cache/agents/spark/latest-output.md
