# Tutorials & How-to Guides

Tutorials and how-to guides are both practical, but they serve fundamentally different readers. Tutorials teach someone who is *learning*. How-to guides help someone who is *working*. Never conflate them — this is the single most common conflation in software docs, and the distinction is study vs work, never basic vs advanced (a how-to can cover something mundane; a tutorial can teach experts an advanced skill). Boundary tests in [diataxis.md](diataxis.md).

## Two Distinct Types of Practical Documentation

| | **Tutorial** (Learning) | **How-to Guide** (Working) |
|---|---|---|
| **Reader** | Beginner building mental model | Competent user solving a problem |
| **Goal** | Reader acquires skills & confidence | Reader accomplishes a specific task |
| **Voice** | "we" — building alongside the reader | "you" — directing an able practitioner |
| **Scope** | Complete journey, no shortcuts | Focused on one task, start-to-finish |
| **Explanation** | Minimal — link out, don't teach inline | Zero — action only |
| **Options** | Eliminate — one path, no detours | Acknowledge — real-world complexity |
| **Examples** | Getting Started, First App | Authentication, Data Fetching, Error Handling |

## Other Guide Types

| Type | Purpose | Example |
|------|---------|---------|
| Concept Guide | Explain an integration pattern (→ see [Explanation Pages](tone.md#explanation--concept-pages)) | TanStack Query, Error Handling, SSR |
| Migration Guide | Upgrade between major versions | v1 → v2 breaking changes |
| FAQ | Address common questions | Q&A format with short answers |

---

## Tutorials (Learning-Oriented)

Tutorials include Getting Started pages and any "First X" walkthrough. The reader is learning — they don't yet know what questions to ask.

### Tutorial-Specific Rules

1. **Show the destination early.** Tell the reader what they'll have built by the end. Screenshot or interactive demo before step 1.
2. **Deliver visible results at every step.** Each step produces output the reader can verify: "You should see..." / "The output looks like..." A `:::terminal` block pairing the command with its real output is the cleanest way to show this. Flag known failure signs too: "If you don't see X, you probably forgot Y." Say "In this tutorial we will build..." — never "you will learn..."
3. **Eliminate options.** One path. Don't mention alternatives — they fracture the learner's focus. Save "you could also..." for how-to guides.
4. **Minimize explanation.** If a concept needs > 2 sentences of explanation, link to a concept page instead. The tutorial is for *doing*, not *understanding*.
5. **Guide observation.** Point out what the reader should notice: "Notice that the hook returns `undefined` until the query resolves."
6. **Ensure repeatability.** Pin versions, provide exact config, test the tutorial end-to-end. A tutorial that doesn't work destroys trust.

### Getting Started Structure

Show the destination first — screenshot, demo, or description of what the reader will have built by the end.

Offer two paths:

### Path 1: Automatic (fastest start)
CLI scaffolding command — one line to a working project. Consider adding a `:::prompt` block so
readers can hand setup to their agent verbatim:

```md
:::prompt
Read https://docs.my-sdk.dev/react/getting-started and add My SDK to my app.

Requirements:
- Create `config.ts` with the SDK config
- Wrap the app root in the provider
- Replace <API_KEY> with the key from my dashboard
:::
```

### Path 2: Manual (full control)
Wrap the steps in `::::steps` — 4 steps, always in this order:
1. **Install packages** — with inline one-line dependency descriptions
2. **Create config** — central configuration object
3. **Wrap in provider** — framework integration (skip for vanilla)
4. **Use the SDK** — first working code

Use `::::steps` rather than manually numbered headings. Inserting a step later then costs nothing.

### End with "Next Steps"
Curate 3-4 links. `<Cards>` gives them visual weight and forces a one-line description on each:

```mdx
import { Card, Cards } from 'vocs'

<Cards>
  <Card title="TypeScript" description="Get the most out of type inference." to="/react/typescript" />
  <Card title="Authentication" description="Set up user authentication." to="/react/guides/authentication" />
</Cards>
```

A plain bolded link list is equally acceptable and reads better in Markdown output:

```markdown
- [**TypeScript**](/react/typescript) Learn how to get the most out of type inference.
- [**Authentication**](/react/guides/authentication) Set up user authentication.
```

---

## How-to Guides (Task-Oriented)

How-to guides serve competent users who know what they want to accomplish. The reader is *working*, not *learning*.

### How-to Guide Rules

1. **Assume competence.** The reader already knows the SDK basics. Don't re-explain setup or foundational concepts — link to the tutorial.
2. **Action only.** Every sentence either tells the reader to do something or shows them code. No teaching, no theory, no background.
3. **Name the task in the title.** "Authenticate Users", "Fetch Data", "Handle Errors" — not "Auth Guide" or "Data Overview". Task-based titles are also what search and `llms.txt` match on.
4. **Address real-world complexity.** Unlike tutorials (which eliminate options), how-to guides should acknowledge variations with conditional imperatives: "If you're using a custom transport, pass it via..." A guide useful for exactly one narrow case and nothing adjacent is rarely worth having.
5. **Start and end at meaningful points.** Don't repeat setup from Getting Started. Begin where the reader's real problem begins. Practical usability beats completeness.
6. **Frame around the user's problem, not the machinery.** "Click Deploy to deploy" is a feature walkthrough addressed to no need. A real guide answers a human project — and may cut across several APIs or tools to do it; the user's goal defines its scope, not the product's feature list.

### Task Guide Template

```
# [Task Title] [What the reader will accomplish]

[1-2 sentence description. Name the hooks/functions used. Reference prerequisite guide.]

## Example
[Interactive playground embed — show the FINISHED result FIRST]

::::steps
### [Prerequisite reference]
### Create component skeleton
### Add form/logic handler
### Integrate SDK hook
### Add loading state (optional)
### Handle errors (optional)
### Wire it up!
::::
```

### Rules

1. **Example first.** Show the interactive playground before the walkthrough. Readers see the end result before committing.
2. **One concept per step.** A step adds a hook OR error handling OR loading state — never multiple.
3. **Label optional steps.** Mark enhancement steps with `(optional)` in the heading. Core path should be 3-4 steps.
4. **Full files at every step.** Every code block is a complete, runnable file. Use `:::code-group` to show all related files with `[filename]` labels.
5. **Diff-based evolution.** Use `// [!code ++]` / `// [!code --]` to show what changed. Don't explain changes in prose when diffs are clear.
6. **Chain guides via references**, not repetition. Step 1 should link to the prerequisite guide, not re-explain setup.

## Progressive Disclosure

Layer information from simple to advanced:

| Level | Content | Audience |
|-------|---------|----------|
| Core path (steps 1-4) | Minimal working example | Beginners |
| Optional steps (5-7) | Loading, errors, receipts | Intermediate |
| `:::details` blocks | TypeScript tips, advanced config | Power users |
| Concept guides | Integration patterns, caching | Advanced |

### Techniques

- **`:::details[Advanced TypeScript configuration]`** for optional deep configuration
- **Separate concept guide pages** for deep integration patterns (e.g., TanStack Query internals)
- **FAQ** as a safety net for edge cases
- **"Read from Contract" pattern**: each section is self-contained — reader can stop after section 1 with a working example

Don't hide anything load-bearing behind `:::details`. Collapsed content is still fully present in
the Markdown served to agents, but a human scanning the page will miss it — so a required step
belongs in the step list, not in a details block.

## Framework-Specific Content

### Separate pages, not tabs

Maintain parallel page trees per framework, with a path-scoped sidebar per track (see
[structure.md](structure.md#sidebar--navigation)). Do NOT use `<Tabs>` within a page for framework
variants — one URL per variant is what makes a framework's docs linkable and retrievable.

- Identical structure (same steps, same headings)
- Framework-idiomatic code (React hooks vs Vue composables vs Solid primitives)
- Shared conceptual content via imported MDX snippets

### Package manager tabs ARE tabs

The one exception: install commands always show pnpm/npm/yarn/bun in a `:::code-group`. Vocs
recognizes package manager labels and syncs the selection across the entire page, so the reader
picks once.

## Prerequisites Communication

### Inline, not in a separate section

Explain dependencies at point-of-use with one-line descriptions:

```markdown
- [Axios](https://axios-http.com) is an HTTP client for the browser and Node.js.
- [TanStack Query](https://tanstack.com/query/v5) is an async state manager.
- [TypeScript](/react/typescript) is optional, but highly recommended.
```

### Guide chaining

Reference prerequisite guides inline rather than listing prerequisites at the top:

```markdown
The following guide builds on the [Authentication guide](/react/guides/authentication)
and uses the [useSubmit](/react/api/hooks/useSubmit) hook.
```

### Warnings for critical requirements

Use a `:::warning` callout for configuration that will break things if missing:

```md
:::warning
Replace the `projectId` with your own Project ID!
[Get your Project ID](https://dashboard.example.com/)
:::
```

## Code Example Progression

### Multi-file code groups at every step

Show all relevant files together in a `:::code-group`, each labeled with its filename:

````md
:::code-group
```tsx [send-transaction.tsx]
// main component
```
```ts [config.ts]
// SDK config
```
:::
````

### Final step shows ALL files

The "Wire it up!" step includes every file in the code group, giving the reader the complete picture.

### Diff annotations show evolution

```tsx
import { useSendTransaction } from 'my-sdk' // [!code ++]
import { parseAmount } from 'my-sdk/utils' // [!code ++]

export function SendTransaction() {
  const { data: hash, sendTransaction } = useSendTransaction() // [!code ++]
```

### Keep examples honest with snippets and twoslash

For any example that must stay correct across releases, prefer including a real file
(`// [!include ~/snippets/react/send-transaction.tsx]`) or marking the block `twoslash`. Both are
verified by `vocs build`, so a breaking change in the SDK fails the docs build instead of silently
shipping a wrong example.

## Migration Guides

### Structure

```markdown
# Migrate from vX to vY [What changed and how to upgrade]

## Overview
[1-2 paragraphs: WHY the major change exists]

[Install command in a :::code-group]

:::info
Not ready to migrate yet? The vX docs are still available at [X.x.sdk.sh](url).
:::

## Breaking Changes
### [Change name]
[Before/After code with // [!code --] and // [!code ++]]

## Deprecations
### [Deprecated API]
[Replacement code + rationale]
```

### Rules

1. **Always provide an escape hatch.** Link to previous version's docs.
2. **Explain the "why" for every removal.** "This gives you more control" or "Reduces bundle size."
3. **Show before/after as diffs.** Use `// [!code --]` / `// [!code ++]` for every API change.
4. **Group by impact.** Breaking changes first, then deprecations.
5. **Mark deprecated APIs at the source.** Add `:badge[Deprecated]{warning}` next to the name on the API reference page, linking to the relevant section of this guide.

## Error Handling Pattern in Guides

Error handling is always an optional step using a consistent pattern:

1. Import the base error type
2. Destructure `error` from the hook
3. Display with type narrowing: `(error as BaseError).shortMessage || error.message`

Dedicated error handling guides show TypeScript type discrimination for specific error types.
A `twoslash` block with `// @errors:` is the clearest way to show what the compiler rejects.

## FAQ Pattern

Use H2 headings as questions. Each answer is 2-5 sentences or a short code snippet. End with a redirect to community discussions for anything not covered.

```markdown
## Type inference doesn't work
[Checklist of 3 things to verify]

## My widget doesn't connect
[Guidance to try alternatives]
```

Question-shaped headings are the one place categorical headings are wrong for a different reason:
they should match how readers actually phrase the problem, because that phrasing is what search and
agent retrieval match against.
