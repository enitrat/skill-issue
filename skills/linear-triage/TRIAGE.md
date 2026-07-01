# Triage Workflows

All triage follows **prepare → confirm → execute**: present proposed changes, wait for approval, apply.

## Board-level triage

When the user asks for a project overview, query all open issues (not completed, not canceled).

### Health dashboard

| Metric | Value | Flag |
|--------|-------|------|
| Open issues | N | — |
| Missing priority | N | Red if >0 |
| Missing labels | N | Red if >20% |
| Missing milestone | N | Yellow if >30% |
| Thin descriptions (<100 chars) | N | Red if >0 |
| Stale (no update >30 days) | N | Yellow if >0 |
| WIP per person | N | Red if >2 per person |

### Issues needing attention

Group flagged issues into:

- **Missing metadata**: no priority, no label, no milestone
- **Quality concerns**: empty descriptions, missing acceptance criteria, infodump (>1500 chars, no structure)
- **Stale**: no update in 30+ days while in Backlog
- **Overloaded WIP**: person has >2 items In Progress

For each: identifier, title, what's wrong, one-line proposed fix.

### Next steps

Let the user choose: fix a batch of metadata issues, deep-dive a specific ticket, or address a category.

## Single-issue triage

### 1. Gather context

- Read the full issue via `get_issue` with `includeRelations: true`
- Read sub-issues if it's a parent/epic
- Score against the quality checklist ([ISSUE-WRITING.md](ISSUE-WRITING.md) or [EPIC-WRITING.md](EPIC-WRITING.md) for epics)

### 2. Present assessment

- **Quality score**: X/10 with breakdown
- **What's good**: specific strengths
- **What's missing**: specific gaps with concrete suggestions
- **Metadata gaps**: missing labels, priority, milestone, assignee
- **Label check**: enforce rules from [LABELS.md](LABELS.md)
- **Proposed changes**: numbered list of every mutation

For **epics**, also check: follows 6-section structure? Contains implementation details that belong in sub-issues? Duplication with sub-issues? Has decomposition with dependency order?

For **infodumped issues**, propose a restructured version using Why/What/How.

### 3. Confirm

Present changes as a numbered checklist. The user can:

- Approve all: "go" / "apply" / "yes"
- Cherry-pick: "do 1, 3, 5"
- Reject: "skip" / "no"
- Discuss: ask questions or suggest alternatives

### 4. Execute

Apply via MCP tools (`save_issue`, `save_comment`, `create_issue_label`). Report what was done.

## Batch metadata fix

1. Query all issues with the specific gap
2. Propose values based on title/description analysis
3. Present as table: `| Issue | Current | Proposed | Reason |`
4. Apply after approval (all, cherry-pick, or override)

## Dependency audit

1. List all open issues in the project/milestone
2. Analyze logical dependencies from issue content
3. Flag missing blocking relationships
4. Present proposed `blocks/blocked-by` relations
5. Apply after confirmation
