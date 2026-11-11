# Subagent model policy

- NEVER run subagents on Fable/Mythos-class models, ever. This applies to Agent calls and to every `agent()` call inside a Workflow. Never use `subagent_type: "fork"` (forks always inherit the parent model and ignore overrides).
- Exploration and research subagents (codebase search, repo surveys, web research) default to Sonnet. Set `model: "sonnet"` explicitly.
- All other subagents and workflow agents inherit the parent's model unless I say otherwise. If the parent is Fable/Mythos-class, inheriting is not allowed: set an explicit non-Fable `model` instead.
- Don't pick a model for a subagent on your own judgment beyond these rules (e.g. don't choose Opus because a skill or hook suggests it).

# Attribution

- Never add Claude attribution anywhere: no `Co-Authored-By: Claude` trailer in commits, no "Generated with Claude Code" line in PR bodies, issues, or comments.

# Pull requests

- Attach assets like screenshots to a PR with the `gh` CLI and its `--attach` flag. Never create a new branch just to upload assets.
