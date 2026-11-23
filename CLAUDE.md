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

## claude.ai Features Through CLIProxy (macOS)

The `claudeSettings` activation in `nix/home/common.nix` writes
`ANTHROPIC_BASE_URL` (CLIProxyAPI at `http://127.0.0.1:8317`) and
`ANTHROPIC_AUTH_TOKEN` into `~/.claude/settings.json`. Claude Code ranks that
token above a claude.ai login, so sessions lose the Artifact tool and
claude.ai connectors. No setting brings them back; both are reached around
Claude Code instead, with the claude.ai OAuth token that CLIProxy keeps and
refreshes in `~/.cli-proxy-api/claude-*-<account>.json`.

`tools/claude-mcp-headers` is the one place that reads that token. The account
comes from its argument, `$CLAUDE_AI_ACCOUNT`, or `~/.config/claude-ai/account`
(local, not in the flake). Do not point the default profile at claude.ai, and
do not unset `ANTHROPIC_*` in a session.

### Artifacts

`tools/claude-artifacts` mirrors Claude Code's Artifact tool: `publish
<file.html>` creates one, `update <artifact> <file.html>` publishes a new
version at the same link, and `list`, `read [--content]`, `versions`,
`comments`, `share private|org`, `rename`, `pin`, `unpin` and `delete --yes`
manage them. It is a `uv` script that calls `api.anthropic.com/api/frame/*`
with the header `X-Frame-CP: go`, the endpoints that tool uses, found in the
Claude Code binary. Do not call the Artifact tool from a session.

- Short links (`claude.ai/artifact/<id>`) are the artifact uuid in base58,
  padded to 22 characters; the API takes the uuid. Output uses short links.
- A deploy without a `description` clears it, so `update` resends the current
  one. The raw source host (`<uuid>.frame.claudeusercontent.com/_f/<ver>/_src/`)
  answers 403 to requests without a User-Agent.
- The direct publish records contract `0.0.0`. Pages that use the Artifact
  runtime (`window.claude.*`, shared data, comments) are untested.

Typed artifacts (Slides, Design, Design System, Motion) are instances of a type
that Anthropic publishes as an artifact holding a viewer and a `SKILL.md`.
`claude-artifacts types` lists them, `type-skill <type>` prints the
`SKILL.md` that says which `project/` files to write, `create <type> <title>`
makes an empty instance (`POST /api/frame/types/<slug>/create`), and
`push <artifact> <dir>` sends a folder's files.

- `push` deploys with `mode: "patch"` and the live `baseVersion`. Without
  `mode` the deploy drops every project file it does not name; without
  `baseVersion` a typed instance answers `409 conflict`, which also means
  someone saved since: read again, do not force.
- Docs and Sheets keep their content on a server reached only through the
  `claude-docs` connector, not through `push`. Data adds a store
  (`/api/frame/db/agent`), not covered.
- Whiteboard is a type too, in beta; this account's `/types` does not list it.

### Connectors

Connectors are plain HTTP MCP servers, user scope in `~/.claude.json`, one per
connector, each pointing at `https://mcp-proxy.anthropic.com/v1/mcp/<mcpsrv_id>`
with `claude-mcp-headers <account>` as `headersHelper`. Registered today:
`linear`, `notion`, `google-drive`, `claude-docs`, `gmail`, `google-calendar`.

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

Everything here is undocumented: the frame API, the MCP proxy's
`X-Mcp-Client-Session-Id` header and CLIProxy's file format. A Claude Code,
API or CLIProxy update can break any of them.

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
