# Agent-Readable Documentation

Vocs serves the same source twice: rendered HTML for humans, raw Markdown for machines. This file
covers the machine surface — what it is, what it demands of your writing, and how to verify it.

This is not an optional extra. For an SDK, a large share of readers are now agents writing code on
someone's behalf. A page that only works in a browser is a page half your audience can't use.

## What Vocs Serves to Agents

| Surface | What it is | Configuration |
|---|---|---|
| `.md` routes | Any page as raw Markdown: `https://docs.example.com/getting-started.md` (home page: `/index.md`) | None |
| User-agent detection | Known AI crawlers automatically receive Markdown instead of HTML | None |
| `/llms.txt` | Concise index — every page's title, path, and description | None |
| `/llms-full.txt` | Entire docs concatenated into one Markdown file | None |
| MCP server | `list_pages`, `read_page`, `search_docs` (+ source tools) at `/api/mcp` | `mcp: { enabled: true }` |
| Ask AI menu | In-page AI menu; surfaces the MCP URL for readers to copy | Enabled with AI features |

Detected AI user agents include `ClaudeBot`, `anthropic-ai`, `claude-web`, `GPTBot`,
`OAI-SearchBot`, `ChatGPT-User`, `PerplexityBot`, `Google-Extended`, `MistralAI-User`, `cohere-ai`,
and others. Search crawlers (`Googlebot`, `Bingbot`, `Applebot`) still get HTML, so SEO is
unaffected.

## Writing Rules That Follow From This

These are the concrete authoring consequences. They apply to every page type.

