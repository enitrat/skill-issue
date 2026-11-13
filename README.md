# skill-issue

Personal automation repo for machine setup, dotfiles, agent skills, subagents,
rules, and small local tools.

## Quick Start

Machines are configured by the Nix flake in this repo: [`flake.nix`](flake.nix)
and [`nix/`](nix/). Two kinds of machine, one shared definition:

| Machine | Output | First setup | Later changes |
| - | - | - | - |
| macOS laptop (client) | `darwinConfigurations.mac` | see [Fresh Mac](#fresh-mac) | `rebuild` (alias for `sudo darwin-rebuild switch --flake …#mac`) |
| Linux dev box (Boat sandbox, Ubuntu) | `homeConfigurations."user@<arch>-linux"` | `curl -fsSL https://raw.githubusercontent.com/enitrat/skill-issue/main/bootstrap/linux.sh \| bash` | `rebuild` (alias for `nh home switch ~/skill-issue -c user@<arch>-linux`) |

Check a machine: `~/skill-issue/bootstrap/check.sh` (on the Mac, use the checkout
path).

## Install Skills

Install all skills declared by this repo:

```bash
make skill-install
```

Useful commands:

```bash
make skill-update
make skill-list
```

Personal skills live under `skills/<name>/`. Third-party skills live under
`skills/external/<name>/`. `make skill-install` installs the checked-in catalog.
`make skill-update` fetches the sources in [`skills-external.json`](skills-external.json)
so their changes can be reviewed before installation.

For a Codex profile, run `make codex-setup` to install these skills globally and
add the [pstack Codex port](https://github.com/michael-denyer/pstack-claude).
The plugin is installed into the active `CODEX_HOME` profile; start a new Codex
session to load it. Run the command again to refresh the skills; use
`codex plugin marketplace upgrade pstack-claude` to refresh the marketplace.

The bundled launchers from the Telegram, one-conv, and Slack skills
are also linked through `tools/`, so a switch exposes `tg`, `one-conv`,
and `slack-user` on `$PATH`. Their credentials remain outside the repository in
the locations documented by each skill.

## Claude Code Plugins

`plugins/` is a Claude Code marketplace for skill bundles that should be toggled
as a unit instead of installed flat. It sits outside the repo root so
`npx skills add .` ignores it.

```bash
claude plugin marketplace add ~/workspace/skill-issue/plugins
claude plugin install emil@skill-issue
claude plugin disable emil@skill-issue              # off by default
claude plugin enable emil@skill-issue --scope local     # on for one repo only
```

[pstack](https://github.com/cursor/plugins/tree/main/pstack) is not vendored. It
installs from upstream's own Claude Code build, `pstack@cursor-plugins`, which
`nix/home/files/claude-settings.json` declares. Claude Code does not auto-update
third-party marketplaces, so refresh it with
`claude plugin marketplace update cursor-plugins`. `rules/pstack-models.md` sets
every pstack role to Opus at medium effort (rewrite it with `/pstack:setup-pstack`), and
`rules/pstack-local.md` holds this machine's pstack policy.

`plugins/emil/` vendors the [Emil Kowalski](https://emilkowal.ski/skill) skills
(design engineering, animation, Apple design, mobile/Swift, UI library picker).
`make emil-sync` refreshes it; `plugins/emil/UPSTREAM` pins the commit.

`plugins/thermos/` vendors Cursor's
[Thermos](https://github.com/cursor/plugins/tree/main/thermos) review plugin
(`/thermos:thermos`, `/thermos:thermo-nuclear-review`,
`/thermos:thermo-nuclear-code-quality-review`). Upstream ships only a Cursor
manifest, so `make thermos-sync` adds `.claude-plugin/plugin.json` and applies
`plugins/thermos/claude-code.patch`: namespaced subagent types, Agent-tool
orchestration, and model-invocable rubric skills the subagents load. A patch
that no longer applies fails the sync and leaves the vendored copy as it was.
Unlike emil it is on by default: the switch adds this marketplace and enables
`thermos@skill-issue`. After a sync, run `claude plugin update thermos@skill-issue`.

## How It Fits Together

| Area | Source of truth | Applied by | Target |
|------|-----------------|------------|--------|
| Machine setup | `flake.nix`, `nix/` | `darwin-rebuild switch` / `home-manager switch` | Shell, CLI tools, dotfiles, macOS settings and apps |
| Agent skills | `skills/` + `skills-external.json` | `make skill-install` | Claude/Codex/Cursor skill directories |
| Claude rules | `rules/` | Local Claude configuration | `~/.claude/rules/` |
| Subagents/prompts | `subagents/` | Local Claude/Codex configuration | `~/.claude/agents/`, `~/.codex/prompts/` |
| Custom CLIs | `tools/` | Symlinks in `~/.local/bin`, from `nix/home/common.nix` | Local commands |

## Machine Setup

```text
nix/home/common.nix   both machines: zsh, git, ssh client, CLI tools
nix/home/darwin.nix   Mac only: iTerm, key bindings, editor defaults
nix/home/linux.nix    dev box only: the cwd fix for restored sandboxes
nix/darwin/           Mac system: macOS defaults, Homebrew casks, App Store apps
```

Put a tool in `common.nix` unless it truly belongs to one kind of machine.
Project toolchains (a pinned Node, Foundry or Terraform version) go in the
project's own `devShell` with direnv, not here.

Outside Nix on purpose:

- Self-updating agent CLIs: `claude`, `codex`, `boat`. Boat sandboxes ship them;
  on a Mac, use their official installers.
- Files the apps rewrite: `~/.claude/settings.json` is copied from
  `nix/home/files/claude-settings.json` on each switch, not linked.
- Secrets and identity: `~/.gitconfig.local` (written by `git-id`),
  `~/.ssh/config.local`, the Boat API key and the Tailscale OAuth client in the
  Keychain (`boat-resolve --help` and `tailnet --help` show how to store them),
  and 1Password. The Nix store is world-readable.
- Mac apps installed by hand: Grok Bot, Scrawl, Canon Utilities, darktable, Blender
  (reasons in `nix/darwin/default.nix`).

### Fresh Mac

1. Install Nix: `curl -fsSL https://install.determinate.systems/nix | sh -s -- install`
2. Clone this repo to `~/workspace/skill-issue`.
3. `sudo nix run nix-darwin -- switch --flake ~/workspace/skill-issue#mac`

Homebrew runs with `cleanup = "check"`: a switch fails while something
installed is not declared in `nix/darwin/default.nix`. Declare it or uninstall
it; nothing is removed silently.

Manual steps that stay manual: `gh auth login`, `atuin login`, `git-id add ...`,
and Raycast's own Cmd+Space hotkey (see
[config/others/macos-settings.md](config/others/macos-settings.md)).

## Repository Layout

```text
flake.nix, flake.lock           # Machine setup entry point
nix/                            # Nix modules (see Machine Setup)
bootstrap/                      # linux.sh for a fresh dev box, check.sh for any machine
skills/                         # Agent skills, segmented by ownership
  external/                     # Downloaded third-party skills
skills-external.json            # Upstream references and download sources
scripts/install-skills          # Installer used by `make skill-install`
Makefile                        # Skill commands
rules/                          # Claude Code behavior rules
subagents/                      # Claude/Codex agent definitions and prompts
tools/                          # Local executable CLIs
tailscale/policy.hujson         # The tailnet policy, applied by `tailnet policy apply`
config/others/                  # Human docs for third-party setup
```

## Adding Things

Add a skill:

1. Create `skills/<skill-name>/SKILL.md`.
2. Keep helper scripts in `scripts/` beside the skill and prefer `uv` inline
   dependencies for Python helpers.
3. Include only files the skill needs at runtime; keep caches and local agent
   outputs out of skill directories.

Add a third-party skill:

1. Add its upstream source URL, skill name, and maintainer to
   `skills-external.json`.
2. Keep the upstream URL specific to the skill directory when possible.
3. Run `make skill-update` and review the downloaded skill, then run `make skill-install`.

Add a tool or setting:

1. Edit the module it belongs in (see Machine Setup).
2. Switch, then run `bootstrap/check.sh`. Add a line there if the change is
   something a future edit could silently break.
3. To update every pinned input: `nix flake update`, switch, check.

Change the tailnet policy: edit `tailscale/policy.hujson`, then run `tailnet
policy apply`. It runs the file's tests on Tailscale's side, shows the change,
then sets it. The file wins over the admin console: an edit made there is lost at
the next apply. The tests address the Mac and phone through `hosts`, which
`tailnet` fills from `~/.config/tailnet/hosts` on this Mac, so their tailnet
addresses stay out of the repository.

Add a local CLI:

1. Create `tools/<name>` with a shebang, `--help`, and `--version`.
2. Make it executable.
3. Document it here only if it is part of the standard workflow.

## Cleanup Principles

- One definition per tool. Platform modules hold only real differences.
- Secrets never enter the flake.
- Avoid committing generated caches such as `.codex/`, `.tldr/`, and
  `__pycache__/` inside skills.

## License

Personal use.
