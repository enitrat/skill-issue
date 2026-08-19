# CLI tooling and shell alternatives

Research date: 2026-08-19

This review covers the declared baseline in `dotfiles/.chezmoidata/packages.toml`, the Zsh fragments and Oh My Zsh installer, Git and tmux configuration, the pre-commit setup, and the README. It focuses on maintained first-party projects and concrete overlap in this repository. A tool is not marked “deprecated” merely because a newer tool exists.

## Executive recommendation

The setup does not need a wholesale CLI replacement. The useful core is coherent: `mise` for tool versions, `uv` for Python tools, `fzf`/`fd`/`ripgrep` for search, `bat`/`eza` for display, `zoxide`/`sesh`/`tmux` for navigation and sessions, Atuin for history, Starship for the prompt, and `delta`/`difftastic`/Mergiraf for different Git jobs.

The highest-value changes are:

1. Remove the Oh My Zsh framework and its installer. Keep native Zsh, Starship, `compinit`, and only the explicitly needed plugins/completions.
2. Remove `zsh-history-substring-search`: Atuin already owns `Ctrl-R` and configurable Up-arrow history search. Keep `zsh-syntax-highlighting`; keep `zsh-autosuggestions` only if its inline suggestions are actually useful.
3. Stop cloning floating plugin branches in a provisioning script. Vendor a reviewed revision or use chezmoi externals with an explicit revision and a documented update path.
4. Generate and commit `mise.lock`; pin the few global tools that matter, while allowing an intentional periodic update for the rest.
5. Do not install both Bun and pnpm globally without a demonstrated use case. Keep Node LTS and choose the package manager per project; put project runtimes in that project’s `mise.toml`.
6. Treat `terraform` as a policy decision: use OpenTofu where an open-source Terraform-compatible tool is wanted, or retain Terraform where a provider/platform requires it, but do not install an unpinned global Terraform binary merely because it is available.

The rest of this document separates these recommendations from optional experiments.

## Shell framework and plugins

### Strong recommendation: native Zsh instead of Oh My Zsh

