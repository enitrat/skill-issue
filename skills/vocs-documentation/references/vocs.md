# Vocs Setup for SDK Documentation

Setup guide for Vocs with the markdown extensions and code annotations used in SDK documentation.

Vocs is a Vite + Waku documentation framework. Pages are Markdown, MDX, or React components;
every MDX page is a React Server Component by default.

## Project Initialization

```bash
pnpm create vocs
```

Or add it to an existing project:

```bash
pnpm add vocs waku vite
```

**`package.json` scripts:**

```json
{
  "scripts": {
    "dev": "vocs dev",
    "build": "vocs build",
    "preview": "vocs preview"
  }
}
```

Dev server runs at `http://localhost:5173`.

## Project Structure

Vocs reads routes from `src/pages` by default (`rootDir` / `srcDir` can change this).

```
my-sdk/
  public/                  # Served at / — logos, favicon, fonts, images
  src/
    pages/
      index.mdx            # /
      react/               # Per-framework docs track
        getting-started.mdx
        guides/
        api/
          hooks/
            useQuery.mdx
      core/                # Framework-agnostic track
      snippets/            # Reusable MDX fragments (see below)
      _components/         # Ignored by routing — page-local components
      _hooks/              # Ignored by routing
      _api/                # API routes (_api prefix stripped from URL)
      _root.css            # Global styles / theme tokens
      _slots.tsx           # Footer, OutlineFooter, SidebarHeader
      _mdx-wrapper.tsx     # Wraps every MD/MDX page in this directory
    snippets/              # Real code files embedded via `[!include ~/...]`
      react/
        config.ts
  vocs.config.ts           # Site config: nav, theme, integrations
```

Routing rules:

- `src/pages/index.mdx` → `/`
- `src/pages/react/getting-started.mdx` → `/react/getting-started`
- `src/pages/reference/index.mdx` → `/reference`
- Any path segment containing `_components` or `_hooks` is never a route

**Files Vocs generates for you** — never hand-write or commit these:
`/llms.txt`, `/llms-full.txt`, `/sitemap.xml`, `/robots.txt`. The last two require `baseUrl`.

## Configuration

### `vocs.config.ts`

```ts
import { defineConfig, McpSource } from 'vocs/config'

export default defineConfig({
  title: 'My SDK',
  description: 'Documentation for My SDK',
  titleTemplate: '%s · My SDK',
  baseUrl: 'https://docs.my-sdk.dev',   // required for sitemap.xml / robots.txt

  logoUrl: { light: '/logo-light.svg', dark: '/logo-dark.svg' },
  iconUrl: '/favicon.svg',

  topNav: [
    { text: 'Guide', link: '/react/getting-started' },
    { text: 'API', link: '/react/api' },
    { text: 'GitHub', link: 'https://github.com/org/repo' },
  ],

  sidebar: {
    '/react': [/* see Navigation below */],
    '/core': [/* mirrors /react */],
  },

  twoslash: {
    inlineCache: true,      // persists type info next to snippets; warm CI builds
  },

  mcp: {
    enabled: true,
    sources: [McpSource.github({ name: 'my-sdk', repo: 'org/repo', paths: ['src'] })],
  },
})
```

Config file may be `vocs.config.ts`, `.mts`, `.js`, or `.mjs`. Use exactly one, at the project root.

### Navigation

Routes come from `src/pages`. **Discoverability comes from `sidebar` in `vocs.config.ts`.** A page
absent from the sidebar is invisible to readers browsing the site — treat adding a page and
updating the sidebar as one change.

```ts
export default defineConfig({
  sidebar: [
    { text: 'Getting Started', link: '/react/getting-started' },
    {
      text: 'Hooks',
      collapsed: true,            // collapse groups with > 5 items
      items: [
        { text: 'useQuery', link: '/react/api/hooks/useQuery' },
        { text: 'useMutation', link: '/react/api/hooks/useMutation' },
      ],
    },
    { text: 'GitHub', link: 'https://github.com/org/repo', external: true },
  ],
})
```

**Path-scoped sidebars** — the right shape for parallel framework tracks. Vocs picks the deepest
matching path prefix:

```ts
sidebar: {
  '/react': [/* React track */],
  '/core': [/* Core track — identical ordering */],
  '/reference': {
    backLink: true,
    items: [{ text: 'Site Config', link: '/reference/site-config' }],
  },
}
```

