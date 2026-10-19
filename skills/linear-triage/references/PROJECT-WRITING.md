# Shaping a project

Order: **grill → brief → milestones → issues**. Confirm each before writing the next.

## Grill

Question the plan until each open decision has an answer and a reason. Use the
`grilling` skill if installed. At minimum: who is the user and what job are they
doing; what's out and why; in which order do pieces ship; what must this match in
the product today. Keep a running **decided** list and check it before asking again.

## Brief

The project description, at business altitude: someone outside the team learns
something from the first two sections. Implementation detail goes to issues.

```markdown
## Summary
<what, for whom, when it ships: 2–4 lines>

## Why it matters
<the KR it serves, what breaks without it>

## How it works
<one or two paragraphs a newcomer can follow: the mechanism and what the user sees>

## What we ship
1. **<piece>** (<milestone>, <date>). <one sentence>.

## Not in
<each with a reason>
```

Add **Who** (party, role, owner) or **Risks** (if this is wrong → then) only when
they have something important in them.

## Milestones

Stages with exit evidence: the outcome, what proves it (an E2E run, a demo), and a
date. Riskiest or launch-bound stage first. Milestones all on one date are stages
in name only.

## Decomposition

- Vertical slices, riskiest first.
- Present the shape (milestones and issue titles) before any body.
- Bodies follow [ISSUE-WRITING.md](ISSUE-WRITING.md). A rule shared by several
  issues is stated once in the brief.

## Project updates

Weekly while active. The agent drafts from issue changes and linked threads; the
lead sets health and publishes.

```markdown
Health: On track | At risk | Off track

- Shipped:
- Decided (linked):
- Blocked on / decision needed (owner, date):
- Next:
```

Leave out any line with nothing in it.
