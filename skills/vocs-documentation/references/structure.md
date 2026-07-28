# Documentation Structure

Rules for organizing an SDK documentation site on Vocs.

## Site Architecture

Organize docs into parallel tracks per framework/variant, each mirroring the same structure:

```
src/pages/
  framework-a/          # e.g. react/
    getting-started.mdx
    guides/             # Task-oriented how-to guides
    api/                # API reference pages
      hooks/            # (or functions/, composables/, classes/, etc.)
      config/
      plugins/          # (or adapters/, connectors/, providers/, etc.)
  framework-b/          # e.g. vue/ — mirrors framework-a structure
  core/                 # Framework-agnostic version
  snippets/             # Reusable MDX fragments (never rendered directly)
src/snippets/           # Real code files embedded via `[!include ~/…]`
```

### Key principles

1. **Mirror structure across variants.** Every framework track uses identical directory layout and sidebar ordering. Readers switching frameworks find docs in the same place.
2. **Shared content lives in `src/pages/snippets/`.** Write once, import everywhere. Give shared fragments `searchPriority: 0` so they never surface as standalone search results.
3. **Snippets are real code files.** Store reusable config, schema, and boilerplate in `src/snippets/` — embed via `// [!include ~/snippets/…]` rather than duplicating. Those files compile in your own build, so they can't silently rot.

## Sidebar / Navigation

Routes come from the `src/pages` tree; the sidebar is declared in `vocs.config.ts`. **A page absent
from the sidebar is invisible to browsing readers** — add the page and the sidebar entry in the
same change.

Order sidebar sections by the reader's journey:

1. **Introduction** — Why, Installation, Getting Started, TypeScript
2. **Guides** — Task-oriented (e.g. Authentication, Data Fetching, Error Handling)
3. **Configuration** — Config creation, storage, providers
4. **API Reference** — Hooks/functions alphabetically, grouped by domain if > 30 items
5. **Miscellaneous** — Errors, Utilities, FAQ

Use `collapsed: true` on sub-groups with > 5 items to keep the sidebar manageable.

Use the **object form of `sidebar`** to give each framework track its own tree — Vocs picks the
deepest matching path prefix:

```ts
export default defineConfig({
  sidebar: {
    '/react': [
      { text: 'Getting Started', link: '/react/getting-started' },
      {
        text: 'Hooks',
        collapsed: true,
        items: [{ text: 'useBalance', link: '/react/api/hooks/useBalance' }],
      },
    ],
    '/core': [/* identical ordering, /core links */],
  },
})
```

Pair a `topNav` `match` predicate with these tracks so the correct top-level tab stays active
across the whole section. See [vocs.md → Navigation](vocs.md#navigation).

When a page moves, add a `redirects` entry in the same commit.

## Frontmatter

Keep frontmatter minimal:

```yaml
---
title: useBalance
description: Hook for fetching native currency balance.
---
```

Only `title` and `description` — and both can come from `# useBalance [Fetch the native currency
balance of an address]` instead. No tags, categories, or sidebar metadata; the sidebar config
handles navigation.

The description is not decoration: it is the page's entire entry in `llms.txt`. Never ship a page
without one.

Exceptions worth setting deliberately:

| Field | When |
|---|---|
| `searchPriority: 0` | Shared MDX snippets that are never rendered standalone |
| `layout: minimal` / `blank` | Landing pages, marketing-style index pages |
| `outline: false` | Very short pages where a TOC is noise |

## Page Templates

Every page type follows a rigid template. Predictability is a feature.

### API Reference Page (Query/Read)

```
# hookName [One-line summary]

## Import
## Usage
## Parameters
  ### paramA
  ### paramB
  ---  (horizontal rule separates core from optional params)
  ### optionalParamC
## Return Type
## Underlying API  (link to lower-level library or core function)
```

### API Reference Page (Mutation/Write)

Same as query but includes mutation-specific shared content (onSuccess, onError, mutate, mutateAsync).

### Guide Page

```
# Task Title [What the reader will accomplish]
1-2 sentence description + hook/function references.

## Example  (interactive playground embed FIRST)

::::steps
### 1. Prerequisite reference
### 2. Create skeleton
### 3. Add logic
### 4. Integrate SDK hook
### 5. Add loading state (optional)
### 6. Handle errors (optional)
### 7. Wire it up!
::::
```

### Getting Started Page

```
# Getting Started [Install and configure the SDK]

## Overview  (one sentence + link to "Why")

## Automatic Installation  (CLI scaffolding, plus a :::prompt block for agent-driven setup)
## Manual Installation
::::steps
### Install
### Configure
### Wrap in Provider
### Use
::::

## Next Steps  (<Cards> with 3-4 curated links)
```

Use `::::steps` rather than manually numbered headings — no renumbering when a step is inserted.

## Content Reuse System

Vocs has no page-level template variables. Shared content is an imported MDX component, and
variation comes through **props**.

### Pattern: Shared content with props

**Wrapper page** (per framework):

```mdx
import Balance from '../../snippets/getBalance.mdx'

# useBalance [Fetch the native currency balance of an address]

<Balance packageName="my-sdk" actionName="getData" typeName="GetData" />
```

**Shared fragment** (`src/pages/snippets/getBalance.mdx`, with `searchPriority: 0`):

````mdx
---
searchPriority: 0
---

## Import

```ts
import { {props.actionName} } from '{props.packageName}'
```
````

For anything longer than a few interpolations, prefer a **physical code snippet** in
`src/snippets/` included with `// [!include ~/snippets/react/config.ts:setup]`. It type-checks as
part of your build; an interpolated string does not.

### Pattern: Shared option/result blocks

Extract common parameter groups (e.g. TanStack Query options, mutation results) into dedicated MDX
fragments. Import them into every page that uses those patterns. To omit an option on a specific
page, pass it as a prop and branch in the fragment — MDX is React, so a conditional is a plain
expression:

```mdx
{!props.hide?.includes('gcTime') && <GcTime />}
```

## Cross-Referencing

1. **Within same section**: absolute route paths `[createConfig](/react/api/createConfig)`
2. **Cross-section**: full paths `[writeContract](/core/api/actions/writeContract)`
3. **External**: full URLs `[TanStack Query docs](https://tanstack.com/query/v5/docs/...)` — Vocs adds `target="_blank" rel="noreferrer"` automatically
4. **Same-page anchors**: `[enabled](#enabled)`, `[abi](#abi)`
5. **Deprecation markers**: `:badge[Deprecated]{warning}` next to the name, linking to the migration guide

Prefer absolute route paths over relative file links. They survive file moves, and they're what
`vocs build` validates.

## Code Example Conventions

| Convention | Usage |
|-----------|-------|
| `:::code-group` | Always show companion files (config, schema/types) alongside main example |
| `// [!code focus]` | Highlight the relevant line in per-parameter examples |
| `// [!code ++]` / `// [!code --]` | Show additions/removals in migration and step-by-step guides |
| `// [!include ~/snippets/…]` | Embed reusable config/schema files rather than duplicating |
| `twoslash` blocks | Demonstrate TypeScript type inference; the build fails if they stop compiling |
| Package manager tabs | Always show pnpm, npm, yarn, bun for install commands — Vocs syncs the selection across the page |
| ```` ```ts [config.ts] ```` | Label every code block with its filename |
