# Setup alternatives: decision memo

This memo synthesizes the focused research in:

- [Zsh architecture and plugin alternatives](zsh-alternatives.md)
- [CLI tooling and shell alternatives](cli-tooling-alternatives.md)
- [Provisioning and system alternatives](provisioning-and-system-alternatives.md)

The linked reports contain the primary-source citations and detailed tradeoffs.

## Recommended direction

Keep the overall platform: chezmoi for home-directory state, mise for
cross-platform tools and runtimes, and Homebrew Bundle for macOS-only software.
The setup needs clearer ownership and reproducible updates more than it needs a
new provisioning system.

Replace Oh My Zsh with native Zsh plus a deliberately small plugin layer.
Antidote is the best-fit manager if convenient plugin updates are valued; pinned
chezmoi externals sourced directly are the smaller alternative. Preserve the
numbered fragment design and initialize completion exactly once.

Plugin disposition:

- Keep `zsh-syntax-highlighting`, loaded last.
- Keep `zsh-autosuggestions` only if inline suggestions are useful; it can use
  Atuin's history strategy.
- Remove `zsh-history-substring-search` unless its inline Up/Down behavior is
  specifically preferred over Atuin.
- Remove the Oh My Zsh `git` and `virtualenv` plugins; local Git helpers,
  Starship, and mise already own their useful behavior.
- Keep the `macos` and `command-not-found` helpers only if individual commands
  are demonstrably used and their platform dependencies are provisioned.

Before expanding the inventory, add and commit a mise lockfile, pin shell plugin
revisions, and make Homebrew upgrades an explicit maintenance action rather
than a side effect of `chezmoi apply`.

## Inventory decisions to make

- Choose whether Bun and pnpm are genuine global defaults or project-level
  choices alongside Node LTS.
- Choose Terraform or OpenTofu according to actual provider/team constraints;
  avoid an unpinned global tool with no declared use.
- Either provision Git LFS or remove the required global LFS filter.
- Decide whether both Bitwarden CLI and 1Password CLI belong in the baseline.
- Keep HTTPie only if it earns a global Python-tool installation over `curl`.

The existing Git/search/navigation stack is coherent. Keep `ripgrep`, `fd`,
`fzf`, `bat`, `eza`, `zoxide`, Atuin, Starship, tmux, sesh, delta, difftastic,
Mergiraf, git-spice, and `gh` unless usage evidence says otherwise.

## Worth a bounded trial

- Jujutsu in one colocated Git repository; do not replace Git or git-spice yet.
- Ghostty if a native, file-configured terminal would replace iTerm2; WezTerm if
  cross-platform configuration and its multiplexer are the actual goal.
- Ice only if Hidden Bar no longer solves the menu-bar/notch problem.
- Colima as a documented OrbStack fallback, not a second default runtime.
- Tailscale SSH for an explicit tailnet-only host class.

## Do not add without a concrete requirement

- Home Manager/nix-darwin: revisit for generation rollback or stronger
  whole-machine reproducibility, not as a dotfile cleanup.
- Ansible: revisit when remote machines become a fleet needing coordinated
  privileged changes.
- `direnv`, `just`, Zellij, and additional “modern Unix” replacements: current
  tools already cover their main roles.
- Apple's `container`: promising, but still pre-1.0 and restricted to recent
  Apple-silicon/macOS combinations.

## Suggested implementation order

1. Capture current shell startup time, bindings, completion behavior, and the
   Oh My Zsh aliases actually used.
2. Remove redundant plugins, then replace Oh My Zsh with native completion and
   pinned plugin loading.
3. Add mise locking and intentional update commands.
4. Make Brew Bundle use `--no-upgrade`; gate Docker Desktop removal behind host
   policy and separate editor configuration from macOS defaults.
5. Resolve the small inventory decisions above.
6. Trial optional replacements one at a time, without adding them to the shared
   baseline until they displace an existing tool.
