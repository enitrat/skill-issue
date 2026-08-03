# Label Taxonomy

Division of labor: **statuses** say where work is in the lifecycle, **relations** say why it's blocked, **labels** say what kind of work it is and where it lives. Labels never duplicate what a status or relation already expresses.

## Category labels (exactly one per issue)

| Label | Color | When to apply |
|---|---|---|
| `Bug` | Red `#EB5757` | Observed behavior differs from expected behavior. |
| `Feature` | Purple `#BB87FC` | New capability that doesn't exist yet. |
| `Improvement` | Blue `#4EA7FC` | Enhancement to existing functionality: DX, performance, API surface, polish. |
| `Documentation` | Blue `#0075ca` | Docs-only change: guides, API reference, migration notes. |
| `Spike` | Red `#eb5757` | Time-boxed research. Deliverable is a written decision, not code. "No change" is a valid outcome. |
| `Security` | Red `#d93f0b` | Vulnerability, audit finding, or hardening task. |

Tie-breaker: adds a new public capability → `Feature`; changes how an existing thing works → `Improvement`.

## Module labels (at most one — where in the product)

| Label | When to apply |
|---|---|
| `module:platform` | Cross-cutting infra: auth, wallet, tx lifecycle, decryption UX, design system, analytics, compliance, routing. |
| `module:portfolio` | Home, balances, shield/unshield, transfer, onramp. |
| `module:earn` | Yield vaults, Morpho integration, batcher, deposits/redemptions. |
| `module:swap` | cToken-to-cToken exchange, solver/RFQ, quote flow. |
| `module:activity` | Unified tx history, decryptable receipts, shareable links. |

## Area labels (additive — what expertise it touches)

| Label | When to apply |
|---|---|
| `area:ux` | Needs design input, UX review, or visual/design-system work. |
| `area:devx` | Tooling, CI, monorepo setup, linting, testing infra. |
| `area:sdk` | Involves Zama SDK consumption, dogfooding, or SDK-facing integration. |

## State label (the only one)

| Label | When to apply | When to remove |
|---|---|---|
| `needs-info` | Waiting on external input: reporter clarification, another team's decision, vendor response. Legal in any status before In Progress. | When the information arrives. |

## Retired labels — do not apply, migrate on sight

Migration executed 2026-08-03. If any resurface (restored issues, imports), re-migrate:

| Retired | Replacement |
|---|---|
| `Enhancement` | `Improvement` |
| `ui`, `ui-debt` | `area:ux` (+ infer a category label if none remains) |
| `to-refine` | `needs-scoping` was the old mapping; now → status `Shaping` or `Backlog` |
| `ready` | Status `Ready` (gate in [SKILL.md](../SKILL.md)) |
| `needs-scoping` | Status `Backlog`/`Shaping` |
| `blocked` | Blocking **relation** only |
| `epic` | Project, or plain parent issue with sub-issues ([PROJECT-WRITING.md](PROJECT-WRITING.md)). Grandfathered on existing epics until promoted. |
| `KR 1.1` | Project → initiative link |

## Provisioning

Before applying a label, check it exists via `list_issue_labels`; create missing canonical labels with `create_issue_label` using the colors above. Never create labels outside this taxonomy without asking.

## Enforcement during triage

1. **Exactly one category label?** Infer from title/description and propose.
2. **Module label present** where the issue clearly belongs to one module? Propose it.
3. **Retired label present?** Migrate per the table.
4. **Stale `needs-info`?** Check comments — if the answer arrived, propose removal and a status move.
5. **`blocked`-style prose** ("waiting on X") without a relation? Propose the relation.
