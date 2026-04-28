# Label Taxonomy

## Category Labels (exactly one required per issue)

Category labels describe _what kind of work_ the issue represents.

| Label           | Color            | When to apply                                                                       |
| --------------- | ---------------- | ----------------------------------------------------------------------------------- |
| `Bug`           | Red `#EB5757`    | Something is broken. Observed behavior differs from expected behavior.              |
| `Feature`       | Purple `#BB87FC` | New capability that doesn't exist yet.                                              |
| `Improvement`   | Blue `#4EA7FC`   | Enhancement to existing functionality. Better DX, performance, API surface.         |
| `Documentation` | Blue `#0075ca`   | Docs-only change: guides, API reference, migration notes, README.                   |
| `Spike`         | Red `#eb5757`    | Time-boxed research or exploration. Deliverable is a decision or writeup, not code. |
| `Security`      | Red `#d93f0b`    | Security vulnerability, audit finding, or hardening task.                           |
| `epic`          | Orange `#f2994a` | Parent issue grouping multiple sub-issues into a coherent workstream.               |

### Rules

- Every issue gets exactly **one** category label.
- `epic` can coexist with one other category label (e.g., `epic` + `Feature` for a feature epic).
- If unsure between `Feature` and `Improvement`: if it adds a new public API surface or capability, it's `Feature`. If it changes how an existing thing works, it's `Improvement`.

## State Labels (at most one per issue)

State labels describe _triage status_. They are orthogonal to Linear's workflow statuses (Backlog, Todo, In Progress, etc.). Not every issue needs a state label -- only issues that have been through triage or need attention.

| Label           | Color            | When to apply                                                                                                                        | When to remove                              |
| --------------- | ---------------- | ------------------------------------------------------------------------------------------------------------------------------------ | ------------------------------------------- |
| `needs-scoping` | Yellow `#f2c94c` | Issue quality score < 5 during triage. Missing Why, vague What, no acceptance criteria, or infodumped.                               | After the issue is rewritten to score >= 7. |
| `needs-info`    | Yellow `#f2c94c` | Issue is blocked waiting on external input: reporter clarification, another team's decision, vendor response.                        | When the information arrives.               |
| `ready`         | Green `#4cb782`  | Issue quality score >= 7, all metadata present (priority, milestone, category label). Fully specified, can be picked up.             | When issue moves to In Progress.            |
| `blocked`       | Red `#EB5757`    | Issue cannot progress due to a dependency on another issue, external event, or technical blocker. Must have a blocking relation set. | When the blocker is resolved.               |

### Rules

- At most **one** state label per issue. If an issue is both `needs-scoping` and `needs-info`, prefer `needs-info` (external blocker takes precedence).
- State labels are **managed by triage**. Don't apply them casually outside of a triage session.
- `ready` is a quality seal: it signals to the team "this is pick-up-able without further discussion."

## Release Labels (optional, additive)

| Label                | Color          | When to apply                                       |
| -------------------- | -------------- | --------------------------------------------------- |
| `released`           | Grey `#ededed` | Issue has shipped to production (latest channel).   |
| `released on @alpha` | Grey `#ededed` | Issue has shipped to alpha/prerelease channel only. |

## Special Labels (existing, keep as-is)

| Label             | When to apply                            |
| ----------------- | ---------------------------------------- |
| `Wiz-remediation` | Security findings from Wiz scanner.      |
| `UX and Design`   | Issues requiring design input or review. |

## Label Provisioning

State labels may not exist in a workspace yet. Before applying a state label, check if it exists via `list_issue_labels`. If missing, create it with `create_issue_label` using the colors defined above.

## Enforcement During Triage

When triaging an issue, check:

1. **Has category label?** If not, infer from title/description and propose one.
2. **Has conflicting category labels?** Flag and ask which to keep.
3. **Needs a state label?** Apply based on quality score and blocking status.
4. **Has stale state label?** E.g., `needs-info` but info has arrived (check comments). Propose removal or transition.
