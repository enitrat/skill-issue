# Writing issues

An issue is a prompt: humans skim it, agents execute it, and both attend to the top and the end and lose the middle. The layout is **U-shaped**: the contract (Outcome, Done when, Scope) above the fold, binding Constraints last, narrative in the middle. Density beats length; evidence in [issue-writing-research.md](issue-writing-research.md) when a rule is challenged.

One issue is owned by three seats in turn, so the body **grows by stage**. Each stage adds its blocks and never rewrites the previous seat's blocks without a comment.

## The template

```markdown
# <Imperative title: verb + object + qualifier, ≤12 words>

**Outcome.** One sentence: what is true after this ships that is not true now.

## Done when
- [ ] <observable assertion>                       ← product: behaviour
- [ ] <state no picture shows, as an assertion>    ← product: indexer lag, races
- [ ] One Storybook story per picture on the storyboard   ← when area:ux
- [ ] `<literal command that must pass>`           ← engineer: at least one, always

## Scope
**In:** <1–4 bullets>
**Out:** <1–4 bullets, each pointing at the issue that owns it or "nothing">
**Appetite:** <one PR | S | M | L>

## Why                                             ← ≤80 words; the record carries the rest
<Two sentences and a link to the decision this rests on, if any.>

## Design                                          ← when area:ux; keep the issue's design context here
- Storyboard: <link>, pictures <n–m>
- Frames: <Figma link per picture, or "in Storybook">
- Copy: <where the strings live; "placeholder, owner: marketing">
- DS gaps filed: <issues>

## Pointers                                        ← engineer; label it "production details" if the designer reads it
- `path/to/file.ts` — <why it matters, ~6 words>
- Prior art: <path>

## Constraints                                     ← last = recency; severity in CAPS
- MUST NOT <...>
- MUST <...>
- SHOULD <...>

<collapsed appendix: traces, schema dumps, alternatives considered>
```

Constraints stay visible; a collapsed MUST escapes human review. Use a Linear collapsible for the appendix, or a trailing `## Appendix` heading.

## What each stage adds

| Stage (status) | Seat | Adds | Exit when |
|---|---|---|---|
| Product shaping | Product | Title, Outcome, Why, Scope, behavioural done-when, storyboard link, milestone, priority | Every state on the storyboard is a picture or a done-when |
| Design shaping | Design | Frames per picture, copy, DS gaps filed, redrawn pictures with a one-line reason | Every picture has a frame and copy; assignee moves to the engineer; Slack ping posted |
| Ready | Engineer | Pointers, Constraints, the command done-when, estimate (confirmed), due date, relations | Readiness test in [SKILL.md](../SKILL.md) passes |

A ticket without `area:ux` skips Design shaping.

## Section contract

| Block | Human | Agent |
|---|---|---|
| Title, Outcome, Done when, Scope | Read: is this mine, how big, when am I finished | Done-when is the definition of complete; run the commands |
| Why | Skim | Disambiguate only; never widen scope from it |
| Design | Design and engineer read | Frames name the components to use |
| Pointers | Skim | Start here |
| Constraints | Read the MUSTs | Violating a MUST fails the task regardless of tests |
| Appendix | Skip | Read |

Load-bearing content in a skip zone is the author's fault; a missed done-when is the reader's.

## Word budgets

Counts exclude appendices and code blocks.

| Type | Target | Cap | Required blocks |
|---|---|---|---|
| Chore | 40–100 | 150 | Title, Outcome, one command |
| Bug | 120–220 | 300 | Title, Outcome, **Reproduction** (replaces Why), done-when incl. failing test, Pointers |
| Spike | 120–250 | 300 | Question, **Timebox**, Deliverable (a written decision), Kill criteria |
| Feature, one PR | 250–400 | 500 | Full template |
| Feature, multi-PR | 350–500 | 600 | Full template; the brief and record carry the narrative |

Over the cap → split it, or move project-level rationale to the project and link it.

- **Bug:** Reproduction replaces Why: steps, environment, first seen, verbatim error. Hypotheses go to the appendix, labelled.
- **Spike:** the deliverable is a written decision; "no change" is valid. Timebox is the appetite.

## Constraints

Lock what breaking would hurt a consumer or a downstream issue: public signatures, behavioural contracts, module boundaries, invariants, error contracts. Leave internal structure, naming and order to the implementer. Test: would removing the line let a competent implementer make a *wrong* choice, not merely a different one? If no, cut it.

