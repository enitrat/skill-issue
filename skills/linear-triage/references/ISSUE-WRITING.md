# Writing Issues

An issue is a prompt: the human skims it, the agent executes it. Both readers attend to the top and the end and lose the middle — humans by F-pattern scanning, LLMs by U-shaped positional attention. So the layout is **U-shaped**: the contract (outcome, done-when, scope) above the fold, binding constraints at the end, and the only skippable content — narrative — in the middle **dead zone**.

Length is not the variable to optimize; **position and density** are. The strongest evidence (3,180 agent-authored PRs, arXiv:2512.21426): self-contained issues merge +16.7% more, well-scoped +16.4%, named files +7% — while body length correlates *negatively* with success. Raise density, not word count. Full evidence and sources: [issue-writing-research.md](issue-writing-research.md) — read it when a rule here is challenged.

## The template

Fixed order, no exceptions:

```markdown
# <Imperative title: verb + object + qualifier, ≤12 words>

**Outcome.** One sentence: what is true after this ships that is not true now.

## Done when
- [ ] <observable assertion>
- [ ] <observable assertion>
- [ ] `<literal command that must pass>`        ← at least one, always

## Scope
**In:** <1–4 bullets>
**Out:** <1–4 bullets — the no-gos>
**Appetite:** <one PR | S | M | L>

## Why                                          ← ≤80 words; the dead zone carries the skippable part
<Two or three sentences, with the evidence link (Slack/report/parent). Or just a link.>

## Pointers
- `path/to/file.ts` — <why it matters, ~6 words>
- Prior art: <link or path>

## Constraints                                  ← last = recency position; severity in CAPS
- MUST NOT <...>
- MUST <...>
- SHOULD <...>
- MAY <...>

<collapsed appendix: logs, traces, schema dumps, alternatives considered>
```

Appendix mechanics: use a Linear collapsible section (`/collapsible`) with an informative summary line ("Appendix: full stack trace + repro env"). Collapsed content stays in the description string, so agents read it while humans skip it. Constraints stay visible — a collapsed MUST escapes human review. (Verify once that collapsibles survive the MCP round-trip; fall back to a trailing `## Appendix` heading if not.)

## Section contract — who reads what

| Block | Human | Agent |
|---|---|---|
| Title + Outcome + Done-when + Scope | **Read.** Answers: is this mine, how big, when am I finished. | Read; done-when is the definition of complete; run the commands. |
| Why | Skim or skip. | Disambiguate only — never expand scope from it. |
| Pointers | Skim. | Start here; fetch these files. |
| Constraints | Read the MUSTs. | Read all; violating a MUST fails the task regardless of tests. |
| Appendix | Skip. | Read. |

The contract makes "I didn't read that" a process error: load-bearing information in the skip zone is the author's fault, missed done-when is the reader's.

## Word budgets — hard caps

Counts exclude collapsed appendices and code blocks (pasted traces are free — verbatim evidence is high-signal).

| Type | Target | Cap | Required blocks |
|---|---|---|---|
| Chore / mechanical | 40–100 | 150 | Title, Outcome, one command |
| Bug | 120–220 | 300 | Title, Outcome, **Reproduction** (replaces Why), Done-when incl. failing test, Pointers |
| Spike | 120–250 | 300 | Question, **Timebox**, Deliverable (decision/doc/prototype), Kill criteria |
| Feature, one PR | 250–400 | 500 | Full template |
| Feature, multi-PR | 350–500 | 600 | Full template + parent/project brief carries the narrative |

Over the cap → it is not one issue. Split it, or move the design rationale into the project brief ([PROJECT-WRITING.md](PROJECT-WRITING.md)) and link it from Pointers. The brief carries the narrative so the issue doesn't have to.

### Variant notes

- **Bug:** Reproduction replaces Why — steps, environment, first occurrence, verbatim error. Developers rank repro steps and stack traces as the most valuable bug content; nobody needs a narrative about why a crash is bad. Hypotheses go in the appendix, labeled as hypotheses.
- **Spike:** the deliverable is a written decision; "no change" is a valid outcome. Kill criteria say when to stop digging. Spikes carry Timebox instead of Appetite — for a spike, the timebox *is* the appetite.

## Constraints: lock the contract, free the implementation

Constraints lock what breaking would hurt a consumer or a downstream issue: public API signatures, behavioral contracts, module boundaries, invariants, error contracts. Internal structure, naming, file layout, and implementation order stay free — the implementer decides. The test: would removing this line let a competent implementer make a *wrong* choice (not just a *different* one)? If no, cut it.

Severity uses RFC 2119 in ALL CAPS — MUST / MUST NOT / SHOULD / MAY — and nothing else. An unmarked constraint in prose is unenforceable: one reader hears mandatory, another hears optional.

**The harness rule:** a constraint that appears in a second issue moves out of issues entirely — into CLAUDE.md, a skill, or a CI check. Every promotion shortens all future issues at once and loses nothing.

## Formatting rules