**Top nav highlighting** across a broader section:

```ts
topNav: [
  {
    text: 'Guide & API',
    link: '/react/getting-started',
    match: (path) => Boolean(path?.startsWith('/react') || path?.startsWith('/core')),
  },
]
```

`match` accepts a string prefix or a predicate function.

**Moving a page** means three edits in one commit: the file, the sidebar link, and a redirect.

```ts
export default defineConfig({
  redirects: [
    { source: '/guide/install', destination: '/react/getting-started/install' },
  ],
})
```

### Global styles

`src/pages/_root.css` is loaded automatically. Target `color-scheme` (not a `.dark` class) so
overrides follow the built-in theme toggle:

```css
:root {
  --vocs-color-accent: #7c3aed;
}

:root[style*='color-scheme:dark'],
:root[style*='color-scheme: dark'] {
  --vocs-color-background: #232225;
}
```

## Markdown Extensions Reference

### Headings with subtext

The single most useful Vocs-specific habit. `# Title [Subtext]` renders the bracketed text as page
subtext **and** backfills `title` / `description` frontmatter when they aren't set — which is what
`llms.txt` indexes.

```md
# useBalance [Fetch the native currency balance of an address]
```

### Frontmatter

Keep it minimal. Only these matter for SDK docs:

```yaml
---
title: useBalance
description: Hook for fetching native currency balance.
---
```

| Field | Use |
|---|---|
| `title`, `description` | Metadata + `llms.txt` entry. Set explicitly, or via `# Title [Subtext]`. |
| `layout` | `full` (default), `minimal`, `blank` |
| `outline` | `false` to hide the TOC, or a number to cap heading depth |
| `searchPriority` | `0` excludes the page from search; higher numbers boost it |
| `showSidebar` / `showTopNav` / `showLogo` / `showSearch` / `showAskAi` / `showFeedback` | Per-page UI overrides |

`filePath` and `lastModified` are injected at build time — don't set them.

### Callouts (Admonitions)

Container directives. All support a custom title in brackets, and can contain code blocks and
other directives.

```md
:::note
Default behavior note.
:::

:::info
Reassurance or context.
:::

:::tip
Helpful side-information.
:::

:::warning[Breaking change]
You must replace `apiKey` with your own key from the dashboard.
:::

:::danger
This method deletes data permanently. There is no undo.
:::

:::success
Your SDK is now configured and ready to use.
:::
```

`:::callout[Heads up]` is the generic form (renders as info with a custom title).

| Directive | Use for (in SDK docs) |
|---|---|
| `note` / `info` | Default behavior, context, "not ready to migrate yet?" |
| `tip` | Optional improvements, TypeScript conveniences |
| `warning` | Required config, breaking behavior, "you must do X" |
| `danger` | Destructive operations, security-critical info |
| `success` | Completion confirmation at the end of a tutorial |

Nesting requires more colons on the outer directive:

````md
::::warning[Read this first]
:::details[Why?]
Explanation.
:::
::::
````

### Steps

Native step-by-step UI. Use `#####` headings inside. This is the backbone of Getting Started pages
and task guides — no manual step numbering.

````md
::::steps
### Install the SDK

:::code-group
```bash [pnpm]
pnpm add my-sdk
```
```bash [npm]
npm install my-sdk
```
:::

### Create a config

```ts [config.ts]
import { createConfig } from 'my-sdk'

export const config = createConfig({
  baseUrl: 'https://api.example.com',
})
```

### Use it in your app

```ts [index.ts]
import { config } from './config'
import { getData } from 'my-sdk'

const result = await getData(config, { id: '123' })
```
::::
````

### Code Groups

Tab between related code blocks. Labels go in brackets after the language; icons resolve
automatically from the label text, and **package-manager tabs sync across the whole page**.

````md
:::code-group
```bash [pnpm]
pnpm add my-sdk
```
```bash [npm]
npm install my-sdk
```
```bash [yarn]
yarn add my-sdk
```
```bash [bun]
bun add my-sdk
```
:::
````

Always show the companion file alongside the main example:

