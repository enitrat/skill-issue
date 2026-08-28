# Triage and audits

Every audit ends in a list of findings, each with the object, what is wrong, and a one-line fix; then **prepare → confirm → execute**. Gates and statuses are defined in [SKILL.md](../SKILL.md).

## Board health

Query open issues (not Done/Canceled/Duplicate) with their due dates, projects, milestones, initiative links.

| Check | Flag |
|---|---|
| Issue in Triage older than 7 days | Red |
| Open issue missing priority or category label | Red |
| Issue in Ready failing any readiness-test item | Red |
| Issue in Design shaping or later with no due date | Red |
| Issue past its due date with status unchanged and no comment | Red |
| Issue due after its milestone's target date | Yellow |
| Issue in Design shaping without a storyboard link, or assignee not the designer | Red |
| `area:ux` issue in Ready whose Design block has a picture without a frame | Red |
| PR linked to an issue that is not Ready or later | Red — no Ready ticket, no PR |
| Status moved backwards with no comment | Yellow |
| Issue in a milestone-bearing project with no milestone | Yellow |
| Project-less issue that is neither Triage nor explicitly team backlog | Yellow |
| Retired label present | Yellow — migrate per [LABELS.md](LABELS.md) |
| Backlog issue untouched 30+ days | Yellow |
| WIP per person > 2 in In Progress | Red |
| Committed project without milestones or initiative link | Major |
| Every milestone on the same date | Yellow — milestones are stages; date each one where its evidence lands |
| Active project without an update in 14+ days | Warning |
| Parent decomposed through `relatedTo` | Major |
| Constraint text repeated across ≥2 issues | Yellow — promote to harness |

Before calling a project at risk, read its recent completions and which milestone the open issues belong to.

Report grouped by gate violated. Offer: fix a batch, deep-dive one item, or a category.

## Single-issue audit

1. `get_issue` with `includeRelations: true`; its comments; sub-issues if a parent; the project brief and its Decisions document if one exists.
2. Is the issue legal where it sits? A `[TO SCOPE]` dump in Ready is the canonical violation: demote to Product shaping. An `area:ux` issue in Ready with empty Design block: demote to Design shaping.
3. Score against [ISSUE-WRITING.md](ISSUE-WRITING.md) for its stage.
4. Check decisions: does the description contradict a decision in its own comments or at project level? The decision wins; propose the edit. A decision sitting at the wrong scope (issue detail in the project document, project rule buried in one issue's comments) is a finding.
5. Present: score with breakdown, what holds, what is missing, metadata gaps, label check, status verdict (stay / demote / promote), numbered mutations.
6. Confirm ("go", "1 and 3", reject, discuss). Execute. Re-read and report.

## Handoff audit

Run when an issue changes seat, or on request for a project.

1. Target status gate holds (SKILL.md table).
2. Assignee is the seat that owns the target status.
3. Due date set to the day this seat hands the work on: a design due date falls before the build starts, a build due date on or before its milestone.
4. The artifact travels with its context: the storyboard for design, frames + copy for engineering.
5. Propose the Slack ping: one line, issue link, what is expected, by when (the due date).
6. A backwards handoff carries a comment naming what was missing.

## Decision hygiene

Run weekly per active project, or when someone asks "why did we decide X".

1. List comments and linked Slack threads on the project, milestones and issues since the last update.
2. Any decision in Slack or a 1:1 that changed scope, order, naming or a done-when, and has no comment or record line → propose the comment and, if the contract changed, the description edit.
3. Any record line contradicted by a ticket → propose fixing the ticket.
4. Any question in the "Open" section answered somewhere → move it to decided.
5. Vocabulary changes reach the project's glossary (`CONTEXT.md` or equivalent) in the same batch.

## Intake (Triage status)

For each issue: preserve evidence verbatim; classify (category, module, priority); dedupe (`list_issues` query; propose Duplicate with the original); route to a project or the team backlog, never a bucket. Exit to Backlog, or straight to Product shaping when someone will shape it now.

## Due-date planning

Weekly, or when a milestone date moves:

1. List issues in Design shaping or later without a due date, past their due date, or due after their milestone.
2. Propose dates working backwards from the milestone: build due on or before the milestone; design due before the build starts, leaving the build its estimate's worth of days. Keep WIP ≤ 2 per person per week.
3. Overdue issues: propose the new date with the reason as a comment, or a status move if the work is done, or an escalation to the lead if the date cannot hold.
4. Present as `| Issue | Status | Seat | Current due | Proposed due | Reason |`. Apply after confirmation with `save_issue` `dueDate`.
5. Flag cross-team load on a shared seat (a designer serving two teams) as a finding for the lead; the tool cannot resolve it.

## Batch metadata fix

Query the gap, propose values from title and description, present `| Issue | Current | Proposed | Reason |`, apply after approval. Over ~15 issues, offer a subagent for execution and report the table back.

## Dependency audit

1. List open issues in the project or milestone.
2. Infer dependencies from content ("after X lands", "needs the Y indexer").
3. Flag prose dependencies without a relation, relations to Done issues, circular relations, and a blocker due after the issue it blocks.
4. Propose `blocks` / `blockedBy` mutations; apply after confirmation.

## Estimate review

List issues approaching Ready without an estimate or with an agent-proposed one; propose per issue with one line of rationale referencing similar completed issues; the user confirms or overrides each.