1. **Every page needs a real description.** `llms.txt` is title + path + description, nothing else.
   A missing description makes the page a blank entry in the only index most agents read first.
   Get it from `# Title [Subtext]` or explicit frontmatter — see
   [vocs.md → Headings with subtext](vocs.md#headings-with-subtext).

2. **Headings are the retrieval unit.** Task-based (`## Handle Errors`, `## Configure Retries`),
   not categorical (`## Notes`, `## Miscellaneous`). An agent chunking your page keeps headings and
   throws away layout.

3. **One topic per page.** Retrieval returns pages, not paragraphs. A page covering auth, caching,
   and error handling gets returned for all three queries and satisfies none of them.

4. **No placeholder examples.** `foo`, `TODO`, and `// your code here` are worse than nothing: an
   agent will faithfully reproduce them in a user's codebase. Every example must be real and
   runnable.

5. **Prose density is a token budget.** Padding a human skims past is context an agent pays for.
   The terse-fragment rule for parameter descriptions
   ([tone.md](tone.md#parameter-descriptions)) is a token-efficiency rule as much as a style one.

6. **State behavior explicitly; never rely on layout.** Bold text, column position, and card
   placement carry no meaning in Markdown. If optionality matters, put it in the type
   (`string | undefined`). If ordering matters, say so in words.

7. **Interactive content needs a Markdown fallback.** See `toMarkdown` below.

## Custom Component Markdown

Any custom MDX component without a `toMarkdown` hook reaches agents as an opaque JSX tag — the
information it conveys is simply missing from `.md`, `llms.txt`, and `llms-full.txt`.

Define the hook alongside the component. It returns a Markdown AST node (or array of nodes) and is
invoked *only* when generating agent-facing Markdown, so interactive rendering is untouched.

```tsx
// src/components/ClientPrompt.tsx
const prompt = 'Add my-sdk to my app as a client.'

export const ClientPrompt = Object.assign(
  function ClientPrompt() {
    return <pre>{prompt}</pre>
  },
  {
    toMarkdown: () => ({
      type: 'code',
      lang: 'text',
      value: prompt,
    }),
  },
)
```

```mdx
import { ClientPrompt } from '../components/ClientPrompt'

<ClientPrompt />
```

The hook fires for standalone MDX tags. For an SDK site, the components that most need it are
interactive playgrounds, live demos, generated API tables, and version/badge widgets — exactly the
components whose content a reader would otherwise have to see rendered to understand.

### Auditing

```bash
vocs markdown-audit
```

Dry-renders every page and reports components that survive as MDX in agent-facing output, grouped
by component with the affected pages and a suggested fix. It exits `1` when anything is
unrendered — wire it into CI next to `vocs build`. `--json` gives machine-readable output.

```txt
[vocs] Markdown audit found 1 component left after dry rendering 1 page (2 occurrences).

Components:
  InteractiveWidget (2 occurrences)
    Fix: add `InteractiveWidget.toMarkdown` to return a Markdown AST node.
    /guides/setup (2 occurrences)
```

## MCP Server

Exposes docs — and optionally source code — to AI clients over Model Context Protocol at
`/api/mcp`. For an SDK this is the highest-leverage feature in Vocs: an agent that can read both
your docs *and* your implementation stops guessing at signatures.

```ts
// vocs.config.ts
import { defineConfig, McpSource } from 'vocs/config'

export default defineConfig({
  mcp: {
    enabled: true,
    sources: [
      McpSource.github({ name: 'my-sdk', repo: 'org/my-sdk', paths: ['src'] }),
    ],
  },
})
```

| Tools | When exposed |
|---|---|
| `list_pages`, `read_page`, `search_docs` | `mcp.enabled` |
| `list_sources`, `list_source_files`, `read_source_file`, `get_file_tree`, `search_source` | `mcp.sources` configured |
| `submit_feedback` | `mcp.enabled` **and** `feedback` configured |

Notes and limits:

- `search_docs` is text search over page files, not a semantic embedding index.
- Set `GITHUB_TOKEN` for higher rate limits and authenticated code search.
- Only paths you explicitly configure are exposed. Private sites belong behind your existing auth.
- `http://localhost:5173/api/mcp` works only for clients on the same machine.
- Generated Markdown pages carry a prelude naming the MCP endpoint and pointing at `search_docs`
  (and `submit_feedback`, when configured). That prelude is not repeated in `llms.txt`.

Document the endpoint in your own Getting Started page. Readers who use agents will want it, and
they won't discover it on their own:

```md
:::tip
Point your AI agent at our MCP server so it can search these docs and read the SDK source:
`https://docs.my-sdk.dev/api/mcp`
:::
```

### Non-GitHub sources

```ts
McpSource.from({
  name: 'workspace',
  type: 'custom',
  async listFiles(path) { /* … */ },
  async readFile(path) { /* … */ },
  async getTree(options) { /* … */ },
})
```

## Search

Keyword search (MiniSearch) is on by default with no configuration: Vocs indexes title, subtitle,
text, and category fields at build time and fetches the index on first search.

```ts
export default defineConfig({
  search: {
    fuzzy: 0.2,
    prefix: true,
    combineWith: 'AND',
    boost: { title: 4, subtitle: 3, text: 2, category: 1, titles: 1 },
  },
})
```

Per-page control via frontmatter:

```yaml
---
searchPriority: 5    # higher ranks higher; 0 excludes the page entirely
---
```

Set `searchPriority: 0` on shared MDX snippet files that are never rendered standalone — otherwise
fragments surface as results. This replaces the "exclude shared/ from search" step other frameworks
need.

**AI search** is opt-in and additive: keyword results appear instantly, semantic results blend in as
they arrive. Configure one retriever under `ai.retriever` — `Retriever.cloudflare({ instance })` to
delegate the index to a hosted backend, or `Retriever.local()` to have Vocs chunk and embed pages
at build time into a static vector store it owns. Retriever credentials are server-side only and
are never serialized to the browser.

## Page Feedback

```ts
import { defineConfig, Feedback } from 'vocs/config'

export default defineConfig({
  feedback: Feedback.slack(),
  mcp: { enabled: true },
})
```

With both configured, agents can file feedback through the same adapter as readers via
`submit_feedback` (fields: `pagePath`, `helpful`, optional `category` and `message`). Vocs adds the
page URL and timestamp. For an SDK, this is a direct channel for "the docs said X but the API does
Y" reports from agents mid-task — treat that queue as a bug tracker for the docs.

## Prompts for Maintaining Docs

Vocs' own guidance is that agents do best with an explicit task, the guides to read, the files to
edit, and a verification command. When delegating docs work, use that shape.

**Adding a page:**

```txt
Add a Vocs page at src/pages/react/guides/authentication.mdx for developers integrating auth.

Explain the happy path first, include one minimal runnable code example, add a troubleshooting
section, and add the page to the sidebar in vocs.config.ts.

Then run `pnpm build` and fix any broken links or MDX errors.
```

**Files agents should edit** — and nothing else:

| File | Purpose |
|---|---|
| `vocs.config.ts` | Title, description, navigation, integrations, theme |
| `src/pages/**/*.md` | Markdown-only pages |
| `src/pages/**/*.mdx` | Pages using imports, JSX, or Vocs components |
| `src/pages/_root.css` | Global styles and theme tokens |
| `public/**` | Logos, images, favicons, fonts |

Generated files (`llms.txt`, `llms-full.txt`, `sitemap.xml`, `robots.txt`, `.vocs/`), build output,
and unrelated application code are off-limits.

**Useful audit prompts:**

```txt
Audit these docs as a first-time developer using this SDK. List missing pages, unclear examples,
and navigation problems.
```

```txt
Rewrite this page for agent retrievability: task-based headings, a concise description, no
placeholder examples.
```

```txt
Find code examples in the docs that no longer match the SDK source and update them.
```

The last one is where an MCP `sources` entry pays off — the agent can diff docs against
implementation directly instead of trusting either.

## Checklist Before Shipping

- [ ] Every page has a `description` (explicit, or via `# Title [Subtext]`)
- [ ] Headings are task-based
- [ ] No placeholder or non-runnable examples
- [ ] Custom components define `toMarkdown`; `vocs markdown-audit` exits `0`
- [ ] Shared MDX snippets carry `searchPriority: 0`
- [ ] New pages appear in the `vocs.config.ts` sidebar
- [ ] Moved pages have `redirects` entries
- [ ] `vocs build` passes (MDX, internal links, twoslash types)
- [ ] `baseUrl` is set so `sitemap.xml` and `robots.txt` generate