````md
:::code-group
```tsx [App.tsx]
import { useQuery } from 'my-sdk/react'

export function App() {
  const { data } = useQuery({ key: 'users' })
  return <div>{data?.name}</div>
}
```
```ts [config.ts]
import { createConfig } from 'my-sdk'

export const config = createConfig({ baseUrl: 'https://api.example.com' })
```
:::
````

### Details

````md
:::details[Advanced TypeScript configuration]
To enable strict type inference, add the following to your `tsconfig.json`:

```json
{ "compilerOptions": { "strict": true, "noUncheckedIndexedAccess": true } }
```
:::
````

### Cards

For "Next Steps" sections and section landing pages:

```mdx
import { Card, Cards } from 'vocs'

<Cards>
  <Card
    title="TypeScript"
    description="Get the most out of type inference."
    icon="braces"
    to="/react/typescript"
  />
  <Card
    title="API Reference"
    description="Every hook, function, and config option."
    icon="book-open"
    to="/react/api"
  />
</Cards>
```

`Card` also accepts `topRight` (e.g. `topRight={<Badge variant="success">Stable</Badge>}`).

### Badges

Inline status labels via text directive:

```md
Vocs v2 is :badge[Beta]{warning}.
The Vite plugin is :badge[Stable]{success}.
This feature is :badge[Experimental].
```

Use these for deprecation markers next to API names, paired with a link to the migration guide.

### Tabs

