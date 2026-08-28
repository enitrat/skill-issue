---
name: linear-triage
description: Linear project management for a product → design → engineering team. Use whenever the user mentions Linear or an issue identifier like TEAM-123 — shaping a project or writing its brief, writing or reviewing an issue, moving an issue between statuses or handing it to the next seat, auditing a board, setting or reviewing due dates, recording a decision, or drafting a project update.
---

# Linear

Manage work in Linear with the `mcp__claude_ai_Linear__*` tools. Every mutation runs **prepare → confirm → execute**: show the exact changes, wait for approval, apply, then re-read and report what landed.

## Reference

- [PROJECT-WRITING.md](references/PROJECT-WRITING.md) — grill, decisions, project brief, milestones, decomposition, project updates
- [ISSUE-WRITING.md](references/ISSUE-WRITING.md) — the issue template and how it grows through each stage, word caps, voice, scoring
- [TRIAGE.md](references/TRIAGE.md) — board health, single-issue audit, handoff audit, decision hygiene, due-date planning, batch fixes
- [LABELS.md](references/LABELS.md) — label taxonomy and retirements

## Where things live

| Tool | Holds | Never holds |
|---|---|---|
| Notion | Strategy: OKRs, quarter plans, partner and business docs | Discussion of a project that is already in Linear |
| Linear project | The brief, milestones, project updates, project-scoped decisions (comments or a "Decisions" document) | Implementation detail; decisions about one issue |
| Linear issue | One unit of work, its states, its acceptance criteria, its design context and its own decisions as comments | Project narrative; project-wide decisions |
| Figma / tldraw / Storybook | Design artifacts at a stated fidelity, linked from the issue | Scope. A frame or a branch is never authorisation to build |
| Slack | Pings and banter: "done, please look", "starting X, any context?" | Final authority. A decision taken in Slack is linked into Linear within 24 hours |

**The scope rule.** A decision is recorded at the scope it binds: about one issue → a comment on that issue; about the whole project → a comment on the brief or milestone, or a line in the project's "Decisions" document. Slack threads are linked in (Cmd-K → link Slack message) so the reasoning survives. Before re-asking a question, read the comments and decisions: a question already answered is closed.

## The hierarchy

One unbroken chain: **initiative → project → milestone → issue**. Content at the wrong level is a triage finding.

| Object | Is | Must have |
|---|---|---|
| Initiative | A KR | Owner, target, ≥1 project once committed |
| Project | A committed, bounded outcome with an end date | Brief, lead, target date, stage milestones, ≥1 initiative |
| Candidate project | Evidence and open questions, no commitment. Project state `Backlog` | Problem statement, evidence links |
| Milestone | A stage with exit evidence | Stage outcome, what proves it, target date |
| Parent issue | One deliverable that needs several leaves | Real sub-issues, own Outcome and Why |
| Leaf issue | Smallest delegable, verifiable unit | Passes the gate for its status |

Project versus parent issue: several people, more than ~2 weeks, or deserves its own status reporting → project. Ambient work (one-off bugs, polish) lives in the team backlog with no project. Bucket projects ("Continuous Enhancements") receive nothing new.

## Seats and handoffs

A ticket has one owner at a time and several owners over its life. The **assignee is the current owner**; a status change that hands the work on also changes the assignee and posts a Slack ping. Accountability defines a seat, tasks do not: a designer may code and an engineer may sketch without moving the seat.

| Seat | Owns on an issue | Decides alone |
|---|---|---|
| Product | Outcome, Why, scope, the state list grouped into pictures, behavioural done-when, priority | What the user can do, and in which order features ship |
| Design | Layout, interaction, copy, the DS component per picture, filed DS gaps | Interface within DESIGN.md, copy within the voice guide, component promotion |
| Engineer | Pointers, constraints, estimate, implementation, one story per picture, tests | Implementation approach, test strategy, stopping when code reaches an unlisted state |
| Lead | Priority between projects, what ships, the two gate reviews | Architecture, this process |

The lead reviews at two gates only: **Ready** (the issue is complete enough to build) and **PR** (quality of what ships). Everything between belongs to the seat that owns the step. A product remark the ticket does not cover goes back into the ticket, never into the diff.

## Status state machine

Statuses are policy. A transition is legal only when its entry gate holds; a backwards move carries a one-line comment saying why.

| Status | Owner | Entry gate |
|---|---|---|
| **Triage** | Lead | Raw intake with evidence verbatim: source link, reporter, where seen |
| **Backlog** | Lead | Category + module label, priority, deduped, routed to a project or parked in team backlog |
| **Product shaping** | Product | Someone is writing Outcome, Why, scope and the state list |
| **Design shaping** | Design | Product half complete: Outcome, done-when, scope, storyboard link. Assignee is the designer, due date set |
| **Ready** | Engineer | The **readiness test** below. Design half complete when `area:ux` |
| **In Progress** | Engineer | Claimed. Agent-run work stays assigned to its accountable human |
| **In Review** | Engineer → Lead | PR open, body cites the issue. Review covers acceptance criteria, not only the diff |
| **Done** | — | Every done-when verified. Linked stakeholders notified |
| **Canceled / Duplicate** | — | Reason stated / original linked |

