---
name: teaching-artifact
description: Build a sectioned, shareable HTML artifact that teaches a system, an integration or a decision and surfaces its big risks fast. Outline gate first, then a structure chosen from the reader's purpose, step-by-step SVG diagrams, outcome matrices, risk cards and folds in place of prose, in the user's design-system colours. Use when the user wants to learn, review or brief others on a system, integration, vendor or set of options as a page or artifact ("teach me this in an artifact", "explainer page", "research page", "risk overview", "spike write-up"). Not for one focused diagram (show-me) or an explanation in chat (teach).
---

# Teaching artifact

A page a busy reader learns from in five minutes and returns to for detail. Design carries the meaning; prose is the last resort.

Scope. This skill owns the page's structure, visuals, copy and iteration. It borrows, and does not restate:
- Voice and diagram-by-diagram pacing: the `teach` skill.
- Gathering the facts: the `how` / `research` skills, or explorers you brief.
- The page contract (CSP, fonts, title, responsive rules): the Artifact tool's `quickstart` result, called with `intent: "other"`.

## 1. Check the evidence

Research comes before the outline. The page is shared, so its numbers become the team's numbers.

- Check yourself every number and claim that drives the recommendation. A subagent's figure stays the subagent's until you have re-read its source or re-run its query.
- When two reports disagree, read the cited source yourself. One read settles it; a third opinion does not.
- A "never" or "always" claim about a system's states is model-checked or dropped. Prose reasoning about state machines misses interleavings.
- Copy numbers and counts exactly as the source states them. A rounded count ("about 10") where the source lists 8 is an error a reader will find.

## 2. Choose the structure from the reader's purpose

Ask what the reader must decide or understand. Walk this tree:

```
What is the reader trying to do?
├── Learn a system and know its big risks
│     → Header · The task · Short answer + risk strip · How it works · Fit · Risks · Open decisions · Reference
├── Choose between alternatives (versions, vendors, designs)
│     → Header · The task · Short answer + risk strip · Shared base (once) · One section per alternative · Side by side · Shared risks · Open decisions · Reference
└── Understand one mechanism
      → Header · Short answer · Build-up sections, one per moving part · Gotchas · Reference
```

Branches combine. When a split into alternatives arrives mid-stream, restructure the whole page to the second branch; a bolted-on section breaks the reader's map of the page.

Each alternative's section has the same blocks in the same order (intro, how it works, outcomes, risks), because the reader compares by position. Same order, not same counts: never add a filler card to match the other section.

A risk every alternative carries goes once, in the shared risks, with one severity chip per alternative ("A: Med · B: High").

## 3. Outline gate

No HTML before the user approves an outline. Corrections to voice and density cost nothing before a page exists and a rewrite after. Use `references/outline-template.md`: per section the answer sentence, the visual and the folds, then a concrete voice-and-look block, then at most three questions.

- The user approves without answering a question: decide it, and name the decision in the delivery reply.
- The user asked to judge only the finished page: write the outline to a file, answer its questions yourself, build, and list the answers in the delivery reply.

## 4. Design system

When the user names a design system, take its colours and fonts. Otherwise use the quickstart defaults.

1. Read the semantic tokens: background, foreground, card, border, muted, primary, and the status roles with their tints.
2. Resolve each to a literal value from the primitives file. An artifact has no access to the system's variable chains.
3. Write them as tokens on bare `:root`, light values only: no dark blocks, every colour explicit, `body` background set.
4. Map status roles to bad, warn, ok, info, each as a tint background plus its on-tint text colour. They drive severity chips, outcome cells and gauges.
5. Map `--brand` to the system's accent that means "ours", not its primary button colour.
6. Replace every kit value, even ones that happen to match.
7. Fonts: display face for headings, body face, mono face for labels and figures. Inline a face that Google Fonts does not host as a base64 `@font-face`, heading weight only: write a placeholder, substitute the base64 into the same file once, keep no separate template.

The dark short-answer block is an inverse panel built from the same tokens; it is allowed on a light-only page.

