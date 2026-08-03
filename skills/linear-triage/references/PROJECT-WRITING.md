# Writing Projects

A project is a **committed, bounded outcome**: it has a definition of done, a lead, a target date, stage milestones, and a link to the initiative (KR) it serves. If it cannot end, it is not a project.

This file replaces the old epic guidance. The `epic` label is retired: what used to be a labeled epic is either a **project** (multi-person, >~2 weeks, or deserves its own status reporting) or a **parent issue** (one deliverable decomposed into sub-issues).

## Candidate → committed gate

Ideas accumulate as **candidate projects** (project state `Backlog`): problem statement, linked evidence, open questions, rough appetite. That's all a candidate needs — and all it may have. Commitment is a deliberate transition requiring:

- [ ] Outcome stated (what is observably different when done)
- [ ] Definition of done + non-goals
- [ ] Lead named, target date set
- [ ] Stage milestones defined
- [ ] Linked to ≥1 initiative
- [ ] Initial decomposition exists (at least the first milestone's issues)

A project in `Todo`/`In Progress` containing a `[TO SCOPE]` brain-dump issue failed this gate — flag it during triage.

## Project brief structure

Six core sections plus delivery. The reference example is *Delegated View Grants* (SUP team) — match its density, not its length.

### 1. Background
Ground a reader who has never seen this domain. Narrative prose that teaches: concepts, architecture, protocol mechanics needed to understand the problem. Substantial is fine; rambling is not.

### 2. What's Wrong Today
Concrete failures, who they affect, why no incremental patch fixes it. If failures share a root cause, name it. This section justifies the project's existence.

### 3. Acceptance Criteria
5–10 numbered, outcome-level capability assertions. Testable by someone who never read the issues. No class names or architecture — observable behavior only. Mark research ACs explicitly *(research)* — "a documented decision to stop" is a valid AC.

### 4. Success Metrics
| Metric | Target |
|---|---|

Mandatory when the project exists because something is slow, broken, or costly. Optional for pure refactors.

### 5. Non-Goals
What this project does NOT attempt, each with a one-sentence reason (deferred, unnecessary, blocked on external work). Consolidate scattered "out of scope" notes from issues here.

### 6. Assumptions & Dependencies
| Assumption | Impact if wrong |
|---|---|

Include interface stability, external services, protocol invariants, prerequisite work owned by other teams.

### 7. Decisions & Sources
- Decisions made, rationale, and rejected alternatives — especially **reopened decisions**: if the project revisits a call someone already made, say whose, when, and why reopening is justified.
- Source links: Slack threads, Notion docs, incident reports, customer requests. Preserve the chain from evidence to commitment.

## Brief voice

- **The brief stands alone.** A reader from product, engineering, or commercial catches up in one read without opening a link. State facts and own them; links live only in Sources as the evidence chain. (Issues are the opposite: they point at paths and let the agent read — [ISSUE-WRITING.md](ISSUE-WRITING.md).)
- **Density, not register.** Clarity rules — active voice, one meaning per word, no hedges — at normal sentence length. Explain mechanism and why, with connective tissue between sentences, not staccato definitions. Match the density of the reference brief, not its register.

## Milestones

Milestones are **stages of the project lifecycle**, never components or layers.

Each milestone description states:
- **Stage outcome** — what is true when it completes.
- **Exit evidence** — what proves it (a live E2E run, a written go/no-go, a demo).
- **External dependencies** — anything gating it that this team doesn't own, with owner and date.
- **Purpose when non-obvious** — de-risking vs delivery, and what decision it feeds.

Good: `Amoy testnet (rehearsal)`, `M1 — Decision & feasibility`, `Mainnet go-live`. Bad: `Backend`, `Frontend`, `Testing`. A milestone that outgrows its project gets promoted to its own project.

Sequence milestones so the **highest-risk or most time-critical stage comes first**, and say in the description why the order is what it is.

## Decomposition

- **Slice vertically, not horizontally.** Each issue delivers a user-observable or structurally complete outcome. "All frontend work" delivers nothing alone.
- **Order by risk.** The first issues test the riskiest assumption. Easy cleanup comes last.
- **Parent issues use real sub-issues.** Decomposition via `relatedTo` links is a triage finding: related issues don't roll up, so the parent shows no progress and its checklist rots.
- **Size leaves at 1–5 days.** Larger → needs sub-issues. Smaller than a ticket (one-line config) → checklist item inside a leaf.
- **The parent survives approach changes; leaves are disposable.** Product decisions live at the parent/project level, never hidden inside a leaf.
- Issues follow the U-shaped template ([ISSUE-WRITING.md](ISSUE-WRITING.md)) and stay under their word caps — the brief carries the narrative so issues don't have to. State a constraint that applies to all sub-issues once, here in the brief; leaves reference it.

## Project updates

Weekly for active projects. An agent drafts from issue changes and linked discussions; the **lead judges health and publishes** — health is an interpretation, not a computation.

```markdown
Health: On track | At risk | Off track

Since last update:
- Shipped or validated:
- Learned:
- Scope/assumption changes:

Risks & decisions:
- Decision needed, owner, deadline:
- Blockers and dependencies:

Next:
- Next meaningful outcome and its expected evidence:
```

## Anti-patterns

| Anti-pattern | What's wrong | Fix |
|---|---|---|
| **Immortal bucket** | No outcome, no end ("Continuous Enhancements") | New outcomes → own project; ambient fixes → team backlog |
| **Committed-but-unshaped** | Project in Todo holding `[TO SCOPE]` dumps | Demote to candidate or run the commitment gate |
| **Spec in brief** | Class names, signatures, schemas in the project | Move to the foundation issue; brief owns outcomes |
| **relatedTo decomposition** | Children linked as "related", no roll-up | Convert to sub-issues |
| **Layer milestones** | "Backend", "Frontend" stages | Re-cut as lifecycle stages with exit evidence |
| **Orphan project** | No initiative link | Attach to its KR, or question why it's committed |
| **Dangling initiative** | KR with zero projects after shaping | Create the delivery project or mark the KR at-risk |
| **Never-updated** | health unknown, no updates | Weekly update cadence, agent-drafted, lead-published |

## Red flags during triage

| Flag | Condition | Severity |
|---|---|---|
| Empty brief | Description < 100 chars on a committed project | Critical |
| No milestones | Committed project without stages | Major |
| No initiative | Committed project unlinked to any KR | Major |
| Stale | No update in 14+ days while active | Warning |
| TBD/WIP content | Brief is placeholder text | Critical |
| Grandfathered epic | `epic`-labeled issue still in a bucket project | Warning — promote when next active |
