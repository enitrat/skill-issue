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

## Claude Code Profiles (macOS)

Two profiles, selected by `CLAUDE_CONFIG_DIR`:

| Profile | Directory | Credential | Used for |
| - | - | - | - |
| default | `~/.claude` | CLIProxyAPI at `http://127.0.0.1:8317` | every session |
| artifacts | `~/.claude_artifacts` | claude.ai login (team plan) | publishing Artifacts |

The `claudeSettings` activation in `nix/home/common.nix` writes
`ANTHROPIC_BASE_URL` and `ANTHROPIC_AUTH_TOKEN` into the default profile's
`settings.json`. Claude Code ranks `ANTHROPIC_AUTH_TOKEN` above the claude.ai
login, and without that login it drops the Artifact tool. So the default
profile can never publish an Artifact, and no setting fixes that.

`tools/publish-artifact <file.html> [artifact-url]` is the only way an agent
publishes one. It runs `claude -p` in the artifacts profile with both
`ANTHROPIC_*` variables unset, allows only `Read` and `Artifact`, and prints
the URL. Do not call the Artifact tool from a default session, and do not point
the default profile at claude.ai.

- The artifacts profile has no `settings.json`, skills, plugins or `CLAUDE.md`.
  Never link or copy the default profile's `settings.json` into it: that
  carries the proxy variables back in. This rules out account-slot wrappers
  such as multi-cc, whose `cc-share` symlinks `settings.json` into each slot.
- The login is interactive and cannot live in Nix. Run the command in
  `publish-artifact --help` once per machine; `bootstrap/check.sh` fails until
  it is done.
- Write `"$HOME"`, never `~`, in `env CLAUDE_CONFIG_DIR=...`: `env` does not
  expand it and Claude Code creates a literal `~` directory in the current
  folder.

### claude.ai connectors in the default profile

The same precedence also disables claude.ai connectors in the default
profile. They come back as plain HTTP MCP servers, user scope in
`~/.claude.json`, one per connector, each pointing at
`https://mcp-proxy.anthropic.com/v1/mcp/<mcpsrv_id>` with
`tools/claude-mcp-headers <account>` as `headersHelper`. The helper reads the
claude.ai OAuth token that CLIProxy keeps and refreshes in
`~/.cli-proxy-api/claude-*-<account>.json`. Registered today: `linear`,
`notion`, `google-drive`, `claude-docs`, `gmail`, `google-calendar`.

- The ids are per account, so they live in `~/.claude.json`, not in the flake.
  Register one with the `claude mcp add-json` command in
  `claude-mcp-headers --help`; list ids with `GET
  https://api.anthropic.com/v1/mcp_servers?limit=1000`, headers
  `anthropic-beta: mcp-servers-2025-12-04` and the helper's `Authorization`.
- A connector must be authorized on claude.ai (Settings > Connectors) by that
  account. `tools/list` succeeds from the proxy's cache even when it is not;
  only a tool call returns `401 mcp_unauthorized_no_token`.
- The startup warning "claude.ai connectors are disabled" stays. It is about
  Claude Code's own connector loading, not these servers.
- Undocumented: the proxy requires an `X-Mcp-Client-Session-Id` header and
  the API path came from the Claude Code binary. A Claude Code or CLIProxy
  update can break either.
- Artifacts have no such path: publishing stays on `publish-artifact`.

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