Oh My Zsh is an active framework, not a deprecated tool. Its own documentation describes it as a framework providing plugins, themes, and defaults, and its plugin system is enabled through the `plugins` array ([project README](https://github.com/ohmyzsh/ohmyzsh), [plugin documentation](https://github.com/ohmyzsh/ohmyzsh/wiki/Plugins)). The local configuration, however, disables its theme (`ZSH_THEME=""`) and already supplies the prompt, environment, PATH, initialization, completions, aliases, functions, and most useful Git behavior itself.

The framework therefore adds a second lifecycle and a large implicit namespace for a small remaining set of features. The `git`, `virtualenv`, `macos`, and Linux `command-not-found` modules are not needed by any tracked script; the local config also overrides several Git aliases. Removing Oh My Zsh would make the target state easier to reason about and would eliminate the installer’s mutable `curl | sh` plus three mutable `git clone` operations.

Suggested end state:

- Keep the existing numbered Zsh fragments.
- Initialize `compinit` once, with a known completion dump location.
- Source `zsh-autosuggestions` if desired, then source syntax highlighting last as required by its upstream documentation ([installation](https://github.com/zsh-users/zsh-syntax-highlighting/blob/master/INSTALL.md)).
- Keep tool-provided completions and Carapace only if they are used; otherwise prefer a small explicit `fpath`.
- Drop the Linux `command-not-found` plugin unless the target distribution’s provider is explicitly installed and tested.

This is a refactor, not a claim that Oh My Zsh is unhealthy. If the framework’s aliases or modules are deliberately relied on, record those dependencies and retain it.

### Remove history-substring-search from this stack

Atuin replaces shell history with a database and provides full-screen search, including `Ctrl-R` and configurable Up-arrow bindings ([Atuin README](https://github.com/atuinsh/atuin), [Zsh key binding documentation](https://github.com/atuinsh/atuin/blob/main/docs/docs/configuration/key-binding.md)). The current startup order explicitly makes Atuin win the `Ctrl-R` binding after fzf. `zsh-history-substring-search` is consequently a second implementation of a smaller history interaction ([upstream project](https://github.com/zsh-users/zsh-history-substring-search)). Remove it unless the preferred behavior is specifically inline prefix/substr search rather than Atuin’s query UI.

`zsh-autosuggestions` is different: it supplies an inline suggestion while typing and is not replaced by Atuin. Keep it if that interaction is valued; otherwise dropping it removes another startup hook. Its upstream project is still available and documents the standalone installation/configuration ([upstream project](https://github.com/zsh-users/zsh-autosuggestions)).

`zsh-syntax-highlighting` remains useful for catching malformed or unknown commands before execution. It must be loaded after widgets and other plugins; the upstream install guide explicitly calls out that ordering ([installation](https://github.com/zsh-users/zsh-syntax-highlighting/blob/master/INSTALL.md)).

### Alternatives if a plugin manager is still wanted

No plugin manager is the best fit for this repository because there are only two likely third-party plugins and chezmoi already manages files. If a manager is desired:

- **Zim** is the strongest framework replacement for a curated module set. It builds a static initialization script and advertises speed without giving up modules ([Zim Framework](https://github.com/zimfw/zimfw)). It still adds a manager, generated state, and another update lifecycle.
- **Antidote** is a good plugin-only manager when retaining Oh My Zsh plugins matters. Its design caches generated bundles so steady-state startup sources a generated file ([Antidote architecture](https://github.com/mattmc3/antidote/blob/main/ARCHITECTURE.md), [project site](https://antidote.sh/)). It is a better fit than a framework if the only requirement is fetching a few plugins.

Do not introduce Zim or Antidote “for speed” without measuring `time zsh -i -c exit`; the native configuration already avoids most common startup costs.

## Completion and interactive shell tools

### Keep, but make ownership explicit

`fzf` is a good baseline. Its current upstream distribution includes native Zsh integration through `fzf --zsh` ([fzf README](https://github.com/junegunn/fzf/blob/master/README.md)), which matches the repository’s guarded initialization. There is no reason to add an fzf plugin manager or the old generated `~/.fzf.zsh` path.

Carapace is a legitimate multi-shell completion generator and supports Zsh plus several other shells ([Carapace project](https://github.com/carapace-sh/carapace)). It is optional here: the config sources the global Carapace bridge at startup, while only a handful of local tools need custom completion. Measure startup and completion quality. If the bridge is not used, remove it and keep native/tool-generated completions; do not replace it with another broad completion framework merely for novelty.

Starship is already the right layer for the prompt. It is cross-shell and intentionally separate from Zsh framework themes ([Starship project](https://github.com/starship/starship)). Do not add Powerlevel10k, Spaceship, or another prompt theme alongside it.

`zoxide` is also a clear keep. It provides directory ranking and interactive `zi` selection, and its upstream lists both fzf and sesh integrations ([zoxide README](https://github.com/ajeetdsouza/zoxide/blob/main/README.md)). `sesh` is complementary rather than redundant: it manages tmux sessions and uses zoxide to find projects ([sesh project](https://github.com/joshmedeski/sesh)).

### Optional shell alternatives

- **Fish** has first-class suggestions and completions, but changing the default shell would make the existing Zsh fragments, scripts, and remote assumptions a new migration project. Do not switch for this audit.
- **Zellij** is a modern terminal multiplexer, but it would replace a working, remote-friendly tmux configuration and require new keybindings and session semantics. Do not add it unless a specific Zellij feature is wanted.
- **television** or another fzf-like picker is not needed while fzf is already used in shell, tmux, and worktree helpers.

## Runtime and package-manager overlap

### Keep `mise`, but use its project scope and lockfile

`mise` is the right central mechanism for this repo. Its configuration is hierarchical, so project-local `mise.toml` files can override global versions ([configuration documentation](https://github.com/jdx/mise/blob/main/docs/configuration.md)). Its `mise.lock` format pins exact versions and checksums where supported and records download URLs ([lockfile documentation](https://mise.jdx.dev/dev-tools/mise-lock.html)).

The current generated global file has no `mise.lock` and most entries resolve to `latest`. That is the main reproducibility gap, not a reason to return to nvm/asdf/pyenv. Enable lockfiles, commit the lockfile, and update it deliberately. A practical split is:

- pin `mise`, `uv`, `gh`, `prek`, `shellcheck`, and tools referenced by Git hooks;
- pin tools used in scripts or automation;
- use a controlled update cadence for interactive display tools;
- keep project-specific language versions out of the global baseline.

### Choose one default JavaScript package manager

The inventory installs Node LTS, Bun, and pnpm, while the tracked repository contains no Bun or pnpm project metadata. `BUN_INSTALL` and `PNPM_HOME` are shell paths, not evidence that both managers are needed. Keep Node LTS globally and let each project declare its package manager in its own configuration. Remove Bun and/or pnpm from the personal baseline unless there is a real workflow for each.

This also avoids an unnecessary global `npm`/Bun/pnpm decision for mise’s own npm backend. Current mise can install npm-backed tools without requiring a system Node/npm and has an explicit package-manager setting ([mise npm backend](https://mise.jdx.dev/dev-tools/backends/npm.html)).

### `uv` is the preferred Python tool boundary

The repo already uses `uv` and `uv tool install` for HTTPie. uv’s documentation says `uvx`/`uv tool run` is generally more appropriate for one-off tools, while persistent `uv tool install` is for tools that must be on PATH for other programs or users ([uv tools](https://github.com/astral-sh/uv/blob/main/docs/concepts/tools.md)). Since no tracked script invokes `http`, make HTTPie an optional tool or use `uvx httpie` when needed; do not add another Python tool manager such as pipx.

Pin installed uv tools (`httpie==...` or an equivalent constraint) when they are part of the baseline. uv otherwise installs the latest version when no version is specified ([tool version documentation](https://github.com/astral-sh/uv/blob/main/docs/concepts/tools.md)).

### Terraform versus OpenTofu

OpenTofu is a CNCF project and describes itself as a drop-in Terraform replacement; its FAQ documents compatibility goals and the provider/registry differences ([OpenTofu](https://opentofu.org/), [FAQ](https://opentofu.org/faq/), [CNCF project page](https://www.cncf.io/projects/opentofu/)).

Recommendation: do not silently rename `terraform` in a generic machine baseline. First choose based on actual projects:

- choose **OpenTofu** if open-source governance, the post-BUSL Terraform licensing change, or OpenTofu features matter and the project/provider set is compatible;
- retain **Terraform** if a team, SaaS, provider, or policy explicitly requires it;
- in either case, pin the version in the project’s `mise.toml` and avoid a global install when no project uses it.

OpenTofu is an option worth piloting, not an automatic migration for this repo.

## Git and review tools

The current tools serve distinct jobs:

| Tool | Current role | Recommendation |
|---|---|---|
| `delta` | Default readable pager and interactive diff filter | Keep. It is the fast everyday view. |
| `difftastic` | Opt-in structural diff through `git dft` | Keep if structural diffs are useful; do not make it the default because the config correctly notes its pipeline cost. |
| `mergiraf` | Syntax-aware three-way merge driver | Keep and keep the safe wrapper. Mergiraf is explicitly designed as a Git merge driver ([upstream API/docs](https://docs.rs/mergiraf/latest/mergiraf/)). |
| `git-spice` | Explicit stacked-branch workflow | Keep if stacks are used. Its branch/upstack/downstack model is materially more than Git’s `updateRefs` setting ([local stacks guide](https://abhinav.github.io/git-spice/guide/branch/)). |
| `sesh` | tmux session selection | Keep when tmux is the primary multiplexer. |
| `gh` | GitHub authentication and workflow CLI | Keep; it is used by Git credential configuration and repository workflows. |

### Optional Jujutsu pilot

Jujutsu (`jj`) is the most interesting modern Git-adjacent tool to evaluate. It can use a Git backend, interoperate with Git remotes, and work in a colocated repository, but its own README still labels it experimental ([project README](https://github.com/jj-vcs/jj), [Git compatibility](https://docs.jj-vcs.dev/latest/git-compatibility/)). It is not a drop-in replacement for the current Git aliases, Git LFS setup, Mergiraf driver, or git-spice workflow. Pilot it in one repository before adding it globally; do not replace Git or git-spice as part of this cleanup.

## Tools that should not be added by default

- **`direnv`**: redundant with mise’s directory-aware environment and tool activation. Add only if a project specifically needs direnv’s `.envrc` trust model.
- **`just`**: useful standalone, but mise already provides tasks and is already the tool manager. Add it only if a project’s task files are shared with a just-based team.
- **`jq`/`yq`**: worthwhile when JSON/YAML transformation is a regular workflow; there is no tracked use today, and the existing `json` alias covers basic pretty-printing.
- **`btop`, `dust`, `procs`, `lsd`, `zellij`, and similar “modern Unix” replacements**: optional personal tools, not improvements justified by this repository’s current workflows.

## Supply-chain and update recommendations

The installer currently has two different floating-resolution surfaces:

1. almost every mise tool is `latest` and there is no committed `mise.lock`;
2. `run_once_before_20-install-omz.sh.tmpl` downloads the Oh My Zsh installer from a moving branch and clones three moving default branches.

Fix these before adding more tools:

- commit `mise.lock` and review lockfile changes as updates;
- pin plugin revisions (or vendor the reviewed plugin files) and update them intentionally;
- use chezmoi’s external-file mechanism if the project wants upstream files without vendoring, with a revision/hash and an update cadence ([chezmoi external files](https://www.chezmoi.io/user-guide/include-files-from-elsewhere/), [external format](https://www.chezmoi.io/reference/special-files/chezmoiexternal-format/));
- pin uv tool versions where the command is part of the baseline;
- keep third-party GitHub/Cargo/npm backends in the lockfile and inspect their source ownership before installation;
- do not expect Homebrew to provide a package lock: Homebrew’s current documentation says `brew bundle` is rolling and does not support a `Brewfile` lock file ([Homebrew Bundle and Brewfile](https://github.com/Homebrew/brew/blob/main/docs/Brew-Bundle-and-Brewfile.md)). Use `--no-upgrade` when an apply should converge without upgrading everything, but understand that it is not version pinning.

One separate correctness issue is already visible in the repository: Git enables required Git LFS filters, but `git-lfs` is not in the declared inventory. Either provision it or remove the required filter configuration; otherwise a repository using LFS can fail before any of the alternative-tool decisions matter.

## Proposed sequence

1. Measure current interactive startup and completion behavior.
2. Remove `zsh-history-substring-search`, then test Atuin’s `Ctrl-R` and Up-arrow behavior.
3. Replace the Oh My Zsh script with native `compinit` plus explicitly managed plugins, keeping syntax highlighting last.
4. Add/pin the mise lockfile and pin any uv tools that remain baseline dependencies.
5. Decide whether Bun, pnpm, HTTPie, Terraform/OpenTofu, and the two vault CLIs are truly global requirements; move the rest to project or optional install paths.
6. Re-measure startup and run the rendered chezmoi/shell checks.