1. One idea per line; front-load the line's key word (`MUST NOT change the wire format`, not `The wire format must not be changed`).
2. Tables for enumerable dimensions, prose for causal reasoning. A scope list under ~4 rows is cheaper as two bullets than a table.
3. Checkboxes only for independently checkable state transitions. `- [ ] code is clean` trains readers to ignore checkboxes.
4. At least one done-when is a literal command in backticks — it closes the agent's own verification loop instead of making you the loop. For UI work, the command's equivalent is a named observable check (screenshot state, E2E test).
5. Full backticked paths, no gestures: `modules/screening/hooks/use-prewarm-screening.ts`, not "the screening layer".
6. Paste errors and user feedback verbatim; never paraphrase a stack trace.
7. Plain assertions, not Gherkin: `logged-out user hitting /decrypt → 401, no ciphertext in body`. Given/When/Then triples the tokens for zero gain unless generating Cucumber tests.
8. Appetite is mandatory on features — it is the only line telling the implementer when to stop gold-plating. Appetite is a **budget** in the description; the estimate field is a **forecast** — when they disagree, that's signal, not error.

## Voice rules

1. Imperative for work, present indicative for facts: "`decrypt()` panics on empty input. Add a bounds check."
2. Delete every hedge — *probably, maybe, ideally, we might want to, try to*. Each is an unresolved decision outsourced to the reader; an agent resolves it arbitrarily and silently. Genuinely unknown → file a spike, or write `MAY` and mean it.
3. Decisions without ceremony: "Use X", not "We decided to use X". Inline rationale only when it prevents a wrong choice: `Use a BTreeMap (iteration order is part of the ABI)` earns its parenthetical; `(Bob suggested this)` doesn't.
4. Decisions made in comments get edited back into the description — comments are unreliable context and compete with the description for the agent's attention.
5. AI-drafted prose needs a subtraction pass: LLM drafts restate the outcome in three places and grow "Summary" and "Next steps" sections. The human edit is a cut.
6. Say what a thing is; never define it by what it isn't. A "note on the name" explaining what the work is *not* is a naming problem — rename the thing.

## Cut list — delete on sight

- The outcome restated under a second heading; "Summary"/"Conclusion" sections on a 400-word doc
- Background the assignee already has; meeting/Slack archaeology (who said what when) — the *link* is the evidence, not the retelling
- "As a user, I want…" framing; Gherkin wrappers around single assertions
- Uncheckable checkboxes; "nice to have" mixed into done-when (it's a separate issue or nothing)
- Estimates/points in the description (that's a field)
- Boilerplate identical across issues (→ harness rule)
- "Think step by step", "be careful" — instructions about how to be an agent
- Whole file contents pasted in — pass paths, let the agent read

## Quality scoring

One point each. State the score whenever drafting or reviewing.

| # | Criterion |
|---|---|
| 1 | Imperative title, ≤12 words |
| 2 | Outcome is one sentence stating the post-ship truth |
| 3 | Done-when: 2–6 observable, independently checkable assertions |
| 4 | ≥1 done-when is a runnable command (or named observable check) |
| 5 | Scope has In, Out, and Appetite |
| 6 | Under the word cap for its type |
| 7 | Every constraint severity-marked; none hiding unmarked in prose |
| 8 | Pointers name full paths and prior art |
| 9 | Hedge-free: no unresolved decision handed to the implementer |
| 10 | Metadata: priority, category + module label, evidence link, estimate proposed |

| Score | Action |
|---|---|
| 9–10 | Eligible for **Ready** once the estimate is human-confirmed |
| 7–8 | Note the gaps, fix inline |
| ≤6 | Stays in Backlog/Shaping; propose the rewrite |

## Worked example (feature, ~300 words — at cap density)

```markdown
# Reject malformed ciphertexts at the decryption boundary with a 400

**Outcome.** Malformed ciphertext input returns a structured 400-class error instead
of a panic-induced 500, so partners self-diagnose and our 5xx rate means "our fault" again.

## Done when
- [ ] Wrong length, unknown scheme id, and truncated payload each return a 400 with a distinct error code
- [ ] Error codes documented in `docs/api/errors.md`
- [ ] `pnpm test --filter fhevm-service decrypt-validation` passes, covering all three cases
- [ ] Existing decryption tests pass unchanged (correct clients see no behavior change)

## Scope
**In:** single-ciphertext decryption endpoint.
**Out:** encryption endpoint (→ SUP-###), key management, SDK error types, dashboards.
**Appetite:** one PR.

## Why
Partners send malformed ciphertexts; the FHE library panics; we return an opaque 500.
They open a support ticket, we read logs, it was a 47-byte payload. Report: <slack link>.

## Pointers
- `services/decrypt.ts` — add validation before the library call
- `services/errors.ts` — extend `ClientError`; expected length is parameter-set-dependent per key
- Prior art: input validation in `register-key.ts`

## Constraints
- MUST NOT panic on any input reachable from the request path.
- MUST NOT include raw input bytes or key material in error messages — they land in logs.
- MUST validate at the service boundary, not inside the FHE library (other consumers).
- SHOULD extend `ClientError` rather than introduce a parallel type.
```

What the 890-word draft of this lost in compression: nothing. Meeting archaeology (~95 words) changed no decision; the security paragraph became a MUST NOT that can actually bind; four prose invariants became done-whens or MUSTs; "batch path: maybe, if it's cheap" — the worst line, an unresolved scope decision an agent resolves silently — became a decided **Out**; hedges became severity markers; and the repro trace was *added*, free, in the appendix.

## The one rule if you keep only one

Done-when goes above Why, and one done-when is a runnable command. The reorder puts the contract where both readers actually look; the command makes "done" pass/fail instead of "looks done". Narrative-first structure is what invites narrative-length drafts — remove the opening act and the word count falls on its own.
