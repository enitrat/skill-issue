# Code visualisation: API and codebase design pages

Read this when the page proposes, reviews or explains a public API, a module boundary, a type model or a refactor. The reader learns the design from code they can read, not from prose about code. Components are in `code-kit.html`.

## Spine

Walk it in order. Skip a section only when the cut list in the outline says why.

| # | Section (Diátaxis mode) | Answers | Primary visual |
|---|---|---|---|
| 0 | Short answer | What is the shape, in one breath? | 3 lines of code: define, call, what you get back |
| 1 | Context (explanation) | Goal, audience, what we compared against (repo, branch, version, date) | Three short cards |
| 2 | The domain (explanation) | Which nouns exist and how they relate | One diagram of the nouns, no API names yet |
| 3 | Consumers (explanation) | Who calls this, and what job each one does | One row per consumer: what they own, what they need from the API |
| 4 | Today (reference) | What a consumer writes now | Real excerpt per consumer, cited |
| 5 | What breaks (explanation) | Why today is wrong, concretely | Failure cards |
| 6 | Proposed surface (reference) | Every entry point and what it returns | Table: entry point · sync/async · what it reads · returns, with Today/Proposed tabs |
| 7 | Usage (how-to) | How a consumer uses it end to end | Tabs, one per consumer stack |
| 8 | Before/after in our code (explanation) | What changes in a real codebase | Switcher: area tabs × Before/After toggle |
| 9 | What it removes | What disappears | Deleted-files chips with line counts, in a fold |
| 9a | Guarantees (explanation), when the design enforces rules | Which rule each type, load-time check or CI check holds | Table: rule in plain words · enforced by |
| 9b | Rollout (how-to), when it ships in steps | In what order it lands, each step shippable alone | Table: step · release it needs · change · what it deletes |
| 10 | Open questions | What the reader must decide | Product / Engineering columns |
| 11 | Reference | Full types, all exports, source paths, how to run the tests | Folds only |

Why this order:
- Domain and consumers come before any API. A proposal judged without its primitives reads as an opinion. A page built around our host app's integration teaches our plumbing, not the API.
- Today comes before proposed, from the real source. Without it the reader cannot see what is wrong, only what is new.
- Each section's eyebrow shows its Diátaxis mode (Reference, Explanation, How-to). One mode per section, so the reader knows whether to read or look up.

## Today must be real

- Read "today" from the source on the audience's baseline: the branch the other team works on, not a release we happen to have installed. Name it in a header pill ("Compared with @scope/pkg 3.8.0-beta.17, checked on <date>").
- Excerpts are verbatim, trimmed with `// …`, never paraphrased into code that does not exist. If you shorten an identifier or drop arguments, the excerpt is no longer "today".
- What-breaks cards state: today's behaviour (with the type or function that causes it) | what breaks for which consumer | the fix in the proposal. One snippet per card, inside the fold. The summary row alone must teach the failure.
- Add one fold listing what today does that the proposal drops. A comparison that hides what the old design did well is not trusted.

## Code blocks

- Every block has a one-line header: the file path or a label ("today: host code to send one redeem"), plus the line count for real files ("179 lines · deleted").
- 15 lines visible at most. Longer code goes in a fold, or is trimmed with `// …`.
- Highlight the lines that carry the point, at most 3 runs and at most a third of the block's lines. A block with everything highlighted teaches nothing.
- Highlight colours carry one meaning page-wide, with a key under each block that uses them: brand tint = what the proposal adds or the call the reader should copy; bad tint = what the consumer must stop writing (protocol knowledge, manual encoding, duplicated rules).
- Use comments in code only to point at the highlighted line's reason, one per run, ≤ 10 words. The prose under the block does not restate them.
- Syntax highlighting is Prism from cdnjs, pinned (`prism@1.29.0` with the typescript, jsx and tsx components), applied per line so highlights survive (see `code-kit.html`).
- After building, print the highlighted lines of every block with a script and read them. Off-by-one highlights are the most common defect on these pages.

## Usage examples must compile

- Write each usage example as a file in a scratch package that depends on the real packages (or the proposal's type sketch), and run `tsc --noEmit --strict` on it. Zero errors before the code goes on the page.
- If an example cannot compile (the API does not exist yet), compile it against the type sketch, and mark the page with a "Sketch: compiled against the proposal's types" pill.
- Examples are standalone: a Node script and a frontend app that do not use our own app's frameworks (flow engine, internal hooks). Our app appears only in the before/after section. Why: a reader from another team must see the API without learning our infrastructure.
- Usage uses syntax the ecosystem and the codebase already use. A new pattern (generators, builders, a DSL) is introduced with a 3-line explanation of what problem it solves before it appears.

## Types and naming

- Every type a code block uses is shown or glossed before that block. Full types go in a reference fold; the section shows only the fields the reader needs at that moment.
- State each naming convention in one sentence next to the surface table ("`prepare*` returns calls and never sends; the bare verb sends with the SDK's signer"). The reader will otherwise ask why two names differ.
- The surface does not ask authors to choose an internal mode they cannot reason about. If the page shows an option like that, it names who decides it and why the author cannot get it wrong.

## Before/after switcher

- Area tabs across the top (one per refactored area: deposit, redeem, registry, …), a Before/After toggle beside them. Opens on the first area, After selected; Before is one click.
- Each side shows the real files with their headers and line counts. Before highlights in bad tint what moved out; After highlights in brand tint the call that replaced it.
- One "why" line under each pair: what moved where, and what the app still owns. No second paragraph.

## Short answer

Three lines of code a reader can learn the shape from, plus at most one sentence on what the API does not do:

```ts
const group = defineVaultGroup({ id, chainId, asset, vaults })
const prepared = await vaults.prepareDeposit({ group, vaultId, account, amount })
await yourEngine.send(prepared.calls)
```

Never a chip strip on an API page.
