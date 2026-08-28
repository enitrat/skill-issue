# Labels

Statuses say where work is, relations say why it waits, the assignee says who owns it now, labels say what kind of work it is and where it lives. A label never duplicates a status, relation or assignee.

## Category (exactly one)

| Label | When |
|---|---|
| `Bug` | Observed behaviour differs from expected |
| `Feature` | New capability |
| `Improvement` | Existing capability changes: DX, performance, API surface, polish |
| `Documentation` | Docs-only |
| `Spike` | Time-boxed research; deliverable is a written decision |
| `Security` | Vulnerability, audit finding, hardening |

Tie-break: adds a public capability → `Feature`; changes how one works → `Improvement`.

## Module (at most one)

| Label | Where |
|---|---|
| `module:platform` | Cross-cutting: auth, wallet, tx lifecycle, decryption UX, design system, analytics, compliance, routing |
| `module:portfolio` | Home, balances, shield/unshield, transfer, onramp |
| `module:earn` | Vaults, Morpho, batcher, deposits and redemptions |
| `module:swap` | cToken exchange, solver/RFQ, quote flow |
| `module:activity` | Transaction history, receipts, shareable links |

## Area (additive)

| Label | Meaning |
|---|---|
| `area:ux` | The issue passes through **Design shaping**: it has screens, copy, or design-system work. Drives the Design block and readiness item 8 |
| `area:devx` | Tooling, CI, monorepo, linting, test infra |
| `area:sdk` | Zama SDK consumption or SDK-facing integration |

## State label (the only one)

`needs-info`: waiting on external input (reporter, another team, vendor). Legal in any status before In Progress; removed when the answer arrives.

## Retired — migrate on sight

Still present in the workspace as of 2026-08-28; the migration of 2026-08-03 did not delete them.

| Retired | Replacement |
|---|---|
| `Enhancement` | `Improvement` |
| `ui`, `ui-debt` | `area:ux` (+ a category label if none remains) |
| `to-refine`, `needs-scoping` | Status `Backlog` or `Product shaping` |
| `ready` | Status `Ready` |
| `blocked` | A `blockedBy` relation |
| `epic` | Project, or parent issue with sub-issues |

## Enforcement

1. Exactly one category label; propose from title and description.
2. Module label where the issue clearly belongs to one.
3. Retired label → migrate.
4. `needs-info` with the answer in comments → remove and propose the status move.
5. "Waiting on X" in prose without a relation → propose the relation.
6. Check a label exists with `list_issue_labels` before applying; create canonical ones with `create_issue_label`; ask before creating anything outside this taxonomy.