For non-code content variants. Note the framework-variant rule in
[guides.md](guides.md#framework-specific-content): use parallel *pages* for framework tracks, not
tabs. `stateKey` syncs tab selection across the page.

```mdx
import { Tab, Tabs } from 'vocs'

<Tabs stateKey="workflow">
  <Tab title="Agent">Use a quick prompt for repeatable edits.</Tab>
  <Tab title="Author">Write Markdown and drop into JSX when needed.</Tab>
</Tabs>
```

### File Tree

Useful for scaffolding output in Getting Started pages. `+` prefixes folders, `**bold**`
highlights, trailing text becomes a comment, `{info="…"}` adds a hover tooltip.

```md
:::file-tree
- +src
  - +pages
    - **index.mdx**{info="The home page."}
    - getting-started.mdx
  - ...
- vocs.config.ts{info="Site config: nav, theme, integrations."}
- package.json
:::
```

### Prompts

Renders a copyable AI-agent instruction block, with URLs, inline code, and `<PLACEHOLDERS>`
highlighted. Good for "set this up for me" flows in Getting Started pages.

```md
:::prompt
Read https://docs.my-sdk.dev/react/getting-started and add My SDK to my app.

Requirements:
- Create `config.ts` with the SDK config
- Wrap the app root in the provider
- Replace <API_KEY> with the key from my dashboard
:::
```

### Terminal

Stitches a command and its output into one visual block. Use `ansi` for colored output.

````md
:::terminal
```bash
pnpm test
```
```ansi
\x1b[32m[PASS]\x1b[0m 12 tests passed
```
:::
````

Shell blocks whose lines start with `$` get per-line copy buttons, and the `$` is not copied.

### Mermaid

Fenced ```mermaid blocks render natively — no plugin. Use for architecture and lifecycle diagrams
on explanation pages.

### Inline code with highlighting

`` `console.log("hi"){:js}` `` renders as syntax-highlighted inline code. `{:ansi}` also works.

## Code Annotations

All annotations are comments inside the code block, so they never break the code.

| Annotation | Effect |
|---|---|
| `// [!code focus]` | Dims all other lines, focuses this one |
| `// [!code ++]` / `// [!code --]` | Green / red diff styling |
| `// [!code hl]` | Highlight |
| `// [!code word:name]` | Highlights every occurrence of `name` |
| `// [!code focus:3]` | Applies to the next 3 lines (the `:n` suffix works on most annotations) |
| `// [!code line-numbers]` | Enables line numbers for the block |
| `// [!code show-wrap]` | Shows the word-wrap toggle |
| `// [!code collapse:1 collapsed]` | Collapses a range, initially collapsed |
| `// [!code fold /regex/g]` | Folds regex matches (e.g. long class strings) |

Code block titles go in brackets in the meta: ```` ```ts [config.ts] ````.

**Annotations** are standalone comment lines that render as messages, and need no twoslash:

```ts
const a = 1
// @log: Custom log message
const b = 2
// @error: Custom error message
const c = 3
// @warn: Custom warning message
const d = 4
// @annotate: Custom annotation message
```

## Code Snippets

Three mechanisms, in increasing order of preference for SDK docs.

### Virtual file snippets

Declare a named block with `filename="…"`, then include it elsewhere in the same page. Good for a
config that several examples on one page share.

````md
```ts filename="client.ts"
import { createClient } from 'my-sdk'

export const client = createClient({ apiKey: process.env.API_KEY })
```

```ts
// [!include client.ts]
const user = await client.getUser({ id: '123' })
```
````

### Physical file snippets

Include real, compiling files from disk. `~/` resolves from `srcDir` (so `~/snippets/config.ts` is
`src/snippets/config.ts`). **This is the pattern to reach for** — the snippet is type-checked by
your own build, so it can't silently rot.

````md
```ts
// [!include ~/snippets/react/config.ts]
```
````

**Regions** pull out just part of a file:

```ts
// [!region setup]
import { createConfig } from 'my-sdk'
export const config = createConfig({ baseUrl: 'https://api.example.com' })
// [!endregion setup]
```

````md
```ts
// [!include ~/snippets/react/config.ts:setup]
```
````

**Find-and-replace** at render time — lets one source file serve several docs variants:

````md
```ts
// [!include ~/snippets/react/config.ts:setup /mainnet/optimism/]
```
````

### Markdown snippets (MDX includes)

Imported MDX compiles to a React component, so shared content is just an import — and props
replace VitePress-style template variables.

```mdx [src/pages/react/api/hooks/useBalance.mdx]
import QueryOptions from '../../../snippets/query-options.mdx'

## Parameters

<QueryOptions packageName="my-sdk" typeName="UseBalanceParameters" />
```

```mdx [src/pages/snippets/query-options.mdx]
#### enabled

`boolean | undefined`

Set to `false` to disable this query from automatically running.

#### gcTime

`number | Infinity | undefined`

Time in milliseconds that unused data remains in memory for {props.packageName}.
```

Use props for small variations — names, labels, type strings. If most of the content differs
between call sites, write separate snippets instead.

## TypeScript Twoslash

Add `twoslash` after the language tag for IDE-grade hover types, verified against the real
compiler at build time. A twoslash block that doesn't type-check **fails the build** — which makes
this the strongest guarantee available that your examples still compile.

````md
```ts twoslash
import { createConfig, http } from 'my-sdk'
import { mainnet } from 'my-sdk/chains'

const config = createConfig({
  chains: [mainnet],
  transports: { [mainnet.id]: http() },
})
//    ^?
```
````

| Syntax | Effect |
|---|---|
| `// ^?` | Shows the type of the identifier above the caret (leave a blank line after it) |
| `// ^\|` | Shows the autocomplete list at that position (needs `// @noErrors`) |
| `// ^^^` | Highlights a range of the line above |
| `// @errors: 2588` | Declares an expected compiler error and renders it |
| `// @noErrors` | Suppresses all errors in the block |
| `// ---cut---` | Hides everything above from the output (still type-checked) |
| `// ---cut-after---` | Hides everything below |
| `// @filename: a.ts` | Writes a virtual file — lets one block span multiple modules |
| `// @jsx: react-jsx` | Required for `.tsx` / JSX blocks |

Virtual-file snippets (`filename="…"`) also work with twoslash, so examples in a code group can
import from one another and keep full type information.

**Caching.** Twoslash invokes `tsc` per block. Results cache to `.vocs/cache/twoslash` by default.
Turn on `twoslash: { inlineCache: true }` to persist them as `// @twoslash-cache:` comments in your
Markdown source — the cache then travels with the repo, so fresh clones and CI start warm. It
rewrites your source files in place; commit the result. Only top-level (non-indented) fences are
supported. `TWOSLASH_INLINE_CACHE_IGNORE=1 vocs build` regenerates,
`TWOSLASH_INLINE_CACHE_REMOVE=1 vocs build` strips the comments.

Rust code blocks can use twoslash too, via `@vocs/twoslash-rust` and
`Twoslash.experimental_rust({ cargoToml: './Cargo.toml' })`.

## React in MDX

Every MDX page is a React Server Component. That is a genuine capability for SDK docs: a page can
read the filesystem, hit an API, or fetch release data at build time with no client JavaScript.

```tsx
// src/components/LatestVersion.tsx
import pkg from '../../../package.json'

export function LatestVersion() {
  return <code>{pkg.version}</code>
}
```

```mdx
import { LatestVersion } from '../components/LatestVersion'

The current release is <LatestVersion />.
```

Rules of thumb:

- Default to server components. Add `'use client'` only for browser APIs, state, or event handlers.
- Server → client is one-way: a client component cannot import a server component.
- Keep inline expressions small. If the logic feels like UI, move it into a component.
- **Every custom component needs a `toMarkdown` hook** or it degrades to raw JSX for agents. See
  [agent-readable-docs.md](agent-readable-docs.md#custom-component-markdown).

## SDK Documentation Patterns in Vocs

### Mapping doc types to Vocs features

| Doc type | Vocs features to reach for |
|---|---|
| **Tutorial** (Getting Started) | `::::steps`, `:::code-group` package-manager tabs, `:::prompt`, `:::success`, `<Cards>` for Next Steps |
| **How-to Guide** (Task Guide) | `::::steps`, code groups with `[filename]` labels, `// [!code ++]` diffs, `:::warning` |
| **API Reference** | `// [!code focus]` per-parameter examples, `twoslash` for inference, MDX snippets for shared options, `openapi` for HTTP APIs |
| **Explanation** (Concept page) | Prose, ```mermaid diagrams, `:::details` for deep dives |

### Per-parameter example pattern

Each parameter gets its own `###`, and the example focuses the one relevant line:

````md
### userId

`string | undefined`

User ID to fetch data for. Querying is disabled if `userId` is `undefined`.

```tsx [App.tsx]
import { useUserData } from 'my-sdk'

function App() {
  const result = useUserData({
    userId: 'usr_abc123', // [!code focus]
  })
}
```
````

### Verification loop

`vocs build` is the check. It fails on MDX errors, broken internal links, and twoslash type
errors — so a green build is a real signal that examples compile and cross-references resolve.
Pair it with `vocs markdown-audit` in CI to catch components that don't degrade to Markdown.

## Coming from VitePress or GitBook

| Feature | VitePress | GitBook | Vocs |
|---|---|---|---|
| Code groups / tabs | `::: code-group` | `{% tabs %}` | `:::code-group` |
| Code block title | ` ```ts [file.ts] ` | `{% code title=… %}` | ` ```ts [file.ts] ` |
| Admonitions | `::: warning` | `{% hint style="warning" %}` | `:::warning[Title]` |
| Expandable | `::: details` | `<details>` | `:::details[Title]` |
| Line focus / diff | `// [!code focus]` | Not available | `// [!code focus]`, plus `word:`, `collapse:`, `fold` |
| Step-by-step | Manual headings | `{% stepper %}` | `::::steps` (native) |
| File inclusion | `<<< @/snippets/f.ts` | `{% include %}` | `// [!include ~/snippets/f.ts:region]` |
| Shared markdown | `<!--@include: …-->` | Reusable content (Pro) | `import Snippet from './s.mdx'` + props |
| Template variables | `<script setup>` + `{{ }}` | Not available | MDX props / JSX expressions |
| TypeScript hover | `twoslash` | Not available | `twoslash` (+ inline cache, Rust) |
| Mermaid | Plugin | Embed | Native |
| OpenAPI rendering | Plugin | Native block | Native `openapi` config + `<OpenApi.*>` components |
| Search | Local / Algolia | AI-powered | MiniSearch by default, opt-in AI retriever |
| Agent output | Plugin | Not available | `.md` routes, `llms.txt`, `llms-full.txt`, MCP — all built in |
| Components in pages | Vue SFC | Not available | React Server Components |

Two migration traps:

1. **`<script setup>` has no equivalent.** Vue template variables become MDX props on an imported
   snippet component. Restructure shared content around props, not page-level variable declarations.
2. **`{% %}` blocks and `<<<` includes don't parse.** Container directives (`:::`) and
   `// [!include]` comments replace them.

## Minimal Dependency List

| Package | Purpose |
|---|---|
| `vocs` | The framework |
| `waku`, `vite` | Peer runtime (installed by `create-vocs`) |
| `@vocs/twoslash-rust` | (Optional) Rust type hints in code blocks |
