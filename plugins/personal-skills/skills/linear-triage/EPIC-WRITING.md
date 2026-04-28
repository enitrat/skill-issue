# Writing Epics

An epic is a **strategic outcome container** — not a spec, not a task list, not a brain dump. It answers: "What problem are we solving, and how will we know we solved it?" It spans 1–6 weeks of total work and tracks a coherent outcome.

## What an epic is NOT

- **Not a spec.** Class names, method signatures, API contracts, storage schemas → belong in sub-issues.
- **Not a task list.** "Do X, then Y, then Z" is a project plan. The sub-issues table tracks sequencing.
- **Not a brain dump.** Long unstructured prose → restructure it.
- **Not an umbrella.** "Everything related to auth" has no end state. An epic has a concrete definition of done.

## Epic structure

Six sections. Each earns its place.

### 1. Background

Ground the reader in the domain. Assume they've never looked at this part of the system. Explain relevant concepts, architecture, protocol mechanics — whatever they need to understand the problem statement. Narrative prose, not bullets. Can be substantial but must teach, not ramble.

### 2. What's Wrong Today

What's broken, missing, or structurally wrong — and why no incremental patch fixes it. Name concrete failures, who they affect, what breaks. If failures share a root cause, state it explicitly. This section justifies the epic's existence.

### 3. Acceptance Criteria

5–10 outcome-level capability assertions. Rules:

- Testable by someone who has never read the sub-issues
- No class names, method signatures, or architecture references — observable behavior only
- Cover happy path and key edge cases
- Number them so sub-issues can reference "epic AC #3"

### 4. Success Metrics

| Metric | Target |
|--------|--------|
| What you're measuring | Concrete threshold |

Optional for pure refactors with no user-facing numbers. Mandatory when the epic exists because something is slow, broken, or costly.

### 5. Non-Goals

What this epic does NOT attempt. Consolidate scattered "out of scope" from sub-issues here. Each non-goal includes a one-sentence reason (deferred, unnecessary, depends on external work).

### 6. Assumptions & Dependencies

| Assumption | Impact if wrong |
|------------|-----------------|
| What you're assuming | What breaks or must change |

Include: interface stability, external service behavior, protocol invariants, prerequisite work.

## Sub-issues

### Table

Every epic includes a sub-issues table at the top (after metadata):

| ID | Title | Status | Labels | Blocked by |
|----|-------|--------|--------|------------|

### Decomposition section

Below the table, a short narrative (one paragraph per sub-issue) explaining dependency order and why each sub-issue exists. Not a restatement of descriptions — the map of the territory.

### Epic vs sub-issue boundary

**Epic holds:** the why (background, problem), outcome-level acceptance criteria, scope boundaries (non-goals), constraints affecting ALL sub-issues, the dependency map.

**Sub-issues hold:** their own Why/What/How (see [ISSUE-WRITING.md](ISSUE-WRITING.md)), granular testable criteria for their slice, implementation details (interfaces, contracts, architecture), their own includes/excludes.

**Never duplicate.** Constraint applies to all sub-issues → state once in epic. Sub-issues reference "see epic." Implementation detail in the epic → move to sub-issue.

### Decomposition principles

- **Slice vertically, not horizontally.** Each sub-issue delivers a user-observable or structurally complete outcome. "All frontend work" delivers nothing alone.
- **Order by risk, not ease.** First sub-issue tests the highest-risk assumption. Easy cleanup comes last.
- **Size at 1–5 days.** Larger → give it sub-issues. Smaller (one-line config) → doesn't warrant a ticket.
- **One foundation, then additive layers.** Foundation establishes the new shape (model, interfaces, migration). Subsequent sub-issues add behavior and can often parallelize.

## Quality scoring

Epics use the same 10-point scale as issues (see [ISSUE-WRITING.md](ISSUE-WRITING.md)) with adapted criteria:

- **#2 (Has Why):** Must have both Background AND Problem Statement sections.
- **#3 (Has What):** Outcome-level acceptance criteria (capability assertions), not implementation.
- **#4 (Has boundaries):** Must have an explicit Non-Goals section.
- **#5 (Has AC):** Capability assertions ("user can X", "system handles Y without Z"), numbered.
- **#6 (Right-sized):** 1–6 weeks total. Larger → it's an initiative, decompose further.
- **#7 (Well-structured):** Six-section structure, not Why/What/How.

## Anti-patterns

| Anti-pattern | What's wrong | Fix |
|---|---|---|
| **Spec in epic** | Class hierarchies, method signatures, schemas | Move to foundation sub-issue. Epic describes outcomes |
| **No acceptance criteria** | Sub-issues exist but no "done" for the epic | Add 5–10 capability assertions |
| **Duplicates sub-issues** | Epic and foundation sub-issue say the same things | Epic owns why + outcomes, sub-issue owns how |
| **Flat task list** | No dependency order or rationale | Add Decomposition section |
| **Never-ending epic** | No time-box, no end state | Define AC + metrics. If it can't end, it's a theme |
| **Vague outcomes** | "Improve the credential system" | Add success metrics |
| **Horizontal decomposition** | Sub-issues split by layer, not by outcome | Re-slice vertically |
| **Missing non-goals** | Scope creep from unstated exclusions | Consolidate into Non-Goals section |

## Red flags during triage

| Flag | Condition | Severity |
|------|-----------|----------|
| Empty epic | Description <100 chars | Critical |
| No sub-issues | 0 children, no decomposition plan | Warning |
| Stale epic | No update in 30+ days | Warning |
| TBD/WIP content | Main content is placeholder text | Critical |
| Spec in epic | Contains class names, method signatures | Major |
| Duplicates sub-issue | Same implementation details in both | Major |
