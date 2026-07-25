# Shell & Machine Setup

Everything here is applied by chezmoi. This page explains the shape of the
setup and the steps that genuinely can't be scripted — it deliberately does
**not** restate the install commands, because the scripts are the source of
truth and a second copy only drifts.

## Bootstrap

```bash
sh -c "$(curl -fsLS https://get.chezmoi.io)" -- init --apply enitrat/skill-issue
```

Homebrew and the Xcode Command Line Tools are installed by the first
provisioning script on macOS, so there's no manual prerequisite. The CLT step
opens a GUI dialog you have to click through; re-run `chezmoi apply` afterwards.

Over SSH:

```bash
ssh user@host 'sh -c "$(curl -fsLS https://get.chezmoi.io)" -- init --apply enitrat/skill-issue'
```

Day to day: `chezmoi diff` to preview, `chezmoi update` to pull and apply.

## How it's organised

`.chezmoiroot` points chezmoi at `dotfiles/`.

| Path | Role |
|------|------|
| `.chezmoidata/packages.toml` | **The** package inventory. Every tool, cask, and formula. |
| `.chezmoidata/vars.toml` | Version-pinned formulae whose install paths are referenced elsewhere (`llvm`, `gcc`). |
| `.chezmoitemplates/lib.sh` | `log`/`warn`/`have`/`mise_path`, included by every script. |
| `.chezmoiignore` | Skips `*-macos.sh` / `*-linux.sh` on the other OS. |
| `dot_config/mise/config.toml.tmpl` | Generated from `packages.toml`. |
| `dot_config/homebrew/Brewfile.tmpl` | Generated from `packages.toml`. |
| `dot_config/zsh/NN-*.zsh` | Shell config fragments, sourced in numeric order. |
| `run_once_before_*` | Bootstrap that must precede the dotfiles landing. |
| `run_onchange_after_*` | Package installs; re-run when the inventory changes. |
| `run_once_after_*` | One-time host setup (system defaults, ssh dirs, logins). |
| `run_after_30-link-tools` | Every apply: symlinks `tools/` into `~/.local/bin`. |

Repo checks live in `.pre-commit-config.yaml`, run by
[`prek`](https://github.com/j178/prek): `prek install` once, then
`prek run --all-files`. They render every template, syntax-check the result,
and shellcheck `tools/` and `scripts/`.

### Adding a package

Edit `dotfiles/.chezmoidata/packages.toml` and run `chezmoi apply`. The mise
config and the Brewfile regenerate, and the install scripts re-run because they
hash that inventory. Nothing else needs touching.

Placement rule: if mise can install it cross-platform it goes in `[[mise]]`.
`[[cask]]` and `[[formula]]` are macOS-only, for GUI apps and the handful of
things mise can't provide.

Installing a global tool with `mise use -g` will be **reverted** on the next
apply — that command writes the same generated file.

### Shell fragment order

The numeric prefixes are load-bearing: env before PATH, PATH before the tool
init that needs those binaries, `compinit` before anything calling `compdef`.
`~/.zshrc` itself is a five-line loop over the directory.

Every tool init is guarded, so a half-provisioned box still gives you a usable
shell instead of a wall of "command not found" on each prompt.

## Manual steps

Not scripted, on purpose:

- **Terminal font** — select `MesloLGS NF` in your terminal (iTerm2:
  Preferences → Profiles → Text → Font). Without a Nerd Font the prompt icons
  render as tofu boxes. This is a terminal-side setting no config can reach.
- **Raycast hotkey** — Raycast stores its own hotkey outside `defaults`, so it
  can't be scripted. The provisioning script releases Cmd+Space on the macOS
  side; you set it in Raycast → Settings → General.
- **Menu bar spacing** takes effect on next login, not via `killall`.

Deliberately not synced, so no long-lived credential lands on a remote box:

- `gh auth login` (prompted interactively during apply when a TTY exists)
- `atuin login -u <username>` — shared shell history
- `tailscale up` — join your tailnet
- `git-id add ...` — git identity, see `git-id --help`

## Git config

`~/.gitconfig` is managed and wires up the diff/merge tools that mise installs:
`delta` as the pager, `mergiraf` as a syntax-aware merge driver (via
`~/.gitattributes`), and `difftastic` behind `git dft` rather than
`diff.external`, which would be slow and unpipeable as a default.

**Identity is not in the managed file.** `git-id` writes `user.name`,
`user.email`, and `core.sshCommand` to `~/.gitconfig.local`, which the managed
config includes *last* — git resolves later values over earlier ones, so
anything local wins. Put hand-rolled settings there too; the managed file is
overwritten on every apply.

`run_once_before_40-migrate-gitconfig` copies an existing identity into
`~/.gitconfig.local` before the managed file lands, so a first apply on a
machine that already had a `~/.gitconfig` doesn't lose it.

One caveat worth knowing: `git config --global --get` does **not** expand
includes, so it will not see the identity. Use `git config --get`. This is why
the starship prompt module and `git-id` both dropped `--global`.

## SSH config

`~/.ssh/config` is managed and **replaces** whatever is there. Move your
existing `Host` blocks into `~/.ssh/config.local` first — the managed file
includes it above its own defaults, and ssh keeps the first value it sees, so
anything local wins.

Global defaults: connection multiplexing (repeat connections skip the
handshake), keepalives that survive Wi-Fi and NAT drops, `HashKnownHosts`,
`AddKeysToAgent`, and `UseKeychain` on macOS.

## Container runtime

OrbStack, not Docker Desktop. The brew-bundle script uninstalls the Docker
Desktop cask if it finds one; a hand-installed `/Applications/Docker.app` is
only flagged, never deleted. OrbStack is free for personal use and needs a paid
license for commercial use.

## Custom tools

`tools/` is symlinked into `~/.local/bin` on every apply, so the repo checkout
never has to be on PATH and can be moved or renamed freely.

| Tool | Description |
|------|-------------|
| `git-id` | Switch git identity + SSH key with one command |
| `dev-check` | Verify the dev environment. `dev-check inventory` checks everything `packages.toml` declares is really installed; `dev-check drift` finds mise tools shadowed by a stale copy earlier on PATH |
| `slack-sanitize` | Anonymize names & clean up Slack thread pastes from clipboard |
| `prune-cursor-server` | Drop stale Cursor Remote-SSH server caches |

`dev-check drift` is worth running after a migration: a Homebrew tool installed
before mise took over will keep winning on PATH, so the mise version is dead
weight and the old one never gets upgraded.

## Raycast scripts

Raycast → Settings → Extensions → Script Commands → Add Directories, and point
it at this repo's `raycast-scripts/`.

## Shell startup cost

`time zsh -i -c exit`. The config keeps this low by activating only mise (no
nvm/asdf/pyenv), calling `compinit` exactly once, generating Scarb/snforge/
sncast completions lazily on first Tab, and de-duplicating PATH with
`typeset -U`.