## 5. Page anatomy

Every section has the same shape, so the reader learns it once:

1. Eyebrow: a mono label with the section number and scope, or a chip naming the alternative.
2. Heading.
3. One answer sentence the reader can stop at.
4. One primary visual directly under it. A second visual only when it answers a different question (how it works, then what happens when it breaks).
5. Folds (`<details>`) for anything a first read skips.

Density test: if a paragraph could be a table row, a chip, a gauge or a diagram step, convert it. Two paragraphs of prose in one section fails the test.

The page opens with a dark short-answer block: a verdict headline with one highlighted phrase, at most two sentences, then a strip of at most 5 risk chips. Each chip shows its severity label and links to its card. Order the chips by severity, then by harm to users' money, then by availability. Five is the ceiling because past it the first chips stop looking more urgent than the rest.

Provenance appears once, as header pills ("Research, nothing decided", "Checked on <date>"). Never tag individual claims as fact, inference or source. Flag uncertainty inline only where it changes a decision ("not yet tested on a fork").

Reference material stays in the closing folds: addresses, identifiers, error names, file paths, version numbers, audit lists, source links. In the main flow it is noise to a learner and reads as authority the prose has not earned.

## 6. Visuals

Pick the visual from the content's shape:

| Content | Visual |
|---|---|
| A flow with 3+ parts | Stepper: one inline SVG built up one part per step |
| How our flows behave in each state of an external system | Outcome matrix: states as rows, our flows as columns, outcome cells on ok/warn/bad tints |
| A live figure that sizes a risk | Gauge bar with the figure and its date under it |
| Two ways something can behave | Twin cards, each with a small chart and an outcome chip |
| Choosing between options | Side-by-side table |
| Detail a first read skips | Fold |

Load the `artifact-diagramming` skill before drawing the first SVG. Copy components from `references/kit.html`; do not reinvent them.

Steppers. Teaching a flow means redrawing it with one part added each time. On a page that is one SVG whose parts are `<g data-s="n">` groups revealed by step buttons. It opens on the last step so the whole picture shows at rest. The caption under it changes per step and reserves its height so the page does not jump.

Visual grammar. One encoding per property that matters, used in every diagram: our components in the brand tint, third-party components in the info tint, sensitive flows as dashed brand edges, hidden values as masked chips. Never encode one property two ways.

Failure states are drawn as nodes next to the component they affect, not as legend entries. Colour carries severity: red only for the worst outcome (stuck, or loss), amber for a recoverable one (retry, refund), green for success.

Emphasis means something stated. A coloured or bold table cell needs a key under the table; otherwise no emphasis. In a side-by-side table, mark the riskier cell, not the "winner".

A generated chart (model checker, tooling output) is never pasted as is. Redraw it with only the states the reader needs, in the reader's words, or turn its result into a caption under the outcome matrix. Mermaid renders natively from `<pre class="mermaid">`; `classDef` cannot read CSS variables, so copy the token's literal value there, the one allowed literal colour outside `:root`.

Phone first. At a 400 px viewport every table cell and diagram label reads without a sideways scroll:
- SVG viewBox at most 560 units wide, labels at 16 units or more, at most 4 boxes in a row. That renders labels near 10 px; an 800-unit viewBox with 11-unit labels renders them at 5 px.
- Annotations go under the node they describe.
- Outcome tables reflow into stacked rows below 600 px (kit `.matrix`). Chip labels stay at 3 words or fewer. The decisive cell is the one a scrolled column hides.

## 7. Copy

Follow `teach`'s voice: plain sentences, one name per concept, no framing labels. On top of that:

Terms
- Before publishing, list every term a newcomer may not know: the system's own component names, our internal names, third-party products, standard numbers, role names. Gloss each in 3 to 8 words where it first appears, tables included, or delete it. The reader is new to this system, so its own nouns are the jargon.
- Jargon is a missing reasoning step. "Only the admin can set a delegate" makes the reader ask what that means; say what happens to whom.

