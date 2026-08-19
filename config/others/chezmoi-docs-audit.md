# Chezmoi documentation audit

Reviewed against the current official chezmoi documentation on 2026-08-19. This is a documentation baseline for the repository-wide review, not an implementation plan.

## Repository-specific conclusions

- The root-level `.chezmoiroot` containing `dotfiles` is the intended way to keep non-home material (`skills/`, `tools/`, documentation, and project automation) outside the source state. Chezmoi reads this file before everything else; all other source-root special files belong under `dotfiles/`, as they currently do. [`.chezmoiroot` reference](https://www.chezmoi.io/reference/special-files/chezmoiroot/) and [custom source directory guide](https://www.chezmoi.io/user-guide/advanced/customize-your-source-directory/)
- Source names in this repository use valid attributes: `dot_`, `private_`, `.tmpl`, and the `run_{once,onchange}_{before,after}_` combinations are recognized, and attribute order matters. Hidden non-`.chezmoi*` entries in source state are ignored by default. [Source-state attributes](https://www.chezmoi.io/reference/source-state-attributes/)
- The OS conditions in `dotfiles/.chezmoiignore` are sound: the file is always templated, and patterns match **target paths**, hence `.config/homebrew/Brewfile` rather than its encoded source name. Subdirectory ignore files would have only local scope. [`.chezmoiignore` reference](https://www.chezmoi.io/reference/special-files/chezmoiignore/)
- `dotfiles/.chezmoidata/host.toml` is a reasonable shared default for `ephemeral_host`; machine-local `[data]` in `chezmoi.toml` overrides `.chezmoidata`. Data files merge at the root in lexical order, dictionaries merge recursively, and lists are replaced rather than merged. `chezmoi data` is the authoritative way to inspect the effective result. [Templating and data precedence](https://www.chezmoi.io/user-guide/templating/#template-data) and [`.chezmoidata/` reference](https://www.chezmoi.io/reference/special-directories/chezmoidata/)
- The package inventory plus `run_onchange_` installers follows chezmoi's official pattern for approximating declarative package management. Including rendered inventory hashes in script comments is also the documented way to make another file/data change affect a script hash. [Declarative package guide](https://www.chezmoi.io/user-guide/advanced/install-packages-declaratively/) and [script guide](https://www.chezmoi.io/user-guide/use-scripts-to-perform-actions/#run-a-script-when-the-contents-of-another-file-changes)
- `.chezmoitemplates/lib.sh` is an appropriate home for a reusable template. Every file beneath `.chezmoitemplates/` is templated regardless of suffix. [Templating guide](https://www.chezmoi.io/user-guide/templating/#using-chezmoitemplates)

## Script semantics to preserve during refactoring

Chezmoi first reads source and destination state and computes the entire target state. It then runs all `run_before_` scripts alphabetically, applies target entries alphabetically, and finally runs all `run_after_` scripts alphabetically. Attributes are stripped before sorting. A `run_before_` script must not mutate source or destination state; doing so has undefined behavior. An `after_` script may depend on managed files or externals having been applied. [Application order](https://www.chezmoi.io/reference/application-order/)

The numeric prefixes in this repository therefore order scripts only within their phase. In particular, `run_once_before_40-migrate-gitconfig` legitimately sees the old destination before managed files are written, while mise and Brew bundle installers correctly use `after_` because they consume generated config files.

The names are slightly misleading unless their exact state behavior is kept in mind:

- Plain `run_` executes on every apply.
- `run_onchange_` executes when the rendered content changes since that **same entry name** last succeeded.
- `run_once_` executes once per unique rendered-content SHA-256, even if the successful identical content previously had another filename. Editing a `run_once_` script creates a new content hash and makes it eligible again.
- Only successful runs are recorded. A deliberate `exit 0` records the current version as done; a non-zero exit is retried on a later apply.
- All variants should remain idempotent. Official guidance says scripts break the declarative model and should be used sparingly.

These details matter for the repository's manual/interactive steps. For example, a `run_once_` script that skips authentication because there is no TTY and exits successfully will not retry automatically; that is acceptable only when its printed manual instruction is the intended terminal state. [Script guide](https://www.chezmoi.io/user-guide/use-scripts-to-perform-actions/) and [target types](https://www.chezmoi.io/reference/target-types/#scripts)

The root-level script files are valid. If a refactor aims to reduce source-root noise, `.chezmoiscripts/` is the native organizational alternative; scripts there retain normal attributes and ordering without creating a destination directory. [Special directories](https://www.chezmoi.io/reference/special-directories/) and [script guide](https://www.chezmoi.io/user-guide/use-scripts-to-perform-actions/)

## Native mechanisms worth considering

- For downloaded files, archives, or cloned trees such as Oh My Zsh and plugins, `.chezmoiexternal.{toml,yaml,json}` is the native alternative to `curl`/`git clone` scripts. It supports checksums, archive filtering and stripping, exact directories, `git-repo`, and refresh periods. The default refresh period is zero (cached indefinitely) unless `--refresh-externals` is used, so pin versions/checksums or set an intentional refresh policy. Externals are applied during the update phase, so only `run_after_` scripts should depend on them. [External source reference](https://www.chezmoi.io/reference/special-files/chezmoiexternal-format/)
- Add `.chezmoiversion` if the repository depends on current features or behavior. Chezmoi processes it before applying anything and rejects an older executable; this is safer than failing midway on an unsupported construct. [Special-files processing order](https://www.chezmoi.io/reference/special-files/)
- A `.chezmoi.$FORMAT.tmpl` under `dotfiles/` can generate machine-local config during `init` or `apply --init`. It is the native place to prompt for durable per-machine choices such as `ephemeral_host`, instead of requiring manual config editing. [Special-files processing order](https://www.chezmoi.io/reference/special-files/) and [`init`](https://www.chezmoi.io/reference/commands/init/)
- If script bodies dominate `chezmoi diff`/`status`, config can set `diff.exclude = ["scripts"]` and `status.exclude = ["scripts"]`. This improves signal without changing execution. [Script guide](https://www.chezmoi.io/user-guide/use-scripts-to-perform-actions/#dont-show-scripts-that-would-run-in-chezmoi-diffchezmoi-status)

No official documentation reviewed here marks this repository's source attributes, `.chezmoiroot`, `.chezmoiignore`, data format, or script forms as deprecated. The likely modernization is therefore structural (fewer imperative installers, native externals/config generation, and a minimum-version guard), not a syntax migration.

## Secrets and encryption baseline

No private key material should be committed as an ordinary template or data value. Chezmoi supports `age`, GPG, and transparent git encryption; encrypted source entries use `encrypted_`, and `chezmoi add --encrypt`/`chezmoi edit` handle encryption and decryption. Age has builtin support when the external command is absent, but builtin age does not support passphrases, symmetric encryption, or SSH identities. [Encryption overview](https://www.chezmoi.io/user-guide/encryption/) and [age guide](https://www.chezmoi.io/user-guide/encryption/age/)

For secrets that already live in a password manager, prefer chezmoi's password-manager/template functions over copying the secret into repository data. If that manager must exist before source-state evaluation, the documented bootstrap point is `hooks.read-source-state.pre`, not a normal `run_before_` script, because normal scripts run only after target-state computation. [Password-manager bootstrap guide](https://www.chezmoi.io/user-guide/advanced/install-your-password-manager-on-init/)

## Validation and operating workflow

The current `scripts/check-chezmoi` use of `chezmoi execute-template -S .` is aligned with the official template-testing command and correctly targets this checkout despite `.chezmoiroot`. The audit should extend, rather than replace, that check with native state-level commands:

1. `chezmoi data -S .` — inspect effective template data and catch merge/override surprises. [Templating guide](https://www.chezmoi.io/user-guide/templating/#template-data)
2. `chezmoi apply -S . --dry-run --verbose` — show the complete planned filesystem work without modifying the destination; dry-run does not execute scripts. [`apply`](https://www.chezmoi.io/reference/commands/apply/) and [global flags](https://www.chezmoi.io/reference/command-line-flags/global/)
3. `chezmoi verify -S . --exclude=scripts` — CI-friendly exit status: zero only when managed targets match target state. [`verify`](https://www.chezmoi.io/reference/commands/verify/)
4. `chezmoi execute-template -S . < file.tmpl` — isolate template syntax/rendering failures. [Template testing](https://www.chezmoi.io/user-guide/templating/#testing-templates)

For a new machine, the documented entrypoint is `chezmoi init --apply <repo>`, which clones/initializes the source, generates config from `.chezmoi.*.tmpl` if present, and then applies. For an existing machine, `chezmoi update` pulls (Git by default) and applies by default; use `chezmoi diff` or `apply --dry-run --verbose` before mutating when reviewing risk. [`init`](https://www.chezmoi.io/reference/commands/init/), [quick start](https://www.chezmoi.io/quick-start/), and [configuration `update.apply`](https://www.chezmoi.io/reference/configuration-file/variables/#update)

When testing repeated script behavior, avoid casually resetting all persistent state: `run_onchange_` and `run_once_` use different state buckets. The documented targeted resets are `entryState` for onchange and `scriptState` for once. [Script-state reset](https://www.chezmoi.io/user-guide/use-scripts-to-perform-actions/#clear-the-state-of-all-run_onchange_-and-run_once_-scripts)
