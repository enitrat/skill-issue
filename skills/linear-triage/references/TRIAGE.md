# Triage and audits

Every audit ends in a list of findings: the object, what's wrong, a one-line fix.
Then **prepare → confirm → execute**.

## Board health

Query open issues with their projects, milestones and assignees. Flag:

- Triage issues older than 7 days.
- Open issues missing priority or category label, or carrying a retired label
  ([LABELS.md](LABELS.md)).
- Ready issues that fail the Ready line in [SKILL.md](../SKILL.md).
- PRs linked to issues that aren't Ready or later.
- More than 2 issues In Progress per person.
- Dependencies written in prose instead of `blocks` / `blockedBy` relations.
- Backlog issues untouched for 30+ days.
- Committed projects with no milestones, or no update in 14 days.

Read recent completions before calling a project at risk. Report grouped by
problem; offer to fix a batch.

## Single-issue audit

1. `get_issue` with relations, its comments, and the project brief.
2. Does the body fit its shape in [ISSUE-WRITING.md](ISSUE-WRITING.md)? Is an open
   question written as a task?
3. Does the description contradict a decision in the comments? The decision wins;
   propose the edit.
4. Present what holds, what's missing, and numbered changes. Apply on approval.

## Intake

Keep evidence verbatim. Classify (category, module, priority), dedupe with
`list_issues`, route to a project or the team backlog.

## Batch fixes

Present `| Issue | Current | Proposed | Reason |` and apply after approval. Over ~15
issues, offer a subagent for the writes.
