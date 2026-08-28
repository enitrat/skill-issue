# Shaping a project

A project is a committed, bounded outcome with an end date. Shaping runs in a fixed order, because each artifact leans on the one before: **grill → brief → milestones → issues**. Skipping a step is how boards reach designers as a list of questions and tickets carry decisions nobody wrote down.

## Candidate → committed gate

Ideas accumulate as candidate projects (project state `Backlog`) holding a problem statement, evidence links and open questions. Commitment requires every box:

- [ ] Brief written to the template below
- [ ] Lead named, target date set, ≥1 initiative linked
- [ ] Stage milestones with dates
- [ ] First milestone decomposed into issues

A committed project holding a `[TO SCOPE]` issue failed this gate; demote it or run the gate.

## Grill

Question the brief until every open decision has an answer with a reason, using the context the user brings. Run the `grilling` skill if installed; otherwise ask, at minimum: who is the user and what job are they doing; what is out of scope and why; in which order do the pieces ship and what does the first piece unblock; what already exists in the product that this must match; what does each party get and give; which failure would embarrass us. Every answer is a recommendation the user can argue against. Keep a running **decided** list and check it before asking again.

## Decisions

A decision lives at the scope it binds:

- **Issue-scoped** (this screen shows X, this error reads Y, this field is optional): a comment on the issue, then the description edited if the contract changed. The comment is the record; the description is the contract.
- **Project-scoped** (delivery order, vocabulary, what is out for the whole project, a rule every issue obeys): a comment on the project brief or milestone, or, when there are more than a handful, a project document titled "Decisions" with one line per decision and a short **Open** list. Tickets point at the line they rest on.

A Decisions document holds one line per decision. It carries no per-feature sections: mechanics that bind one issue live on that issue, or on a context file attached to it.

Either way, a decision reached in Slack or a meeting is linked in (Cmd-K → link Slack message) within a day, with the outcome in one line. Change the decision where it lives first, then the tickets that lean on it.

## Project brief

The project description. Business altitude: someone outside the team learns something in the first two sections, and anything only an implementer needs goes to a ticket. The brief stands alone; links live under "Where the detail lives".

Put a screen's storyboard, frames, copy and design-system gaps on the issue that owns it. Keep the project brief focused on shared decisions and sources.

```markdown
## Summary
<4 lines: what, for whom, when it ships>

## Why it matters
<the business case: which KR, what breaks without it, what it positions us for, what risk it carries>

## What we ship
1. **<piece>** (M0, <date>). <one sentence>. <issues>
2. ...

## How it works
<two paragraphs a newcomer can follow: the mechanism, what the user sees, the one thing copy must never do>

## Who
| Party | Role | Owner |

## Scope
**In:** ... **Not in:** <each with a reason: deferred, unnecessary, external>

## Acceptance criteria
1. <outcome-level assertion testable by someone who never read the issues>

## Risks and dependencies
| If this is wrong | Then |

## Where the detail lives
- Decisions, sources
```

Three rewrites of one brief taught the altitude: v1 read like a protocol paper, v2 carried screen-level detail, v3 opened with the business. Write v3 first.

## States and storyboards

The product owner lists every situation a user can be in on each screen (session, data loading and failure, in-flight actions, empty), names them as situations ("price provider down"), never as code conditions, and gives each a one-sentence policy. Then **group the states into pictures as text**: states with the same visual output share one picture. Approve the grouping before drawing anything. The storyboard (one picture per group, one caption) is the enumeration engineers build from; states no picture can show (indexer lag, race conditions) become done-when bullets on the issue. One Storybook story per picture.

## Milestones

Stages with exit evidence, never layers. Each description states the outcome, what proves it (an E2E run, a live demo, a go/no-go), external dependencies with owner and date, and why it sits where it does. Highest-risk or launch-bound stage first. Each stage carries its own date; milestones that all share one date are stages in name only.

## Decomposition

- Vertical slices: each issue delivers a user-observable or structurally complete outcome.
- Risk first: the first issues test the riskiest assumption.
- Parent issues use real sub-issues; `relatedTo` decomposition is a finding.
- Leaves are 1–5 days. Larger → sub-issues; smaller than a ticket → a checklist line.
- Project-scoped decisions live at project level, never inside a leaf.
- A constraint shared by several issues is stated once in the brief; leaves point at it.
- Present the shape first (milestones, issue titles, what gets cancelled or merged), then the bodies, then write in one batch.

## Project updates

Weekly while active. The agent drafts from issue changes, comments and linked threads; the lead judges health and publishes.

```markdown
Health: On track | At risk | Off track

Since last update:
- Shipped or validated:
- Decisions taken (linked):
- Handoffs completed (issue → role):
- Scope or assumption changes:

Risks and decisions:
- Decision needed, owner, date:
- Blockers and external dependencies:

Next week:
- Outcome expected, its due date and its evidence:
```

## Anti-patterns

| Pattern | Fix |
|---|---|
| Brief at implementer altitude | Rewrite to the template |
| States table as the handoff artifact | Grouping as text, then storyboard; non-drawable states as done-when |
| Decisions in Slack or a meeting with no trace in Linear | Comment at the scope it binds, Slack link attached |
| Issue-scoped decision written into a project document, or the reverse | Move it to its scope |
| All milestones on the launch date | Re-cut the stages and date each one where its evidence lands |
| Immortal bucket project | New outcomes → own project; ambient fixes → team backlog |
| Milestones named after layers | Re-cut as stages with exit evidence |
