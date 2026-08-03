# Triage Workflows

All triage follows **prepare → confirm → execute**: present proposed changes, wait for approval, apply. Statuses are the state machine — every gate check below refers to the entry gates in [SKILL.md](../SKILL.md).

## Board-level triage

Query all open issues (not completed/canceled/duplicate) plus all projects and their initiative links.

### Health dashboard

| Metric | Flag |
|---|---|
| Issues in Triage older than 7 days | Red |
| Open issues missing priority | Red if > 0 |
| Open issues missing category label | Red if > 0 |
| Issues in Ready failing any readiness-test item (no estimate, no verification, deps in prose) | Red if > 0 |
| Issues with a milestone-bearing project but no milestone | Yellow |
| Project-less issues that are neither in Triage nor explicitly team-backlog | Yellow |
| Retired labels present (`ui`, `blocked`, `ready`, …) | Yellow — migrate per [LABELS.md](LABELS.md) |
| Stale: no update in 30+ days in Backlog | Yellow |
| WIP per person > 2 (In Progress) | Red |
| Committed project without milestones or initiative link | Major finding |
| Active project with no update in 14+ days | Warning |
| Initiative with zero projects | Warning |
| Parent "decomposed" via `relatedTo` instead of sub-issues | Major finding |

Before flagging a project as schedule risk, read its recent completions and which milestone the open issues belong to — open-issue counts alone don't establish risk.

### Report format

Group findings by the gate they violate. For each: identifier, title, what's wrong, one-line proposed fix. Then let the user choose: fix a batch, deep-dive one item, or address a category.

## Status-gate audit (single issue)

1. **Gather**: `get_issue` with `includeRelations: true`; sub-issues if a parent; project brief if relevant.
2. **Check the issue is legal in its current status** — the strongest triage question is "does this issue's content justify where it sits?" A `[TO SCOPE]` dump in Ready/Todo is the canonical violation: demote to Shaping, don't polish in place.
3. **Score** against [ISSUE-WRITING.md](ISSUE-WRITING.md) (or the project checks in [PROJECT-WRITING.md](PROJECT-WRITING.md)).
4. **Present**: quality score with breakdown, what's good, what's missing (concrete suggestions), metadata gaps, label check per [LABELS.md](LABELS.md), status verdict (stay/demote/promote), numbered list of every proposed mutation.
5. **Confirm**: approve all ("go"), cherry-pick ("do 1, 3"), reject, or discuss.
6. **Execute** via `save_issue` / `save_comment` / relations. Report what was done.

## Intake triage (Triage status)

For each issue in Triage:

1. **Preserve evidence** — source link, reporter, where observed. Never summarize away the original report; quote it.
2. **Classify** — category label, module label, priority.
3. **Dedupe** — search for existing issues; propose Duplicate status with a link when found.
4. **Route** — to a project (if it belongs to a committed outcome) or to the team backlog (ambient work). Never into a bucket project.
5. Exit to **Backlog** once the above hold; straight to **Shaping** only if someone will spec it now.

## Batch metadata fix

1. Query all issues with the specific gap.
2. Propose values from title/description analysis.
3. Present as table: `| Issue | Current | Proposed | Reason |`.
4. Apply after approval (all, cherry-pick, or override). For large batches (>15 issues), offer to delegate execution to a subagent and report back with the change table.

## Dependency audit

Relations are the single source of truth for blocking.

1. List open issues in the project/milestone.
2. Infer logical dependencies from content ("after X lands", "needs the Y contract").
3. Flag: dependencies stated in prose without a relation; relations pointing at Done issues (stale); cycles.
4. Present proposed `blocks`/`blocked-by` mutations; apply after confirmation.

## Estimate review

When issues approach Ready:

1. List candidates missing estimates or carrying agent-proposed, unconfirmed ones.
2. Propose an estimate per issue with a one-line rationale (reference similar completed issues where possible).
3. The user confirms or overrides each, per the estimates policy in [SKILL.md](../SKILL.md).
