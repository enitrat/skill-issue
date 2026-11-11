---
name: teaching-artifact
description: Build a sectioned, shareable HTML artifact that teaches a system, a design proposal, an API or a decision, with progressive disclosure, real before/after comparisons, step-by-step diagrams, highlighted code and folds in place of prose. Outline gate first, then a page spine chosen from the reader's purpose, then a cold-reader test and a render check before publishing. Use when the user wants to learn, review, propose or brief others as a page or artifact ("teach me this in an artifact", "explainer page", "make an artifact about the API design", "before/after of the refactor", "research page", "risk overview", "spike write-up"). Not for one focused diagram (show-me) or an explanation in chat (teach).
---

# Teaching artifact

A page a reader who has never seen the system learns from in five minutes and returns to for detail. Design carries the meaning; every sentence left on the page teaches something the reader needs.

This skill owns the page's structure, visuals, copy and iteration. It borrows, and does not restate:
- Voice and diagram pacing: the `teach` skill.
- Gathering facts: `how`, `research`, or explorers you brief.
- The page contract (CSP, fonts, title, responsive rules): the Artifact tool's `quickstart` with `intent: "other"`.
- Drawing SVG: the `artifact-diagramming` skill, loaded before the first diagram.

## 1. Choose the spine from the reader's purpose

Ask who reads the page and what they must do after reading it. Walk this tree:

```
What must the reader do after reading?
├── Understand a system (to work in it, operate it, or join the team)
│     → Context · Short answer · The domain in one diagram · How it works, one moving part per section · Gotchas · Reference
├── Review or adopt a design or API (ours, or a proposal to another team)
│     → read references/code-visualisation.md; spine is defined there
├── Build what the page describes (a plan, a target architecture)
│     → Context · Short answer · The system as it will be · Parts, one per section · What it removes · Open questions · Reference
├── Choose between alternatives
│     → read references/risk-pages.md ("Alternatives")
└── Know the risks of something we depend on
      → read references/risk-pages.md ("Risks")
```

Rules that hold on every spine:
- **Domain first.** The first technical section names the domain's nouns and how they relate, in one diagram, before any integration, host application or implementation detail. Why: a page organised around how we integrate something teaches our plumbing, not the thing; the reader cannot judge a proposal whose primitives they were never shown.
- **Final state, not history.** The page describes the system as it is or will be. Rejected candidates, rubrics, decision logs and "how we got here" stay out, except on a choose-between-alternatives page, where the alternatives are the content. Why: a decision log makes the reader reconstruct the result; the page should hand it over.
- **Branches combine.** When a split into alternatives arrives mid-stream, restructure to that spine; a bolted-on section breaks the reader's map.

## 3. Disclosure ladder

The page is read in levels. Each level is complete on its own, and technicality only rises as the reader goes down:

| Level | What it holds | Reader time |
|---|---|---|
| L0 | Title + short answer block | 30 s |
| L1 | Context: the goal, who this is for, what material the page draws on (repo, PR, branch, date) | 1 min |
| L2 | Each section's eyebrow, heading, answer sentence and primary visual | 5 min total |
| L3 | Folds inside sections: mechanics, edge cases, full types, long code | on demand |
| L4 | Reference folds at the end: paths, identifiers, versions, sources, commands | lookup |

- Start wide: L0–L1 use no term the audience does not already know. A term is introduced at the first level that needs it, never earlier.
- The short answer's form follows the content: a verdict sentence for a risk page, three lines of code for an API page, one diagram plus a sentence for a system page. Never a strip of chips that a reader cannot learn from.
- Per section: eyebrow (mono label with section number and scope), heading, one answer sentence the reader can stop at, one primary visual directly under it, folds. A second visual only when it answers a different question.

## 4. Text budget: delete before you convert

For every paragraph, walk this in order:

```
Does the reader need what this paragraph teaches to do their job after reading?
├── No → delete it. Do not shorten it, do not turn it into a chip.
└── Yes
    ├── Is it a sequence, a comparison, a state change or a structure?
    │     → draw it (stepper, table, before/after, diagram) and delete the prose
    ├── Is it detail a first read skips? → move it into a fold
    └── Otherwise → keep it as at most 3 sentences
```

Hard limits:
- At most 3 sentences per paragraph, caption or list item outside folds. A section's visible prose is its answer sentence plus one caption per visual; a longer explanation is a sign the visual is wrong.
- Visible prose (outside folds, code, tables and diagram labels) stays under 900 words for the page.
- Chips hold labels only: a status, a severity, a kind, at most 3 words. A sentence cut down to fit a chip is noise.
- Check both with `python3 -I scripts/page_stats.py page.html` before every publish; it exits 1 when a limit is broken.

When the user says the page is too long: cut 40–50% of visible prose while keeping every mechanism, table, diagram and code block, then show the before/after word count. Do not cut to a third; overshooting loses the reasoning and the user has to ask for it back.

## 5. Visuals

Pick the visual from the content's shape:

| Content | Visual |
|---|---|
| A flow with 3+ parts | Stepper: one SVG built up one part per step |
| Today vs proposed, old vs new | Tabs or a Before/After toggle, "today" selected by default |
| How our parts behave in each state of something external | Outcome matrix: states as rows, our parts as columns, cells on ok/warn/bad tints |
| Code, types, API surfaces | Highlighted code block; see references/code-visualisation.md |
| Options to choose between | Side-by-side table whose rows are the axes that differ |
| A live figure that sizes a risk | Gauge bar with the figure and its date |
| Detail a first read skips | Fold |

