# pstack on this machine

These apply only while a pstack skill (`/pstack:*`) is active, on top of pstack's Claude Code adapter.

- The `cursor-team-kit` plugin is not installed. For `/deslop`, use the `emil-unslop-code` skill. For `control-cli` and `control-ui`, write `Skipped in Claude Code: <step>. cursor-team-kit is not installed.` and go on.
- `/pstack:poteto-mode` stays on across turns until the user opts out.
- Invoking a `/pstack:*` skill opts in to the fan-out it prescribes, without a further confirmation.
