# Provisioning and system alternatives

Reviewed 2026-08-19 against first-party documentation and project-owned source
repositories. This is a fit assessment for this repository, not a catalogue of
every dotfiles or developer-environment tool.

## Recommendation in one paragraph

Keep the current three-way split: chezmoi owns files and small, idempotent
orchestration; Homebrew Bundle owns macOS applications and the few macOS-only
formulae; mise owns cross-platform developer tools and runtimes. The highest
value refactor is to make those boundaries explicit, stop `brew bundle` from
upgrading unrelated software during an apply, and introduce intentional mise
version locking. Do not migrate the whole repository to Nix or Ansible yet.

Home Manager/nix-darwin are credible alternatives when reproducibility or a
multi-machine fleet becomes the primary problem, but they bring a second
configuration language, a Nix installation, generation ownership, and a much
larger migration surface. Ansible is useful for remote fleet orchestration, not
as a better local dotfile manager for this personal setup.

## What the repository currently does well

The repository has a useful source-of-truth shape:

| Concern | Current owner | Assessment |
| --- | --- | --- |
| Dotfiles and rendered config | chezmoi | Keep. Its template data and apply ordering match the repo's multi-OS needs. |
| macOS casks/formulae | generated Brewfile + `brew bundle` | Keep, but opt out of implicit upgrades during apply. |
| CLI tools and runtimes | generated mise config | Keep, but replace unbounded `latest` defaults with ranges or a lockfile. |
| macOS defaults | direct `defaults`/PlistBuddy script | Keep for a small, documented set of stable preferences; do not add a second defaults DSL. |
| Remote access | OpenSSH + Tailscale + optional Mosh | Keep. Consider Tailscale SSH as an explicit opt-in for tailnet-only hosts. |
| Container runtime | OrbStack on macOS | Keep for now; make Docker Desktop removal an explicit host policy. |

The main architectural problem is not the choice of tools. It is that some
scripts currently perform policy decisions (remove Docker Desktop, modify
editor JSON, download terminal integration) that are not clearly part of the
package or dotfile contract.

## Alternatives assessed

### Home Manager and nix-darwin — strong alternative, high migration cost