Claims
- A verdict states a fact and the condition under which it bites, using figures on the page: "a deposit above the remaining cap waits until the cap is raised". Never judge a third party's fitness or scale ("too small for us", "not production-ready") unless our side of the comparison is on the page too. Without it, the judgment is a guess dressed as a finding.
- Model results appear as outcomes in the reader's words ("retries, then refunds"), never as rule names or "breaks / holds".
- Promised structure exists. A sentence that says "ranked", "compared" or "in order" points at a list or table that shows the rank.
- One home per figure: the place where it drives a decision. It may appear once more, in the short answer. Repeated five times, a fact becomes noise.

Outcome cells and chips
- Outcome verb-phrases that name what the user gets: "Settles", "Refunds deposit at deadline", "Stuck until unpaused". Not adjectives.

Risk cards
- Anatomy, in order: title, severity chip, optional gauge, one or two sentences on what we lose, then one `→` mitigation line. Body text in the normal text colour: it is the content, not a caption.
- Calm, specific titles: "Withdrawals thin at high utilization", not "Bank run".
- Rate every risk on one scale across alternatives. If one option has far less of something, it cannot share the other option's rating for that risk.
- Severity matches what the team plans to do. A risk that bites only under a choice the team is not making is Low. If the product call is open, settle it or mark the rating conditional on it. A risk specific to one alternative is rated as if that alternative were chosen and sits in its section.
- A mitigation is an action our system can take. Trace it through the flow step by step, checking what the system can see and control at that moment; a check on a value the system does not know yet is not a mitigation. Messaging to users ("tell holders…") is a product call and goes to Open decisions as a question.

Safety and scope
- Say what stays safe once, where the reader's first fear lives (principal, earnings, user data), as a worked example or twin cards. Scope the claim to the states it holds in. On a risk card, add it only when it lowers the severity a reader would infer.
- Something the product chose not to do is not a risk. Mention it once, in one sentence, where it is relevant; never as a chip, card, table row or model rule.

Open decisions split into Product and Engineering columns. An element that looks clickable (pill, tab, chip) does something; a label that only describes is plain text.

## 8. Build, publish, verify

- The published file is the only source. Edit it in place and publish with `edits`. A split into template and body files makes the next rebuild silently undo every `edits` publish.
- Take the one rendered look the quickstart allows and spend it on what breaks most: 400 px width (tables, diagram labels), any hidden tab panel, a stepper's first and last step. Fix what you see, then publish.

## 9. Iterate

- The user asks what a passage means: answer in chat. Edit the page only to fix the framing, keeping the passage the same length or shorter. Do not raise severity or add work items in the same edit.
- Progressive disclosure repeats a fact in several layers (strip, card, comparison row, open decisions). Before changing a fact, search the page for every layer that states it and send all edits in one publish.
- Delete an open decision the moment the user answers it.
- A section from the approved outline that was cut or merged is named in the reply, with where its content went.
- Tell the user they can comment on a specific card; read those threads with the `ArtifactComments` tool.
- The first delivery reply is the link, the decisions you made for the user, and what you could not verify. Later replies are the link, what changed and any decision needed. Never recap the page in chat.

## Checklist

- [ ] Figures that drive the recommendation checked by you; contradictions resolved at the source
- [ ] Structure from the tree in section 2; alternatives share one block order
- [ ] Outline approved before HTML, or answered in a file when the user judges only the result
- [ ] Design-system tokens on `:root`, light only, status tints mapped, kit values replaced
- [ ] Every section: eyebrow, heading, answer sentence, one primary visual, folds
- [ ] At most 5 risk chips, labelled with severity, ordered
- [ ] One dated provenance pill; identifiers and sources only in reference folds
- [ ] Every newcomer term glossed where it first appears
- [ ] No judgment of a third party's fitness without our side on the page
- [ ] One severity scale across alternatives; every mitigation traced through the flow
- [ ] What stays safe said once, scoped; non-goals are one sentence
- [ ] Rendered at 400 px: every cell and diagram label readable
- [ ] Reply is link + decisions + what changed; no recap
