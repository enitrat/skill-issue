# Zsh architecture and plugin alternatives

Reviewed 2026-08-19 against upstream documentation and repositories. This report
is specific to the current setup under `dotfiles/dot_config/zsh/`, `dotfiles/.chezmoidata/packages.toml`,
`dotfiles/dot_zshenv`, and `dotfiles/dot_zshrc`. It does not change the existing
configuration.

## Recommendation

Remove Oh My Zsh as the runtime framework and use native Zsh plus a small,
static plugin set managed by Antidote. Keep the repository's numbered fragments,
Starship, mise, fzf, zoxide, Atuin, and Carapace. Keep syntax highlighting;
keep `zsh-autosuggestions` if inline suggestions are wanted, but remove
`zsh-history-substring-search` unless its arrow-key behavior is preferred. Atuin
supplies the history-backed autosuggestion strategy when the autosuggestions
plugin is present, and owns interactive history search in this setup.

This is a recommendation, not a claim that Oh My Zsh is obsolete. Oh My Zsh is
actively maintained: its upstream history has commits dated 2026-08-16, and it
still provides a large plugin and alias collection
([repository](https://github.com/ohmyzsh/ohmyzsh),
[recent commits](https://github.com/ohmyzsh/ohmyzsh/commits/master)). The reason
to remove it here is narrower: the setup uses no theme from it, replaces several
of its Git aliases, and already has dedicated tools for the prompt, history,
completion, runtimes, and fuzzy interaction.

## What the current setup is doing

`00-omz.zsh.tmpl` loads Oh My Zsh, which adds its own function and completion
paths, audits `fpath`, runs `compinit`, loads the selected plugins, and maintains
an update check and completion cache. The implementation is visible in
[oh-my-zsh.sh](https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/oh-my-zsh.sh):
the selected plugins are added to `fpath` before `compinit`, then all selected
plugins and libraries are sourced. This is useful framework behavior, but it is
more lifecycle than the current dotfiles need.

The local configuration then has to know about that lifecycle. In particular:

- `40-completions.zsh` conditionally runs a second `compinit` for the
  half-installed case.
- `60-functions.zsh` must `unalias` names created by the Oh My Zsh Git plugin
  before defining local functions.
- The ephemeral-host fragment must set `ZSH_COMPDUMP` before Oh My Zsh loads.
- The installer clones three plugins into Oh My Zsh's custom directory and
  currently follows mutable default branches.

Native Zsh already provides the completion system. Its documented startup order
is `.zshenv`, profile files, then interactive `.zshrc`, and `compinit` creates
the completion definitions and dump file; `compaudit` checks ownership and
world/group-writable paths for security
([Zsh startup files](https://zsh.sourceforge.io/Doc/Release/Files.html),
[completion initialization and security checks](https://zsh.sourceforge.io/Doc/Release/Completion-System.html#Use-of-compinit)).
The numbered fragments can therefore remain, with one deliberate completion
initialization after all desired `fpath` additions and before `compdef` calls.

## Plugin/framework options

| Option | What upstream provides | Fit here |
| --- | --- | --- |
| Native Zsh, no manager | `compinit`, `fpath`, `autoload`, and ordinary `source`/`zle` primitives. | Smallest runtime and clearest ownership. Chezmoi must manage each plugin source or an update workflow must be documented. |
| **Antidote** | Native-Zsh manager that clones bundles and generates a static plugin file. It supports `kind:fpath`, conditional bundles, deferred loading, commit `pin:<SHA>`, and snapshots ([docs](https://antidote.sh/)). | **Best fit.** It handles the few external plugins without becoming a full framework, supports a generated/static startup path, and can load individual Oh My Zsh subplugins during migration. Latest listed release: `v2.3.0` ([releases](https://github.com/mattmc3/antidote/releases)). |
| Zim Framework | Framework, module catalog, plugin manager, and generated static `init.zsh`; modules are declared in `.zimrc` and initialized in order ([README](https://github.com/zimfw/zimfw)). | Credible and active, latest listed release `v1.20.1` ([release](https://github.com/zimfw/zimfw/releases)). More opinionated than needed and would replace the current fragment architecture. |
| Sheldon | Rust binary; TOML configuration, parallel plugin installation, generated shell source, branch/tag/commit selection, and a lock operation ([README](https://github.com/rossmacarthur/sheldon), [configuration](https://sheldon.cli.rs/Configuration.html)). | Good if one manager should serve Bash and Zsh. Adds a compiled manager and another generated/locked state file to a Zsh-only setup. Latest listed release `0.8.5` ([releases](https://github.com/rossmacarthur/sheldon/releases)). |
| Zinit | Very feature-rich manager with Turbo/deferred mode, reports, snippets, annexes, and Oh My Zsh/Prezto support ([README](https://github.com/zdharma-continuum/zinit)). | Active (the upstream history has commits through 2026-08-18), but its large feature surface and configuration model are a poor maintainability tradeoff here ([recent commits](https://github.com/zdharma-continuum/zinit/commits/main)). |
| Keep Oh My Zsh | Mature framework with a large built-in plugin and alias ecosystem, update checks, completion setup, and custom plugin conventions ([README](https://github.com/ohmyzsh/ohmyzsh/blob/master/README.md)). | Lowest migration cost, but retains the alias collisions, extra completion lifecycle, mutable custom clones, and framework behavior that this repository is already working around. |

Antidote is the most balanced choice. Its upstream design explicitly generates a
static file so normal shell startup only sources generated plugin code. Its
bundle syntax also permits direct pins such as
`zsh-users/zsh-autosuggestions pin:<SHA>` and supports reproducible snapshots
([pinning and snapshots](https://antidote.sh/#pin),
[snapshot restore](https://antidote.sh/#snapshots)). Do not use Antidote's
deprecated compatibility `antidote init` mode; the upstream docs recommend
`antidote load`/static bundles instead.

The even smaller alternative is native Zsh with plugins installed as pinned
archives and sourced directly. That is viable if the setup intentionally wants
no plugin-manager state. It is less convenient to update several repositories,
and it needs an explicit generated source file or hand-maintained source lines.

## Current plugin disposition

### Keep, but load explicitly

- `zsh-syntax-highlighting`: keep if command-line feedback is desired. It must
  be sourced after custom widgets and completion setup; the upstream installer
  explicitly says it should be the last plugin sourced
  ([installation order](https://github.com/zsh-users/zsh-syntax-highlighting/blob/master/INSTALL.md)).
  Put it after `compinit`, Carapace, worktree widgets, and any other `zle` code.
- OMZ `macos`: optional. It supplies macOS commands such as `ofd`, `cdf`,
  `quick-look`, Finder helpers, and `music`; it also documents `itunes` as
  deprecated in favor of `music`
  ([plugin README](https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/plugins/macos/README.md)).
  Keep only if these helpers are used; otherwise replace the handful of desired
  functions with local definitions.
- OMZ `command-not-found`: optional and Linux-only. It is a dispatcher that
  sources whichever distro handler exists, including `pkgfile`, Debian,
  Fedora, Homebrew, NixOS, and others
  ([plugin source](https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/plugins/command-not-found/command-not-found.plugin.zsh)).
  It is not a general package installer, and `command-not-found`/`pkgfile` is
  not in this inventory. Keep it only on hosts that provision a matching
  handler.

### Remove or replace

- OMZ `git`: it contributes a very large alias/function set. The upstream list
  includes `gcm`, `gclean`, `gp`, `grb`, `gwt`, and many destructive aliases
  ([Git plugin README](https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/plugins/git/README.md)).
  This repo already defines `gcm`, `gac`, `gri`, and a safer policy-specific
  `gclean`, and must currently unalias names first. Remove the plugin and keep
  the explicit local Git helpers.
- OMZ `virtualenv`: it only supplies `virtualenv_prompt_info` and sets
  `VIRTUAL_ENV_DISABLE_PROMPT=1`
  ([source](https://github.com/ohmyzsh/ohmyzsh/tree/master/plugins/virtualenv)).
  Starship already has a Python/virtual-environment prompt module, and mise is
  responsible for runtime activation. Remove it unless that exact function is
  intentionally retained.
- `zsh-autosuggestions`: keep if inline grey suggestions are wanted. Atuin's
  Zsh integration automatically adds an Atuin search strategy to
  `ZSH_AUTOSUGGEST_STRATEGY` when this plugin is present
  ([Atuin integration](https://github.com/atuinsh/atuin/blob/main/docs/docs/integrations.md)).
  The plugin owns the suggestion widget, while Atuin supplies the history
  backend; those roles are complementary. If inline suggestions are not useful,
  remove the plugin and do not retain the Atuin strategy setting.
- `zsh-history-substring-search`: this provides inline UP/DOWN cycling through
  shell history, while Atuin provides searchable history with Ctrl-R and UP
  bindings. The upstream plugin also requires explicit key bindings and has
  ordering interaction with syntax highlighting
  ([README](https://github.com/zsh-users/zsh-history-substring-search/blob/master/README.md)).
  Remove it if Atuin's TUI is the intended history interface. Keep it only if
  the simple Fish-style inline behavior is specifically preferred, and then
  document which component owns UP/DOWN.

## Interaction with the existing tools

- `starship` owns the prompt. Do not add a framework theme. Starship is
  initialized with `starship init zsh` and configured independently in
  `starship.toml` ([configuration](https://starship.rs/config/)).
- `mise` owns runtime/tool PATH activation and directory environment changes.
  Upstream recommends `mise activate zsh` for interactive shells and shims for
  non-interactive contexts; PATH activation updates environment at prompt time
  ([activation](https://mise.jdx.dev/cli/activate.html),
  [shims versus activation](https://mise.jdx.dev/dev-tools/shims.html)).
  Keep it before consumers that need mise-provided binaries, but avoid a second
  runtime manager such as `nvm`, `pyenv`, or `asdf`.
- `fzf` already provides official Zsh key bindings and fuzzy completion through
  `source <(fzf --zsh)` ([integration](https://github.com/junegunn/fzf#setting-up-shell-integration)).
  Do not install an OMZ `fzf` plugin as well; the current direct integration is
  clearer and supports the repo's `fd`, `bat`, and `eza` options.
- `carapace` is a completion generator/bridge, not a Zsh framework. Keep it
  after `compinit` and ensure its generated `compdef` entries are available via
  `fpath` or its official Zsh initialization
  ([Carapace docs](https://carapace.sh/carapace.html)).
- `atuin` installs shell hooks that record command, exit code, duration, and
  working directory, and binds Ctrl-R/UP by default
  ([shell integration](https://github.com/atuinsh/atuin/blob/main/docs/docs/guide/shell-integration.md),
  [init reference](https://docs.atuin.sh/main/reference/init/)). It should be
  the single owner of interactive history search. Its hooks only work for
  interactive shells that source `.zshrc`, which is consistent with the current
  guarded initialization.

Suggested load order after removing OMZ:

```text
00 ephemeral-host recovery
10 environment
20 PATH and mise availability
30 mise, zoxide, Starship, fzf, Atuin
35 plugin manager's fpath/static plugins
40 compinit once, generated completions, Carapace
50 aliases
60 functions and local widgets
70 worktree completions
80 syntax highlighting last
```

The exact numeric split is optional. The invariant is that `fpath` is complete
before `compinit`, custom `compdef`/ZLE widgets exist before syntax highlighting,
and Atuin is loaded after any autosuggestion plugin if that plugin is retained.

## Chezmoi and supply-chain shape

The current `run_once_before_20-install-omz.sh.tmpl` downloads an installer from
`raw.github.com` and clones three mutable default branches. That makes a fresh
apply depend on moving upstream code and executes code before the target shell
files are applied. It also makes version review and rollback difficult.

If Antidote is selected, model the manager and plugins as pinned externals or a
package-manager dependency, and generate the static plugin file in a retriable
`run_onchange_`/`run_after_` step. Chezmoi externals support archives, exact
directories, refresh periods, and SHA-256/SHA-384/SHA-512 checksums
([external format](https://www.chezmoi.io/reference/special-files/chezmoiexternal-format/)).
Prefer tagged release archives with a recorded checksum for the manager and
plugins, or commit-pinned Antidote bundles/snapshots. Do not use a mutable
`master`/`main` archive with a long refresh period and call that reproducible.

For Git repositories that must remain updateable, an external `git-repo` is
convenient but should be treated as an update operation, not a lock: chezmoi's
format clones then pulls the target, whereas checksums apply to downloaded file
or archive data. Review and test updates deliberately rather than allowing
every shell startup to fetch code. Keep plugin installation outside `.zshenv`.

If retaining Oh My Zsh during a transition, Antidote can load only the required
OMZ library/plugin paths rather than running the complete framework
([OMZ integration](https://antidote.sh/#using-antidote-with-zsh-frameworks)).
That permits a staged migration: first replace the installer with pinned
externals, then replace `git`/`virtualenv`/history plugins, then remove the OMZ
library and its completion lifecycle.

## Validation before implementation

Measure the actual configuration rather than optimizing a framework benchmark.
Capture cold and warm startup and prompt latency with and without each plugin;
the Antidote documentation recommends `zsh-bench` for meaningful Zsh startup
measurement ([performance notes](https://antidote.sh/#how-much-faster)). Check:

1. `zsh -f` still starts, and `.zshenv` remains cheap for non-interactive Zsh.
2. `compaudit` reports no insecure completion paths.
3. `compinit` runs exactly once in the rendered setup.
4. Ctrl-R, UP, autosuggestion acceptance, and syntax highlighting have one
   unambiguous owner each.
5. `chezmoi apply --dry-run` shows manager/plugin changes, and a failed plugin
   fetch or static-generation step returns non-zero so a later apply retries.
6. macOS and Linux render only the appropriate `macos` and
   `command-not-found` integrations.