Home Manager can run standalone on macOS and non-NixOS Linux, and its flake
workflow produces a generation that is activated with `home-manager switch`.
The manual also documents collision handling and backups for unmanaged files.
See the [standalone installation guide](https://home-manager.dev/manual/unstable/installation/standalone.html),
[flake-based standalone setup](https://home-manager.dev/manual/unstable/nix-flakes/standalone.html),
and [collision/backup guidance](https://home-manager.dev/manual/unstable/usage/dotfiles.html).

`nix-darwin` extends that model to macOS system configuration and can manage
Homebrew from a Nix module. Its own README recommends flakes and applies system
changes with `darwin-rebuild switch`; see the [nix-darwin README](https://github.com/nix-darwin/nix-darwin#readme)
and [Homebrew module](https://github.com/nix-darwin/nix-darwin/blob/master/modules/homebrew.nix).

Fit for this repo:

- Benefits: generation-based rollback, reproducible package inputs, a single
  language for user configuration and (with nix-darwin) macOS system settings.
- Costs: Nix/Lix installation and storage, Nix language/module learning curve,
  different symlink/collision semantics, root-owned system activation on
  macOS, and duplicate ownership if Home Manager and chezmoi manage the same
  path.
- Reversibility: good if trialled on one disposable Linux host or in a
  separate profile; poor if it is introduced path-by-path while chezmoi still
  writes those same paths.

Decision: do not replace chezmoi now. Revisit if either (a) several machines
must be byte-for-byte reproducible, or (b) macOS system services/defaults
become a major part of the repository. If trialled, give Home Manager a
non-overlapping subtree first (for example a new tool-specific config), and
choose one owner per target path before expanding it.

### Ansible — useful for a remote fleet, unnecessary for this laptop

Ansible's `ansible.builtin.package` abstracts over the detected package
manager, which is useful across apt/dnf/pacman hosts. The official module
documentation explicitly warns that package names still vary by package
manager and that the abstraction only covers their common argument set; see
the [package module documentation](https://docs.ansible.com/projects/ansible-core/devel/collections/ansible/builtin/package_module.html).

Fit for this repo:

- Benefits: inventory, host groups, privilege escalation, remote execution,
  service management, and better fleet-level reporting than a local shell
  script.
- Costs: another controller/inventory/playbook lifecycle; package-name
  mapping remains; it is heavier than needed for one personal macOS machine
  and a few ad-hoc Linux hosts.
- Reversibility: high when used as a separate `remote/` playbook; low value if
  it replaces the same local dotfiles that chezmoi already applies.

Decision: do not add Ansible to the base setup. Consider a small, separate
Ansible playbook only if remote hosts become numerous or need coordinated
server changes. Keep chezmoi as the user-home convergence tool on those hosts.

### Homebrew Bundle — keep, with a safer apply policy

Homebrew describes Bundle as a declarative interface for formulae, casks,
Mac App Store apps, and several language/package ecosystems. It installs
missing dependencies and, by default, upgrades outdated ones. It also has no
Brewfile lockfile concept. See the [official Brew Bundle documentation](https://docs.brew.sh/Brew-Bundle-and-Brewfile)
and the [brew manpage](https://docs.brew.sh/Manpage#bundle).

That is a good match for the macOS-only part of this repo, but the current
`brew bundle --file ...` in a chezmoi apply can upgrade every declared cask or
formula as a side effect of applying an unrelated dotfile change.

Recommended changes:

1. Run `brew bundle --no-upgrade` (or set
   `HOMEBREW_BUNDLE_NO_UPGRADE=1`) from provisioning. Keep upgrades as an
   explicit maintenance command.
2. Do not add `brew bundle cleanup` to normal apply. Cleanup removes supported
   dependencies not listed in the selected Brewfile and is appropriate only
   when the user explicitly wants the machine reconciled to that inventory.
3. Consider a `mas` entry for App Store-only software such as Amphetamine,
   but only if the App Store login requirement is acceptable and the entry is
   tested on a fresh host. Homebrew documents `mas` support, but it does not
   make App Store authentication non-interactive.
4. Keep the package inventory as the source of truth; do not maintain a second
   handwritten Brewfile.

Migration cost: minimal and reversible. This is the only alternative assessed
here that should be adopted immediately.

### mise — keep and make the current design reproducible

mise already covers the repository's strongest use case: cross-platform CLIs,
runtimes, environment variables, and project tasks. Its current documentation
supports loose selectors such as `node@22` together with a committed
`mise.lock`, exact versions, checksums, download URLs, and a strict locked mode.
See the [mise walkthrough](https://mise.jdx.dev/walkthrough.html),
[lockfile guide](https://mise.jdx.dev/dev-tools/mise-lock.html), and
[lockfile settings](https://mise.jdx.dev/configuration/settings.html#lockfile).

The current generated config uses `latest` for most tools. That is convenient
for a personal rolling setup but makes a new machine depend on whatever was
released at apply time. Some backends (notably npm and cargo) have weaker
lockfile metadata than GitHub/aqua/http backends, so locking improves the
situation without making every package equally reproducible.

Recommended migration:

- First replace `latest` with meaningful ranges (`node = "lts"`, major
  versions, or explicit versions) for runtimes where compatibility matters.
- Generate and commit a global mise lockfile for the architectures actually
  supported by this repo, then use locked installs in CI/bootstrap where
  reproducibility matters. Verify the generated path and platform entries
  against the installed mise version before wiring it into chezmoi; global
  config lockfiles differ from project-local `mise.lock` files.
- Keep the current `packages.toml` inventory, but document that changes to the
  inventory require an intentional lock refresh.

Migration cost: low to medium. It preserves the current shell activation and
package placement model, and rollback is simply removing the lockfile or
restoring the previous selectors.

## macOS-specific alternatives and additions

### macOS defaults: retain the native interface

Apple documents `defaults` as the supported command-line utility for viewing or
modifying the user defaults system, while warning against editing the backing
preference files directly. Apple also notes that defaults are local to the
current device rather than a cross-device configuration store. See [Apple's
UserDefaults documentation](https://developer.apple.com/documentation/foundation/userdefaults).

The current direct `defaults`/PlistBuddy script is therefore reasonable for a
small set of stable preferences. The improvement is scope: move Cursor/VS Code
JSON edits into managed editor files or a separate opt-in script, and keep
system defaults separate from application configuration. A third-party
"macOS defaults" wrapper would add another translation layer without solving
the underlying preference-cache and version-drift problems.

### Terminal: iTerm2 versus a cross-platform terminal

The repository currently downloads iTerm2 shell integration once. That is a
mutable external download and only pays off when iTerm2 is the selected local
macOS terminal.

Two credible trials are:

- [Ghostty](https://ghostty.org/docs) has native macOS and Linux applications,
  GPU rendering, built-in shell integration, and a text configuration file.
  The project supplies official macOS binaries, while Linux distribution
  packages are a mix of distro/community packaging; its `xterm-ghostty`
  terminfo can also require server-side handling over SSH. See the [Linux
  installation notes](https://ghostty.org/docs/linux) and [terminfo guidance](https://ghostty.org/docs/help/terminfo).
- [WezTerm](https://wezterm.org/) is cross-platform, includes a built-in
  multiplexer/SSH CLI, and has pre-built installation paths for macOS and many
  Linux distributions. Its configuration is Lua, and its own docs call out
  PATH and terminfo concerns when launched from the macOS GUI. See the [macOS
  install guide](https://wezterm.org/install/macos.html), [Linux install
  guide](https://wezterm.org/install/linux.html), and [configuration guide](https://wezterm.org/config/files.html).

Decision: do not install both. Keep iTerm2 if its macOS integration is part of
the daily workflow; otherwise trial Ghostty for a native, lightweight local
terminal or WezTerm if cross-platform terminal configuration and an embedded
multiplexer matter more. In either case, manage the chosen config as a pinned
external or a normal chezmoi file, not as an unverified one-time `curl`.

### Container runtime: keep OrbStack; make removal policy explicit

OrbStack's official docs describe it as a Docker-compatible macOS/Linux machine
and container runtime with Compose, Kubernetes, SSH, and file integration. See
the [OrbStack overview](https://docs.orbstack.dev/).

The most credible lower-cost/reversible alternative is [Colima](https://github.com/abiosoft/colima#readme):
its project README documents macOS and Linux support, Docker/containerd/Incus
runtimes, Kubernetes, multiple instances, and MIT licensing. It is more
terminal-first and requires choosing/configuring a VM, so switching changes
runtime state even though Docker clients remain familiar.

Apple's new [`container` tool](https://github.com/apple/container#readme) is
worth watching, especially for Apple-silicon Macs on macOS 26: it consumes OCI
images and provides lightweight VM-backed containers and persistent container
machines. The project explicitly says it is still pre-1.0 and only supports
Apple silicon/macOS 26, so it is not a base provisioning dependency yet.

Recommendation: retain OrbStack, but gate the Docker Desktop uninstall behind
an explicit host policy such as `container_runtime = "orbstack"`. A package
apply should not silently remove a competing runtime on every machine. Add
Colima only as a documented fallback or alternate host profile, not alongside
OrbStack by default.

### Menu-bar utility: Hidden Bar is adequate; Ice is a targeted trial

Hidden Bar is a narrow dependency that hides/reveals menu-bar items. If the
actual need is notch-aware layout, grouping, spacing, profiles, or search,
[Ice](https://github.com/jordanbaird/Ice#readme) is a more capable open-source
candidate and documents a Homebrew cask plus macOS 14+ requirements. Its README
also says it remains in active development, so it adds more permission and
upgrade surface than Hidden Bar.

Decision: do not replace Hidden Bar solely because Ice has more features. Trial
Ice manually if menu-bar spacing or grouping remains a real problem, then
choose one. Do not provision both.

## Remote access and networking

The current Tailscale + OpenSSH + optional Mosh combination is defensible:

- [Tailscale SSH](https://tailscale.com/docs/features/tailscale-ssh) can
  centralize authentication and authorization using tailnet policy, without
  modifying ordinary SSH keys/config for non-tailnet connections. It changes
  the trust model and requires policy/admin setup, so it should be an explicit
  opt-in host mode rather than an automatic bootstrap action.
- [Mosh](https://mosh.org/) remains a useful complement, not a replacement for
  SSH: it roams between IPs and survives intermittent connectivity, but needs
  the client and server and uses UDP (normally ports 60000–61000). Keep it in
  the Linux/macOS baseline only where the network policy permits that UDP
  range.

No replacement is recommended. The practical additions are documentation and
host data: distinguish ordinary SSH, Tailscale SSH, and Mosh hosts, and avoid
assuming that a tailnet or UDP access exists on every remote machine.

## Suggested sequence

1. Change Brew Bundle provisioning to `--no-upgrade`; make Docker Desktop
   removal an explicit host policy; separate editor JSON changes from system
   defaults.
2. Pin important mise ranges and generate a tested global lockfile for the
   supported macOS/Linux architectures.
3. Replace the mutable iTerm2 download with a pinned managed external, or make
   terminal integration conditional on the selected terminal.
4. If needed, manually trial one terminal and one menu-bar alternative; do not
   add both alternatives to the baseline.
5. Revisit Home Manager/nix-darwin only after a concrete requirement for
   generation rollback or whole-system reproducibility appears. Revisit
   Ansible only when remote-host count or fleet policy justifies it.

## Sources

All sources above are first-party project documentation, official manuals, or
the owning project's source repository. They were checked on 2026-08-19.
