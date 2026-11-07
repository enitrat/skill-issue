# CLAUDE.md

This file provides guidance to Claude Code when working with this repository.

## Repository Purpose

Personal automation repo for developer-machine setup, dotfiles, agent skills,
subagent prompts, Claude rules, and small local tools.

## Directory Structure

```text
flake.nix            # Machine setup: darwinConfigurations.mac (macOS clients),
                     # homeConfigurations."user@<arch>-linux" (Linux dev boxes)
nix/
  home/common.nix    # Shared by both: zsh, git, ssh client, CLI tools
  home/darwin.nix    # macOS-only home config
  home/linux.nix     # Linux-dev-box-only home config
  home/zsh/, files/  # Shell fragments and config files the modules read
  darwin/            # macOS system: defaults, Homebrew casks, App Store apps
  pkgs/              # Packages nixpkgs lacks
bootstrap/
  linux.sh           # Fresh Ubuntu dev box to configured, one command
  check.sh           # Asserts a machine has what the flake promises

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
config/others/       # Human docs for third-party setup
```

## Machine Setup

Nix owns machine setup. README.md has the commands; the rules:

- One definition per tool. Put it in `nix/home/common.nix`; use `darwin.nix` or
  `linux.nix` only for something that truly differs between a macOS client and
  a Linux dev box.
- Project toolchains (pinned Node, Foundry, Terraform versions) belong in that
  project's devShell, not in the machine config.
- Read home-manager and nix-darwin option definitions from their source before
  using an option. Options get renamed (`programs.fzf.fileWidget.*`,
  `programs.ssh.settings`), and a rename is a warning you will otherwise miss.
- Nothing secret goes in the flake. The Nix store is world-readable.
- A file an app rewrites itself (`~/.claude/settings.json`, editor settings,
  iTerm prefs) is copied or merged by an activation script, never linked.
- Homebrew uses `cleanup = "check"`. Never change it to `"uninstall"` or
  `"zap"`: those delete apps and their data for anything not declared.

## Checks

`prek` runs the hooks in `.pre-commit-config.yaml` (nixfmt, shellcheck,
whitespace). Its tools come from the repo devShell, which direnv loads. Install
once with `prek install`; run everything with `prek run --all-files`.

After a machine-setup change, verify on a real machine, not only by evaluating:
`<repo>/bootstrap/check.sh`. For Linux, a fresh Boat sandbox
with `bootstrap/linux.sh` is the test. `nix eval
.#darwinConfigurations.mac.config.system.build.toplevel.drvPath` catches option
errors in the macOS config from any machine.

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

They reach PATH as symlinks in `~/.local/bin`, created by `nix/home/common.nix`
and pointing into the live checkout, so edits need no switch. Never put the repo
checkout on PATH.

### Config Docs

Place human setup docs in `config/others/`. Keep docs concise and point to the
executable source of truth rather than duplicating long install scripts.

## Anti-Patterns

- Editing a file under `~` that home-manager links. It is read-only; edit the
  module or file under `nix/` and switch.
- Defining a tool twice, once per platform.
- Installing a CLI with brew, `npm -g`, `cargo install` or a curl script when
  nixpkgs has it. `check.sh` fails when such a copy shadows the Nix one.
- A runtime `case $(hostname)` for a one-machine workaround. Hostnames on
  dev boxes are not stable; scope it to `linux.nix` or `darwin.nix`.
- Putting the repo checkout on PATH. Tools reach PATH as symlinks in
  `~/.local/bin`.
- Editing anything under `skills/external/` as if it were authored here.