- Copy components from `references/kit.html` (general) and `references/code-kit.html` (code). Do not reinvent them.
- Steppers open on the last step so the whole picture shows at rest; the caption changes per step and reserves its height.
- One encoding per property, used in every diagram: ours in the brand tint, third parties in the info tint, sensitive flows dashed. Red only for the worst outcome (stuck or loss), amber for recoverable, green for success.
- A coloured or bold cell, line or chip needs a key under it; emphasis without a key is noise.
- Generated output (model checker, profiler, codegen) is never pasted as is: redraw only what the reader needs, in the reader's words.
- Phone first: SVG viewBox at most 560 units wide, labels at 16 units or more, at most 4 boxes per row. At 400 px every table cell and label reads without sideways scroll.

## 6. Copy

Follow `teach`'s voice: plain sentences, one name per concept. On top of that:

- **Define before use.** List every term a newcomer may not know: the system's own nouns, our internal names, type and function names, third-party products. Each gets a 3–8 word gloss where it first appears, or is deleted. A type used in a code block is shown or glossed before that block. Why: a reader who meets an undefined noun stops learning and starts guessing.
- **Prefer the ecosystem's word.** Use the term the wider ecosystem (TypeScript, EVM, the framework in use) already has over one we coined. Rename a label in a diagram if a reader would ask what it means.
- **Claims carry their condition.** "A deposit above the remaining cap waits until the cap is raised", not "the cap is too small". Never judge a third party's fitness unless our side of the comparison is on the page.
- **Provenance once.** Header pills ("Proposal, nothing decided", "Checked on <date>", "Compared with <baseline>"). Never tag individual claims as fact, inference or source.
- **Promised structure exists.** "Ranked", "compared", "in order" point at a table that shows it.
- **One home per figure**: the place where it drives a decision, plus at most the short answer.
- Open decisions split into Product and Engineering. Delete an open decision the moment the user answers it.

## 7. Outline gate

No HTML before the user approves an outline built from `references/outline-template.md`. Corrections to structure, voice and density cost nothing before a page exists and a rewrite after.

- The outline names the audience and their baseline, the spine from section 2, the ladder from section 3, and a **cut list**: what the page will not contain. Users correct density on the outline; they can only do that if the cuts are visible.
- At most three questions, each one changing what you build.
- The user approves without answering: decide, and name the decision in the delivery reply. The user asks to judge only the finished page: write the outline to a file, answer its questions yourself, build.

## 8. Design system

When the user names a design system, take its colours and fonts; otherwise the quickstart defaults.

1. Resolve the system's semantic tokens (background, foreground, card, border, muted, primary, status roles with tints) to literal values from its primitives file.
2. Write them on bare `:root`, light values only, `body` background set. Replace every kit value.
3. Map status roles to bad, warn, ok, info as tint plus on-tint text. Map `--brand` to the accent that means "ours", not the primary button colour.
4. Fonts: display face for headings, body face, mono face for labels and code. A face Google Fonts does not host is inlined as a base64 `@font-face`, heading weight only, in the published file itself.

Keep the same components and colours across iterations of one page; the user notices when the renderer or the look changes between versions.

## 9. Test before publishing

Run both checks on every publish that adds or rewrites a section.

**Cold reader.** Spawn a fresh subagent with no conversation context. Give it the page's visible text and code (not the HTML), plus one line describing the audience from the outline. Ask it to: restate the short answer; restate each section's point in one sentence; list every term it could not define from the page; for a comparison, name what differs between the options. Every miss is a rewrite instruction: fix the page, not the reader. Why: you cannot unknow the context you built the page from; a reader without it is the only test of whether the page teaches.

**Render.** Open the built page in a headless browser before publishing:
- Zero console errors.
- Click every tab, toggle, step and fold; each shows content.
- Screenshot at 400 px and at desktop width and look at both: tables, code blocks, diagram labels, any hidden panel.
- Never publish a page whose script you have not run, and never splice an old script into a new file; rebuild the script whole.

## 10. Build and iterate

- The published file is the only source. Edit it in place and publish with `edits`. Keep a copy of each published version beside it (`page.v<N>.html`) so a regression can be restored.
- After a large rewrite, give the cold reader the previous and the new version and ask which teaches better. If the old one wins, restore it and redo the change smaller.
- The user asks what a passage means: answer in chat. Edit the page only to fix the framing, keeping the passage the same length or shorter.
- Progressive disclosure repeats a fact across levels (short answer, section, fold, reference). Before changing a fact, search the page for every place it appears and change all of them in one publish.
- A section from the approved outline that was cut or merged is named in the reply with where its content went.
- The first delivery reply is the link, the decisions you made for the user, and what you could not verify. Later replies are the link, what changed and any decision needed. Never recap the page in chat.

## Checklist

- [ ] Every requirement traced to a source; "today" read from the audience's real baseline
- [ ] Spine from section 2; domain nouns shown before any integration; no decision log on a non-choice page
- [ ] Ladder L0–L4 holds; L0–L1 use no unknown term; short answer teaches something
- [ ] `page_stats.py` passes: ≤ 3 sentences per paragraph or caption, < 900 visible words; no sentence turned into a chip
- [ ] Every comparison shows a real "today" next to "proposed", today selected by default
- [ ] Every term, type and coined label glossed or shown before use
- [ ] Every emphasis has a key
- [ ] Outline approved, with audience, baseline and cut list
- [ ] Cold reader restated every section and named no undefined term
- [ ] Rendered: no console errors, every control clicked, 400 px and desktop looked at
- [ ] Reply is link + decisions + what could not be verified; no recap
