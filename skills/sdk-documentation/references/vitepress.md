# VitePress Setup for SDK Documentation

Setup guide for VitePress with all markdown extensions used in SDK documentation.

## Project Initialization

```bash
pnpm add -D vitepress @shikijs/vitepress-twoslash
npx vitepress init
```

Recommended directory structure:

```
site/
  .vitepress/
    config.ts            # Site configuration
    sidebar.ts           # Sidebar extracted to separate file
    theme/
      index.ts           # Theme customization + twoslash registration
      style.css          # Custom CSS
  react/                 # Per-framework docs
    getting-started.md
    api/
      hooks/
  core/                  # Framework-agnostic docs
  shared/                # Reusable markdown fragments (never rendered directly)
  snippets/              # Reusable code files for embedding
    react/
      config.ts
  index.md               # Home page
```

**`package.json` scripts:**

```json
{
  "scripts": {
    "dev": "vitepress dev site",
    "build": "vitepress build site",
    "preview": "vitepress preview site"
  }
}
```

## Configuration

### `.vitepress/config.ts`

```ts
import { defineConfig } from 'vitepress'
import { createTwoslashWithInlineCache } from '@shikijs/vitepress-twoslash/cache-inline'
import { getSidebar } from './sidebar'

const withTwoslashInlineCache = createTwoslashWithInlineCache()

export default withTwoslashInlineCache(
  defineConfig({
    title: 'My SDK',
    description: 'SDK documentation',
    lang: 'en-US',
    cleanUrls: true,
    lastUpdated: true,

    head: [
      ['link', { rel: 'icon', href: '/favicon.svg' }],
    ],

    markdown: {
      theme: {
        light: 'vitesse-light',
        dark: 'vitesse-dark',
      },
    },

    themeConfig: {
      logo: { light: '/logo-light.svg', dark: '/logo-dark.svg', alt: 'logo' },

      nav: [
        { text: 'Guide', link: '/guide/getting-started' },
        { text: 'API', link: '/api/overview' },
      ],

      sidebar: getSidebar(),
      outline: [2, 3],

      editLink: {
        pattern: 'https://github.com/org/repo/edit/main/site/:path',
        text: 'Suggest changes to this page',
      },

      socialLinks: [
        { icon: 'github', link: 'https://github.com/org/repo' },
      ],
    },
  }),
)
```

### `.vitepress/sidebar.ts`

Extract sidebar into a separate file for maintainability:

```ts
import type { DefaultTheme } from 'vitepress'

export function getSidebar() {
  return {
    '/react': [
      {
        text: 'Introduction',
        items: [
          { text: 'Getting Started', link: '/react/getting-started' },
          { text: 'Installation', link: '/react/installation' },
        ],
      },
      {
        text: 'Hooks',
        collapsed: true,     // Collapsible for large groups
        items: [
          { text: 'useBalance', link: '/react/api/hooks/useBalance' },
        ],
      },
    ],
  } satisfies DefaultTheme.Sidebar
}
```

### `.vitepress/theme/index.ts`

Register twoslash floating component:

```ts
import DefaultTheme from 'vitepress/theme'
import TwoslashFloatingVue from '@shikijs/vitepress-twoslash/client'
import '@shikijs/vitepress-twoslash/style.css'

export default {
  extends: DefaultTheme,
  enhanceApp({ app }) {
    app.use(TwoslashFloatingVue)
  },
}
```

## Markdown Extensions Reference

### Code Groups

Tab between multiple code blocks:

````markdown
::: code-group
```ts [config.ts]
export const config = createConfig({ /* ... */ })
```
```js [config.js]
module.exports = { /* ... */ }
```
:::
````

### Line Annotations

| Annotation | Effect |
|---|---|
| `// [!code focus]` | Dims all other lines, focuses this one |
| `// [!code ++]` | Green diff-added styling |
| `// [!code --]` | Red diff-removed styling |
| `// [!code hl]` | Yellow highlight |
| `// [!code error]` | Red underline |
| `// [!code warning]` | Yellow underline |

Multiple consecutive lines can each carry annotations.

### File Inclusion (Snippets)

Import external code files into code blocks. `@` resolves to the VitePress source root.

```markdown
<<< @/snippets/react/config.ts
```