When a team has a single `Shaping` status, treat it as `Product shaping`; propose creating `Design shaping` (type backlog, between Shaping and Ready) the first time an `area:ux` issue needs it. Status creation is a UI action, not an MCP one.

### The readiness test

Ready holds only when **all** are true:

1. One primary objective; no unresolved product decision hidden inside. Open questions are listed as such or split into a spike.
2. Written to the template in [ISSUE-WRITING.md](references/ISSUE-WRITING.md); quality score ≥ 7.
3. Scope In, Out and Appetite explicit.
4. Verification stated: a command, an observable check, or a story per picture.
5. Dependencies are Linear **relations**, never prose.
6. Estimate set and **human-confirmed**. Agents propose, humans bless.
7. Milestone assigned when the project has milestones; **due date set**.
8. When `area:ux`: every picture has a design link and copy, DS gaps are filed issues.

**No Ready ticket, no PR.** Work enters the build from Ready and nowhere else; a branch, a Figma frame or a Slack answer admits nothing.

## Due dates are the deadline

Every issue from Design shaping onwards carries a **`dueDate`**: the day the current seat hands the work on. The date is set when the issue enters the status and re-set at each handoff, so the designer sees "designs due Wednesday" and the engineer "build due the 12th" on the issue itself, without asking. Dates work backwards from the milestone: build due on or before the milestone date, design due before the build starts with room for the build. An issue in Design shaping or Ready without a due date, or past its due date with its status unchanged, is a triage finding. Moving a due date is fine and carries a one-line comment saying why. Cycles, when a team runs them, are a reporting window, never a substitute for the date.

## Scope and fidelity

- Scope is added by the product seat through the ticket. Discovering missing scope mid-build → stop, comment on the issue, product decides; never resolve it in the PR.
- Every artifact states its stage: exploration, storyboard, states, hi-fi. Nothing is labelled "Final" but shipped code. A prototype or branch labelled non-prescriptive is a proposal, not scope.
- Copy is data the component receives; final wording belongs to whoever owns voice, and never blocks Ready.

## The drafting pass

Nothing written by an agent reaches the user or Linear as a first draft. Every body (brief, issue, milestone description, project update, decision comment) goes through one pass:

1. **Draft to a scratch file**, all bodies for the same confirmation step in one file, each under a heading naming its target.
2. **One subagent rewrites the whole file**, invoking the `unslop` skill (AI tells) and the `technical-writing` skill (clarity, density). The **structure is fixed**: section order, headings, checkboxes, severity markers and word caps from the template in [ISSUE-WRITING.md](references/ISSUE-WRITING.md) or [PROJECT-WRITING.md](references/PROJECT-WRITING.md) stay exactly as drafted; only the prose inside each section is rewritten. Where `unslop` and the template disagree (first person, opinions, rhythm), the template wins: a ticket is imperative and voiceless by design.
3. **Re-read and score** each body against its template; fix the last lines by hand rather than with a second run.
4. **Present**, then write to Linear from the file.

One subagent per batch, never one per body.

## Workflows

**Shape a project** → [PROJECT-WRITING.md](references/PROJECT-WRITING.md). Grill, brief, milestones, issues; project-scoped decisions recorded at project level. Confirm the shape (milestones + issue titles) before writing bodies; confirm bodies before writing to Linear.

**Write or rewrite an issue** → [ISSUE-WRITING.md](references/ISSUE-WRITING.md). Draft to the template for its stage, score it, propose metadata (priority, labels, milestone, due date, relations, estimate flagged for confirmation), present, then `save_issue`. Status follows the gates.

**Move or hand off an issue** → check the entry gate of the target status. Present: gate result, assignee change, new due date, the Slack ping text. Backwards moves carry a comment.

**Triage or audit** → [TRIAGE.md](references/TRIAGE.md). Every violation is a finding with a one-line fix.

**Record a decision** → at its scope: `save_comment` on the issue for issue-scoped decisions; `save_comment` on the project or milestone, or `save_document` patch on the "Decisions" document, for project-scoped ones. One line for the decision, one for the reason, the Slack link if the discussion happened there. Then edit the description if the decision changes the contract.

**Project update** → template in [PROJECT-WRITING.md](references/PROJECT-WRITING.md) § Project updates. Agent drafts, lead sets health and publishes.

## Comments posted by an agent

```
**Triage note** (generated by AI)

[content]
```

## MCP gotchas

- Edit descriptions with `patch` ops, not full rewrites; anchors must match once.
- Milestones cannot be deleted through the MCP: rename to "Retired, delete me" and delete by hand. Re-read milestone descriptions after saving; a first save has appeared not to persist.
- `labels` on `save_issue` replaces the whole set; pass the full list.
- Cancelling an issue keeps its body; prepend the one-line reason above it.
- After a batch of writes, `get_issue`/`get_project` once more and diff against what you intended.
