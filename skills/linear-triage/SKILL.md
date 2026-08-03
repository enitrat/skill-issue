---
name: linear-triage
description: Linear project management — the hierarchy (initiative → project → milestone → parent → leaf), status gates, labels, estimates. Use whenever the user mentions Linear or an issue ID like SUP-123 — triaging or auditing a board, writing or reviewing an issue, creating or decomposing a project, drafting a project update, or fixing metadata.
---

# Linear Triage

Manage and triage work in Linear using `mcp__claude_ai_Linear__*` MCP tools. All mutations follow **prepare → confirm → execute**: present proposed changes, wait for approval, then apply.

## Reference docs

- [TRIAGE.md](references/TRIAGE.md) — status gates, health dashboard, batch operations, dependency audit
- [ISSUE-WRITING.md](references/ISSUE-WRITING.md) — U-shaped issue template, word caps, voice rules, quality scoring
- [PROJECT-WRITING.md](references/PROJECT-WRITING.md) — project briefs, milestones, decomposition, project updates
- [LABELS.md](references/LABELS.md) — label taxonomy and enforcement rules

## The hierarchy (constitution)

The planning system maintains one unbroken chain: **evidence → outcome → project → deliverable → leaf**. Every object below has a distinct job; putting content at the wrong level is a triage finding.

| Object | Is | Must have | Must never be |
|---|---|---|---|
| **Initiative** | A KR or strategic effort connecting projects | Owner, target, ≥1 project once work is committed | A label; a quarter-themed grab bag |
| **Project** | A committed, bounded outcome | Brief ([PROJECT-WRITING.md](references/PROJECT-WRITING.md)), lead, target date, stage milestones, ≥1 initiative | Immortal; a team name; an "improvements" bucket |
| **Candidate project** | An opportunity with evidence, no commitment | Problem statement, evidence links, open questions. Stays in project state `Backlog` | A disguised backlog of every request |
| **Milestone** | A stage of the project lifecycle with exit evidence | Stage outcome + what proves it | A component/layer name ("backend") |
| **Parent issue** | One coherent deliverable needing several leaves | Real **sub-issues** (never `relatedTo` links), its own Why/What | A project in disguise (see boundary rule) |
| **Leaf issue** | Smallest delegable, verifiable unit | Passes the readiness test (below) | A layer slice ("add API", "add tests") |

**Project vs parent issue boundary:** multiple people, OR more than ~2 weeks of work, OR deserves its own status reporting → **project**. One coherent deliverable that decomposes into leaves → **parent issue**. The `epic` label is retired; existing labeled epics are grandfathered until promoted to projects.

**Ambient work** (small one-off bugs, polish) lives in the **team backlog with no project**, fully labeled and prioritized. Do not create or feed bucket projects. `Super App — Continuous Enhancements` is a known, marked antipattern kept open for logistics — never add scoped work to it.

## Status state machine

Statuses are executable policy, not decoration. A transition is only legal when its entry gate holds.

| Status | Entry gate |
|---|---|
| **Triage** | Raw intake. Evidence preserved verbatim (source link, reporter, where seen). |
| **Backlog** | Acknowledged: category + module label, priority, source recorded, deduped. Routed to a project or explicitly parked in team backlog. |
| **Shaping** | Someone is actively specifying it. Spec drafted but not approved. |
| **Ready** | Passed the **readiness test**. Replaces the old `ready` label. |
| **In Progress** | Claimed by a person. Agent-executed work stays assigned to its accountable human. |
| **In Review** | PR open. Review covers intent and acceptance criteria, not only the diff. |
| **Done** | Verified per the issue's acceptance criteria. If a source/stakeholder is linked, they were notified or explicitly need none. |
| **Canceled / Duplicate** | State the reason / link the original. |

### The readiness test (gate to Ready)

An issue may enter Ready only if **all** hold:

1. One primary objective; no unresolved product decision hidden inside.
2. Written to the U-shaped template in [ISSUE-WRITING.md](references/ISSUE-WRITING.md); quality score ≥ 7.
3. Scope and non-goals explicit.
4. Verification stated: commands, observable behavior, or evidence that will prove it done.
5. Dependencies exist as Linear **relations** (blocks/blocked-by), not prose.
6. **Estimate set and human-confirmed** (see estimates policy).
7. Milestone assigned, when the project has milestones.

## Estimates policy

Estimates (points) are required at the Ready gate. **Agents never set estimates silently**: propose the estimate during the confirm step and mark it as needing the user's blessing. An unconfirmed estimate blocks the Ready transition.

## Blocked and waiting

- Blocking is expressed by **relations only**. The `blocked` label is retired — a label rots; a relation clears itself.
- `needs-info` is the one surviving state label: waiting on external input (reporter, another team, vendor). It is orthogonal to status and legal in any state before In Progress.

## Invocation

**Triage requests** → [TRIAGE.md](references/TRIAGE.md): "Triage the board", "What needs attention?", "Review SUP-42", "Check dependencies on the launch milestone".

**Issue creation** → [ISSUE-WRITING.md](references/ISSUE-WRITING.md): "Create a ticket for X", "Write up the auth bug".

**Project creation / decomposition / updates** → [PROJECT-WRITING.md](references/PROJECT-WRITING.md): "Create a project for the credential refactor", "Decompose this into sub-issues", "Draft the weekly project update".

**Label/metadata questions** → [LABELS.md](references/LABELS.md).

## Workflow: create issue

1. Clarify: what problem, what outcome, what's out of scope, what evidence exists.
2. Draft per [ISSUE-WRITING.md](references/ISSUE-WRITING.md) (pick the right variant: feature/improvement, bug, spike).
3. Score against the quality checklist; state the score.
4. Propose metadata: priority, category + module labels, milestone, estimate (flagged for human confirmation), relations.
5. Present the full issue for confirmation before `save_issue`. Status per the state machine — usually Backlog or Shaping; Ready only if the gate holds after confirmation.

## Workflow: create project

1. Clarify: outcome, definition of done, non-goals, appetite/target date, which initiative.
2. Decide candidate vs committed (gate in [PROJECT-WRITING.md](references/PROJECT-WRITING.md)).
3. Write the brief, define stage milestones, decompose into issues (vertical slices, risk-first).
4. Present brief + milestones + issue list for confirmation before creating anything.

## Workflow: triage

Follow [TRIAGE.md](references/TRIAGE.md). Enforce the status gates and the hierarchy table above; every violation is a finding with a one-line proposed fix.

## Comments

When posting triage comments to Linear:

```
**Triage note** (generated by AI)

[content]
```