Severity is RFC 2119 in ALL CAPS. A constraint that appears in a second issue moves into CLAUDE.md, a skill, a type or a CI check, and leaves every issue.

## Formatting

1. One idea per line, key word first: `MUST NOT change the wire format`.
2. Tables for enumerable dimensions, prose for reasoning.
3. Checkboxes only for independently checkable assertions.
4. At least one done-when is a literal command, or for UI a named observable check (story, E2E, screenshot state).
5. Full backticked paths.
6. Errors and user feedback verbatim.
7. Plain assertions: `logged-out user hitting /decrypt → 401, no ciphertext in body`.
8. Appetite is a budget in the description; the estimate field is a forecast. Disagreement is signal.

## Voice

1. Imperative for work, present indicative for facts.
2. Delete hedges (*probably, maybe, ideally, try to*): each is a decision outsourced to the reader. Unknown → spike, or `MAY` and mean it.
3. Decisions without ceremony: "Use X". Inline rationale only when it prevents a wrong choice.
4. A decision made in a comment is edited into the description in the same sitting, with the comment as its record.
5. AI drafts need a subtraction pass: cut restated outcomes, "Summary" and "Next steps" sections.
6. Say what a thing is, never what it is not. Error copy says what happened and what to do next; it explains nothing about the system.

## Cut list

Outcome restated under a second heading · background the assignee has · Slack archaeology (the link is the evidence) · "As a user, I want…" · Gherkin · uncheckable checkboxes · "nice to have" in done-when · estimates in the body · boilerplate shared across issues · instructions on how to be an agent · pasted file contents.

## Quality score

One point each; state it when drafting or reviewing.

| # | Criterion |
|---|---|
| 1 | Imperative title ≤12 words |
| 2 | Outcome is one sentence of post-ship truth |
| 3 | Done-when: 2–6 observable assertions |
| 4 | ≥1 done-when is a command or named check |
| 5 | Scope has In, Out, Appetite |
| 6 | Under the cap |
| 7 | Every constraint severity-marked |
| 8 | Pointers name full paths and prior art |
| 9 | Hedge-free; open questions listed as open, not smuggled |
| 10 | Metadata: priority, category + module label, milestone, due date, estimate proposed, Design block complete when `area:ux` |

| Score | Action |
|---|---|
| 9–10 | Ready once the estimate is confirmed and the due date is set |
| 7–8 | Fix inline, note the gaps |
| ≤6 | Stays in shaping; propose the rewrite |

## Worked example (feature with a design stage)

```markdown
# Decryption rights page: list the rights a user granted across enabled chains

**Outcome.** A connected user opens one page and sees every active right they granted on any enabled chain, with grantee, what it can read, chain, granted date and expiry.

## Done when
- [ ] Top-level route; wallet menu links to it as "Manage decryption rights"
- [ ] One list across every enabled chain; unknown grantees shown as address with no name
- [ ] Loading until every chain answers; any chain failing shows one failure state and no rows
- [ ] Expired and revoked rights are not shown
- [ ] Row stays visible with an "Updating" marker after our own revoke until the indexer confirms
- [ ] One Storybook story per picture 1–7 and 10–12 of the storyboard
- [ ] `pnpm typecheck && pnpm test -- decryption-rights` passes; `decryption-rights-list.spec.ts` passes on the `indexer` project

## Scope
**In:** route, multichain query, list, empty and failure states, menu link.
**Out:** revoke (TEAM-325), external requests (TEAM-323), self-decryption permits.
**Appetite:** M, one PR.

## Why
A permission the user cannot find is not one they control. Project decisions: multichain because this is account management; all-or-nothing loading because "none" must never mean "unknown".

## Design
- Storyboard: <tldraw link>, page "Decryption rights page", pictures 1–7
- Frames: <Figma file>, frames 1–7; copy v1 in frame notes, owner marketing
- DS gaps filed: TEAM-39x (Table Row slots), TEAM-39y (Page Header aside)

## Pointers
- `apps/web/modules/wallet/` — session, menu
- `packages/ui/src/organisms/state-prompt-card.tsx`, `empty-state` — gate and empty conventions
- `apps/web/app/earn/_components/vaults-table.tsx` — table family to match

## Constraints
- MUST NOT show a partial list when a chain failed.
- MUST NOT import from `app/earn`; the integrator table lives in a module.
- MUST take every string as data.
```

## The one rule

Done-when above Why, one done-when a runnable command, and every picture on the storyboard accounted for. That makes "done" pass/fail for the engineer and "designed" pass/fail for the designer.
