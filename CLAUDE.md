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
    host.toml        # Host-class flags, all defaulting off (see Host Classes)
  .chezmoitemplates/
    lib.sh           # log/warn/have/mise_path, included by every script
  .chezmoiignore     # Per-OS and per-host-class file selection
  dot_zshenv         # -> ~/.zshenv; pre-.zshrc setup only, sourced by every zsh
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
  external/          # Downloaded third-party skills
skills-external.json # References to third-party skills; not authored here
Makefile              # Skill install/update/list commands
scripts/install-skills # Installer used by `make skill-install`

rules/               # Claude Code behavior rules
subagents/           # Source-of-truth subagent configs/prompts
  claude/            # Claude agent definitions
  codex/             # Codex prompts + docs

tools/               # Local executable CLIs (symlinked into ~/.local/bin)
scripts/             # Repo-internal dev scripts (not installed to PATH)
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

## Host Classes

A workaround that only one machine needs does not belong in the shared config.
Scope it instead: add a flag to `.chezmoidata/host.toml` defaulting to `false`,
put the whole workaround in one file, and select that file from
`.chezmoiignore` — the same pattern the `-macos.sh` / `-linux.sh` suffixes use.
The machine that needs it opts in from its own chezmoi config, which this repo
does not track:

```toml
# ~/.config/chezmoi/chezmoi.toml
[data]
ephemeral_host = true
```

Two properties are the reason to bother: `grep -r <flag>` lists everything
currently scoped that way, and retiring the machine needs no cleanup here,
because the default was already off.

Prefer this over a runtime `case $(hostname)` — hostnames on exactly these
throwaway hosts tend not to be stable, which is usually the thing being worked
around in the first place.

## Checks

`prek` runs the hooks in `.pre-commit-config.yaml`. Install once with
`prek install`; run everything with `prek run --all-files`.

`scripts/check-chezmoi` renders every template with `-S .` and syntax-checks
the result. Run it after touching anything under `dotfiles/` — chezmoi uses
`missingkey=error`, so a template reading an optional key from `packages.toml`
unguarded looks fine in review and fails on someone's fresh machine.

## Adding Content

### Skills

1. Create `skills/<skill-name>/SKILL.md`.
2. Follow the format: YAML frontmatter (`name`, `description`) plus markdown
   instructions.
3. Put helper scripts under `skills/<skill-name>/scripts/`.
4. Do not commit generated caches or local agent outputs inside skill
   directories.

Use `make skill-install` to download declared third-party sources into
`skills/external/` and install all local skills. `make skill-update` repeats
that download, so the repository remains a complete `npx skills add` source.
Keep third-party skills under `skills/external/`; do not edit them as if they
were locally authored.

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

## Anti-Patterns

Each of these looks reasonable in a diff and is wrong for a reason stated
elsewhere in this file. Collected here because they are what actually gets
tried.

- Editing a file under `~` that chezmoi manages. The next apply overwrites it —
  edit the source in `dotfiles/` instead.
- Hand-editing `dot_config/mise/config.toml.tmpl` or the Brewfile to add a
  package. Both are generated from `.chezmoidata/packages.toml`.
- `run_once_` for anything driven by a data file. The state key is the script's
  own hash, so editing the data will not re-trigger it — use `run_onchange_`
  with the data hash embedded in a comment.
- A template conditional that renders to `exit 0` on the other OS. Use the
  `-macos.sh` / `-linux.sh` suffix and let `.chezmoiignore` filter it.
- A runtime `case $(hostname)` for a one-machine workaround. Use a host-class
  flag (see Host Classes).
- Putting the repo checkout on PATH. Tools reach PATH as symlinks in
  `~/.local/bin`.
- Swallowing an install failure with `|| echo skipping`.
- Editing anything under `skills/external/` as if it were authored here.
