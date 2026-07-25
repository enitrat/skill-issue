# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Repository Purpose

Personal automation repo for developer-machine setup, dotfiles, agent skills,
subagent prompts, Claude rules, and small local tools.

## Directory Structure

```text
.chezmoiroot         # Points chezmoi at dotfiles/ as its source root
dotfiles/            # chezmoi source state - dotfiles + provisioning scripts
  .chezmoidata/
    packages.toml    # THE package inventory; mise config + Brewfile derive from it
    vars.toml        # Version-pinned formulae referenced by path elsewhere
  .chezmoitemplates/
    lib.sh           # log/warn/have/mise_path, included by every script
  .chezmoiignore     # Skips *-macos.sh / *-linux.sh on the other OS
  dot_zshrc          # -> ~/.zshrc; a loop over the fragments below
  dot_config/
    zsh/NN-*.zsh     # Shell config fragments, sourced in numeric order
    mise/, homebrew/ # Generated from packages.toml
  run_once_before_*  # Bootstrap that must precede the dotfiles landing
  run_onchange_after_*  # Package installs; re-run when the inventory changes
  run_once_after_*   # One-time host setup (system defaults, ssh, logins)
  run_after_*        # Runs on every apply

skills/              # Agent skills, one directory per skill
  <skill-name>/
    SKILL.md
    scripts/         # Optional helper scripts, preferably uv inline deps
    references/      # Optional reference docs

rules/               # Claude Code behavior rules
subagents/           # Source-of-truth subagent configs/prompts
  claude/            # Claude agent definitions
  codex/             # Codex prompts + docs

tools/               # Local executable CLIs
raycast-scripts/     # Raycast script commands
config/others/       # Human docs for third-party setup
```

## Machine Provisioning

Use chezmoi directly. Do not reintroduce a custom SSH bootstrap wrapper.

```bash
sh -c "$(curl -fsLS https://get.chezmoi.io)" -- init --apply enitrat/skill-issue
chezmoi update
```

Provisioning belongs in `dotfiles/run_*.sh.tmpl`. Keep those scripts idempotent
and OS-aware — via the `-macos.sh` / `-linux.sh` suffix that `.chezmoiignore`
filters on, not via a template conditional that renders down to `exit 0`.

Pick the prefix by re-run semantics, not by habit:

- `run_once_` — genuinely one-time host setup. Never use it for anything
  derived from a file it doesn't contain: the state key is the script's own
  hash, so editing the data file will not re-trigger it.
- `run_onchange_` — anything driven by `packages.toml`. Embed the data hash in
  a comment (`{{ .cask | toJson | sha256sum }}`) so a package edit re-runs it.
- `run_` — cheap operations that should reconcile on every apply.

Scripts start with `{{ template "lib.sh" . }}` and use `log`/`warn`/`have`.
Never swallow an install failure with `|| echo skipping` — that is how a tool
silently goes missing for months.

## Adding Content

### Skills

1. Create `skills/<skill-name>/SKILL.md`.
2. Follow the format: YAML frontmatter (`name`, `description`) plus markdown
   instructions.
3. Put helper scripts under `skills/<skill-name>/scripts/`.
4. Do not commit generated caches or local agent outputs inside skill
   directories.

Skills are installed via `npx skills add enitrat/skill-issue` (or
`npx skills add <owner>/<repo> -a <agent> -s <skill>` for a subset). No
manifest file is needed — the CLI walks the repo for `SKILL.md` files.

#### Skill Scripts Pattern

Scripts should use `uv` with inline script dependencies for zero-setup
execution:

```python
#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = [
#   "typer>=0.9.0",
#   "rich>=13.0.0",
# ]
# ///
```

Guidelines:

- Use `typer` for CLI argument parsing.
- Use `rich` for formatted output.
- Prefer wrapping external APIs over shell commands when that is clearer and
  more testable.
- Include `--raw` JSON output where useful.
- Make scripts executable: `chmod +x scripts/*.py`.

### Tools

1. Create `tools/<tool-name>` with no extension.
2. Add a shebang.
3. Include `--help` and `--version` flags.
4. Make executable: `chmod +x tools/<tool-name>`.

They reach PATH as symlinks in `~/.local/bin`, placed on every apply. Never put
the repo checkout on PATH — it has been at three different paths already.

### Dotfiles

1. Put managed files under `dotfiles/` using chezmoi naming.
2. To add a package, edit `.chezmoidata/packages.toml` and nothing else. The
   mise config and Brewfile are generated; hand-editing them is pointless, and
   `mise use -g` is reverted on the next apply.
3. Choose the `run_*` prefix by re-run semantics (see Machine Provisioning).
4. Test with `chezmoi execute-template -S .`, then `chezmoi diff`. Note that
   `chezmoi`'s configured source dir may be a *different clone* than the one
   you are editing — check `chezmoi source-path` before trusting a diff.

### Config Docs

Place human setup docs in `config/others/`. Keep docs concise and point to the
executable source of truth rather than duplicating long install scripts.
