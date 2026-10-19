# Labels

Labels say what kind of work an issue is and where it lives. A label never
duplicates a status, a relation or the assignee.

**Category (exactly one):** `Bug` · `Feature` (new capability) · `Improvement`
(changes an existing one) · `Documentation` · `Spike` (deliverable is a decision) ·
`Security`.

**Module (at most one):**

| Label | Where |
| --- | --- |
| `module:platform` | Auth, wallet, tx lifecycle, decryption, design system, analytics, compliance |
| `module:portfolio` | Home, balances, shield/unshield, transfer, onramp |
| `module:earn` | Vaults, Morpho, batcher, deposits, redemptions |
| `module:swap` | cToken exchange, RFQ, quotes |
| `module:activity` | History, receipts, shareable links |

**Area (additive):** `area:ux` (screens, copy or design-system work) ·
`area:devx` (tooling, CI, tests) · `area:sdk` (Zama SDK integration).

**State:** `needs-info` while waiting on someone outside the team; removed when the
answer arrives.

**Retired, migrate on sight:** `Enhancement` → `Improvement` · `ui`, `ui-debt` →
`area:ux` · `to-refine`, `needs-scoping`, `ready` → a status · `blocked` → a
`blockedBy` relation · `epic` → a project or parent issue.

Check a label exists with `list_issue_labels` before applying. Ask before creating
one outside this list.
