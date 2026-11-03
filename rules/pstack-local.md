# pstack on this machine

These apply only while a pstack skill (`/pstack:*`) is active, on top of pstack's Claude Code adapter.

- The `cursor-team-kit` plugin is not installed. For `/deslop`, use the `emil-unslop-code` skill. For `control-cli` and `control-ui`, write `Skipped in Claude Code: <step>. cursor-team-kit is not installed.` and go on.
- `/pstack:poteto-mode` stays on across turns until the user opts out.
- Invoking a `/pstack:*` skill opts in to the fan-out it prescribes, without a further confirmation.
- `/pstack:statechart` would install TLC and Java with `mise`, which this machine does not have. Take both from Nix instead: run its script with `TLA2TOOLS="$(nix build --no-link --print-out-paths nixpkgs#tlaplus)/share/java/tla2tools.jar"` and `JAVA="$(nix build --no-link --print-out-paths nixpkgs#jre_headless)/bin/java"`.
- Every pstack subagent runs at `effort: "medium"`. Skip the steps that pick or raise a subagent's reasoning level, and never go above medium.
- poteto-mode's reply rules ("every claim carries its evidence", "terse is not an excuse to drop content") govern the chat reply only, not a page you publish. When a page is the deliverable, the reply is its link, what changed, and any decision needed; never recap the page.