With tab label inside a code group:

```markdown
::: code-group
<<< @/snippets/react/config.ts[config.ts]
:::
```

With line highlighting:

```markdown
<<< @/snippets/snippet.ts{1,3-5}
```

**Region extraction** — import a labeled section from a file:

In the source file:
```ts
// #region setup
import { createConfig } from 'sdk'
export const config = createConfig({ /* ... */ })
// #endregion setup
```

In markdown:
```markdown
<<< @/snippets/react/config.ts#setup
```

### Shared Markdown Includes

Include one markdown file inside another:

```markdown
<!--@include: @shared/installation.md-->
```

Or with relative path:

```markdown
<!--@include: ../shared/installation.md-->
```

Included files have full access to all VitePress markdown features and Vue template variables from the parent.

### Custom Containers (Admonitions)

```markdown
::: info
Informational note.
:::

::: tip
Helpful tip.
:::

::: warning
Warning about potential issues.
:::

::: danger
Critical / breaking info.
:::

::: details Click to expand
Hidden content revealed on click.
:::
```

Custom titles:

```markdown
::: warning Important
Replace the `projectId` with your own!
:::
```

### Template Variables (`<script setup>`)

VitePress markdown files are Vue SFCs. Define variables in `<script setup>`:

```markdown
<script setup>
const packageName = 'my-sdk'
const typeName = 'GetBalance'
const TData = '{ decimals: number; value: bigint; }'
</script>

# useBalance

## Import

```ts-vue
import { {{typeName}} } from '{{packageName}}'
```
```

The `-vue` suffix on the language tag (e.g., `ts-vue`, `bash-vue`) enables `{{ }}` interpolation inside code blocks.

### Conditional Rendering in Shared Files

Use Vue `v-if` / `v-for` in markdown to conditionally show content based on variables from the including page:

```markdown
<div v-if="!hideOptions?.includes('gcTime')">

#### gcTime

`number | Infinity | undefined`

The time in milliseconds that unused/inactive cache data remains in memory.

</div>
```

**Shared file variable defaults**: Wrap `<script setup>` in an HTML comment so the including page's variables take precedence:

```markdown
<!--
<script setup>
const packageName = 'my-sdk'  // default, overridden by parent
</script>
-->

Install `{{packageName}}`:
```

### TypeScript Twoslash

IDE-like hover type annotations in code blocks. Add `twoslash` after the language tag:

````markdown
```ts twoslash
import { createConfig, http } from 'my-sdk'
import { mainnet } from 'my-sdk/chains'

const config = createConfig({
  chains: [mainnet],
  transports: {
    [mainnet.id]: http(),
  },
})
//    ^?
```
````

| Syntax | Effect |
|---|---|
| `// ^?` | Shows the type of the identifier above the caret |
| `// @errors: 2322` | Declares expected TypeScript errors (renders visually) |
| `// ---cut---` | Hides setup code above from rendered output (still type-checked) |

The `createTwoslashWithInlineCache()` wrapper in config.ts caches twoslash results as `// @twoslash-cache: { ... }` comments in the source markdown, speeding up builds.

### Package Manager Tabs

Combine code groups with tab labels:

````markdown
::: code-group
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

For dynamic versions with `<script setup>`:

````markdown
::: code-group
```bash-vue [pnpm]
pnpm add my-sdk@{{version}}
```
```bash-vue [npm]
npm install my-sdk@{{version}}
```
:::
````

**Optional: Group Icons Plugin** for package manager icons in tabs:

```bash
pnpm add -D vitepress-plugin-group-icons
```

```ts
// config.ts
import { groupIconMdPlugin, groupIconVitePlugin } from 'vitepress-plugin-group-icons'

export default defineConfig({
  markdown: {
    config(md) {
      md.use(groupIconMdPlugin)
    },
  },
  vite: {
    plugins: [groupIconVitePlugin()],
  },
})
```

```ts
// theme/index.ts
import 'virtual:group-icons.css'
```

## Minimal Dependency List

| Package | Purpose |
|---|---|
| `vitepress` | Static site generator |
| `@shikijs/vitepress-twoslash` | TypeScript hover annotations |
| `vitepress-plugin-group-icons` | (Optional) Package manager icons in tabs |
