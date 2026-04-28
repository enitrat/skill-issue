# Writing Issues

The goal: anyone reading the issue understands full context and knows exactly what to deliver — without asking the author a single question.

## Guiding principle: lock the contract, free the implementation

Issues define the **outcome and boundaries**, not the internal code. The implementer decides how to structure, name, and wire things.

**Lock in the issue:** public API signatures consumers depend on, behavioral contracts for non-obvious algorithms, architectural constraints (module boundaries, dependency direction), invariants (what must NOT change), error contracts.

**Leave free:** internal data structures, file layout, naming, helper extraction, implementation order.

The test: if removing a detail would let the implementer accidentally break a consumer or downstream issue, it's a contract → put it in How. If removing it just means different internal code structure, leave it out.

## Template

Every issue has three sections. Each forces a different mode of reasoning.

### Why

A narrative paragraph (not bullets) answering in sequence:

1. **What exists today?** Ground the reader in current system state. Assume they've never seen this code.
2. **What's wrong or missing?** The gap, pain, or failure. Who is affected, how, what breaks.
3. **Why now?** Link to a milestone, dependency, user report, or strategic decision. If "why now" can't be articulated, question whether this belongs in the active backlog.

Reads like a briefing — someone picking this up cold understands the full motivation without clicking links.

### What

The outcome — what the system looks like when done. Four parts:

**Prose description:** A paragraph on the concrete deliverable. Enough detail to know the shape of the outcome without being told how to code it.

**Invariants** (refactors only): What must NOT change. Existing behaviors, interfaces, or guarantees that must survive. Any passing test must still pass.

**Scope table** (mandatory when touching >1 subsystem):

| Includes | Excludes |
| --- | --- |
| Concrete in-scope deliverable | Related thing explicitly out of scope |

**Done when** (2–5 criteria, up to 12 for foundation tickets):

- [ ] Observable behavior, not internal state ("user can X", "system handles Y by doing Z")
- [ ] For complex scenarios use Given/When/Then: "Given [precondition], when [action], then [result]"

### How

Orients the implementer on solution constraints. Prose (not a numbered recipe) covering whichever of these apply:

- **Subsystems involved:** Name the layers/modules this touches.
- **Locked interfaces:** Public API signatures in code blocks. These are contracts.
- **Architectural constraints:** Component responsibilities, dependency direction.
- **Behavioral contracts:** Pseudocode for non-obvious algorithms.
- **Verification approach:** What kinds of tests, key scenarios.
- **Dependencies:** Issues that must land first, external coordination.

Mandatory for features/improvements spanning multiple components. Optional for bug fixes and doc updates. Omit entirely for trivial changes (typos, one-line configs).

## Quality scoring

Score each issue on 10 criteria (1 point each):

| # | Criterion | 1 point | 0 points |
|---|-----------|---------|----------|
| 1 | **Actionable title** | Verb or prefix (`feat:`, `fix:`), scannable in a list | Vague, noun-only, or >80 chars |
| 2 | **Has Why** | Narrative briefing: current state, what's broken, why now | Missing or scattered |
| 3 | **Has clear What** | Concrete deliverables as prose | Vague ("improve performance") |
| 4 | **Has boundaries** | Includes/excludes table, or scope is self-evidently narrow | Open-ended, no boundaries |
| 5 | **Has acceptance criteria** | 2–5 testable conditions, observable behaviors | Missing or untestable ("works well") |
| 6 | **Right-sized** | 1–3 days. If larger, has sub-issues | Too large or trivially small |
| 7 | **Well-structured** | Why/What/How sections, key info scannable | Wall of text >1500 chars, no structure |
| 8 | **Has priority** | Urgent, High, Medium, or Low | None |
| 9 | **Has label(s)** | At least one category label | None |
| 10 | **Has milestone** | Assigned to milestone or marked exploratory | Active work with no timeline |

| Score | Action |
|-------|--------|
| 9–10 | Apply `ready` label |
| 7–8 | Note minor gaps, suggest fixes |
| 5–6 | Apply `needs-scoping`, propose improvements |
| 3–4 | Major rewrite needed |
| 0–2 | Not a real issue — rewrite or close |

**Infodump detection:** >1500 chars AND <3 markdown headers AND no checklists AND no acceptance criteria → scores 0 on criterion 7. Fix by restructuring into Why/What/How.

## Anti-patterns

| Anti-pattern | What's wrong | Fix |
|---|---|---|
| **Solution as issue** | "Refactor X to use Y" — no problem statement | Write the Why first. What problem does this solve? |
| **Infodump** | 2000 words, no structure | Restructure into Why/What/How |
| **Placeholder** | Title + one sentence | Flesh out or create as `Spike` with time-box |
| **Code prescription** | Dictates file layout, internal naming, implementation order | Strip internals. Only lock contracts and boundaries |
| **Scope bomb** | Touches 5+ subsystems, no decomposition | Break into epic with sub-issues |
| **Flat checklist** | Disconnected bullet lists, no narrative | Rewrite as Why/What/How prose |
| **Contracts in What** | Locked interfaces dumped in What section | Move to How. What = outcome, How = constraints |
| **Missing invariants** | Refactor with no list of what must NOT change | Add Invariants subsection in What |
| **Numbered recipe** | "Step 1: build X. Step 2: wire Y." in How | Rewrite as prose. Implementer decides order |
