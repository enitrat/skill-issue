# API Reference Documentation

Rules for writing API reference pages for hooks, functions, classes, and configuration objects.

**Reference describes and only describes.** A reference page is not a tutorial (don't teach), not a how-to guide (don't instruct), and not an explanation (don't justify). It provides truth, precision, and consistency. If you catch yourself writing "you should" or "this is useful when", that content belongs in a different page type — link to it instead.

## Page Template

Every API reference page follows a rigid section order. Predictability is the goal — readers learn the template once and navigate all pages by muscle memory.

### Query/Read API (hook or function that fetches data)

```
# hookName [One-line summary of what it fetches]

## Import
[import statement]

## Usage
[code group: main file + config + optional schema/types]

## Parameters
[type import]
### paramA
[type, description, code example]
### paramB
[type, description, code example]
---
### optionalParamC
[type, description, code example]

[shared query/read options — imported MDX snippet]

## Return Type
[type import]
[shared query result fields — imported MDX snippet]

## Action / Underlying API
[link to lower-level API]
```

### Mutation/Write API (hook or function that changes state)

Same as query but with:
- Mutation-specific shared options (onSuccess, onError, onSettled)
- Mutation-specific return fields (mutate, mutateAsync, isIdle)
- Optional `## Type Inference` section for schema/type inference

### Configuration Object

```
# createConfig [Create the SDK configuration object]

## Parameters
[type import]
### option (per option, with code examples)

## Return Type / Config
### property (per returned property)
### method (per returned method, with usage examples)
```

## Parameter Documentation

Each parameter gets its own `###` heading. Never use tables for parameters.

### Format per parameter

````markdown
### userId

`string | undefined`

User ID to fetch data for. [`enabled`](#enabled) set to `false` if `userId` is `undefined`.

:::code-group
```tsx [App.tsx]
import { useUserData } from 'my-sdk'

function App() {
  const result = useUserData({
    userId: 'usr_abc123', // [!code focus]
  })
}
```
```ts [config.ts]
// [!include ~/snippets/react/config.ts]
```
:::
````

### Rules

1. **Type on its own line** in backticks. No "Type:" prefix, no table column.
2. **Description is a terse fragment**, not a full sentence: "The resource's schema." not "This parameter accepts the schema of the resource."
3. **Every parameter gets a complete code example** with the relevant line marked `// [!code focus]`.
4. **Optional vs required** is communicated through the type itself: `| undefined` means optional. No badges. This matters doubly on Vocs — a visual "optional" marker would vanish in the Markdown served to agents, whereas the type never does.
5. **Horizontal rules (`---`) separate parameter groups**: core params above, optional/advanced below.
6. **Parameters section starts with type import**: `import { type UseBalanceParameters } from 'sdk'`
7. **Cross-link inferred params**: "Inferred from [`schema`](#schema) and [`methodName`](#methodname)."
8. **Heading text is the anchor.** `### userId` yields `#userid`, and that's what every cross-reference and agent citation targets. Renaming a parameter heading breaks inbound links — add a redirect or keep the old anchor.

## Return Type Documentation

### For hooks wrapping async state managers (TanStack Query, SWR, etc.)

Import a shared MDX snippet for standard return fields (data, error, status, isLoading, refetch, etc.). Only document the data shape specific to this hook:

````markdown
## Return Type

```ts
import { type UseBalanceReturnType } from 'sdk'
```

### data

`{ id: string; name: string; metadata: Record<string, unknown>; }`

The fetched resource data.

<QueryResult typeName="UseBalanceReturnType" />
````

### For core functions

Document return fields individually:

```markdown
### items

`readonly [T, ...T[]]`

Fetched items from the data source.

### totalCount

`number`

Total number of matching items.
```

### For mutation hooks

Document `mutate` and `mutateAsync` with their parameter types, then standard mutation fields via an imported snippet.

## TypeScript Type Presentation

### Inline backtick types
For parameter and return value types, use inline backticks:
```
`Address | undefined`
`'latest' | 'earliest' | 'pending' | 'safe' | 'finalized' | undefined`
`config['chains'][number]['id'] | undefined`
```

### Import statements
Start Parameters and Return Type sections with the type import:
```ts
import { type UseBalanceParameters } from 'sdk'
```

### Type inference demonstrations
Use `twoslash` blocks for hover types and autocomplete. These are compiler-verified, so a signature
change fails `vocs build` instead of leaving a stale example:

````md
```ts twoslash
import { useQuery } from 'my-sdk/react'
// ---cut---
const result = useQuery({
  schema: mySchema,
  method: 'getUser',
})

result.data
//     ^?
```
````

| Twoslash marker | Use in reference pages |
|---|---|
| `// ^?` | Show the inferred type of a result or field |
| `// ^\|` | Show the autocomplete options for a union-typed parameter (needs `// @noErrors`) |
| `// @errors: 2322` | Demonstrate what the compiler rejects (e.g. an invalid method name) |
| `// ---cut---` | Hide setup imports so the block stays focused but still type-checks |

### Dedicated Type Inference section
For APIs with schema/type inference, add:
```markdown
## Type Inference

With [`schema`](#schema) configured, TypeScript infers correct types for
[`method`](#method), [`params`](#params), and the return type.
See the [TypeScript docs](/react/typescript) for more information.
```

### Complex nested types
Show inline as type literals. Do not create separate type pages for one-off shapes:
```
`{ id: string; name: string; createdAt: Date; }`
```

## Cross-Referencing

Every API reference page should cross-reference related APIs:

| Section | Links to | Example |
|---------|----------|---------|
| `## Underlying API` | Underlying core function | `[getData](/core/api/actions/getData)` |
| `## Underlying API` | External library function | `[fetch](https://lib.dev/docs/fetch)` |
| Parameter descriptions | Other params on same page | `Inferred from [schema](#schema)` |
| Parameter descriptions | Config/Provider pages | `[Config](/react/api/createConfig#config)` |
| Type Inference section | TypeScript guide | `[TypeScript docs](/react/typescript)` |
| Deprecation badges | Migration guide | `:badge[Deprecated]{warning}` + `[migration guide](/react/guides/migrate-v2#change)` |

Use absolute route paths, not relative file paths — `vocs build` validates them, and they survive
file moves.

## Error Documentation

### Per-function error types
Core function pages include an `## Error` section with the error type import:
````markdown
## Error

```ts
import { type GetDataErrorType } from 'my-sdk'
```
````

### Hook error handling
Hooks delegate errors to the async state manager. The shared result snippet documents the `error` field typed to the specific `ErrorType`.

### Centralized errors page
List all error classes by category with name, one-line description, and import statement. No elaborate explanation needed.

## Shared Content System

Vocs has no page-level template variables. Shared reference blocks are **imported MDX components**,
and per-page variation comes through **props**.

### Props for type interpolation

Each page passes the types its shared blocks need:

```mdx
import QueryOptions from '../../snippets/query-options.mdx'
import QueryResult from '../../snippets/query-result.mdx'

# useBalance [Fetch the native currency balance of an address]

## Parameters

<QueryOptions packageName="my-sdk" typeName="UseBalanceParameters" />

## Return Type

<QueryResult
  TData="{ decimals: number; value: bigint }"
  TError="GetBalanceErrorType"
/>
```

The snippet consumes them as `{props.TData}`, `{props.typeName}`, and so on. Give every snippet
`searchPriority: 0` in its frontmatter so fragments never surface as standalone search results.

### Key shared files to maintain

| File | Content | Used by |
|------|---------|---------|
| `snippets/query-options.mdx` | Read/query parameters (enabled, gcTime, staleTime) | All query hooks |
| `snippets/query-result.mdx` | Read/query return fields (data, error, status) | All query hooks |
| `snippets/mutation-options.mdx` | Write/mutation parameters (onSuccess, onError) | All mutation hooks |
| `snippets/mutation-result.mdx` | Write/mutation return fields (mutate, mutateAsync) | All mutation hooks |

### Conditional rendering in shared files

MDX is React, so omitting an option is a plain expression — no directive needed:

```mdx
{!props.hide?.includes('gcTime') && (
  <>
    #### gcTime

    `number | Infinity | undefined`

    Time in milliseconds that unused data remains in memory.
  </>
)}
```

Called as `<QueryOptions hide={['gcTime']} />`.

Prefer separate snippets over deeply conditional ones. Once a fragment has three or more `hide`
branches, split it.

## HTTP APIs: OpenAPI

For SDKs that wrap an HTTP API, don't hand-write endpoint reference pages. Vocs generates an
interactive reference — its own sidebar, parameter and response tables, request samples, and an
in-browser playground — from a spec.

```ts
// vocs.config.ts
export default defineConfig({
  openapi: [{ spec: './openapi.yaml', path: '/api' }],
})
```

`spec` may be a project-relative file path, a URL, or an inline object. Each tag becomes a page;
each operation becomes an anchored section on that page, with the sidebar generated automatically.

| Need | Option |
|---|---|
| Add authored guide pages into the section | `sidebar: { top: [{ text: 'Authentication', link: '/api/auth' }] }` |
| Group tags under section headers | `x-tagGroups` at the spec root (Redoc convention) |
| Keep one API's tags top-level | `sidebar: { flatten: ['Data API'] }` |
| Hide internal tags entirely | `exclude: ['Platform API']` |

Embed pieces of the reference inside authored pages:

```mdx
import { OpenApi } from 'vocs'

<OpenApi.Endpoints path="/api" />              {/* accordion of all operations */}
<OpenApi.Operation operationId="createSession" />  {/* one full endpoint block */}
<OpenApi.Playground operationId="getBlocks" />     {/* just the request/response sample */}
```

`Operation` and `Playground` also accept `method` + `path` instead of `operationId`, plus
`anchors={false}` and `hideQueryParams`.

**The division of labor for an SDK:** the OpenAPI section documents the wire protocol; your
hand-written pages document the SDK functions that wrap it. Link between them — an endpoint page
should point at the SDK function, and the SDK function's `## Underlying API` should point at the
endpoint. Don't duplicate parameter documentation across both.

`Handler.openApi` from `vocs/server` mounts a standalone reference on any Hono or fetch-based
server, when the reference needs to live next to the API rather than in the docs site.

## Plugin / Adapter References

Factory functions (plugins, adapters, middleware, connectors) use a simpler template:

```
# pluginName [One-line summary]

## Import
## Usage
## Parameters
```

No Return Type or Underlying API sections — these are configuration factories, not runtime APIs.

Use the shared-snippet + wrapper pattern: write plugin docs once in `snippets/plugins/`, import via
thin wrapper pages that pass framework-specific props.

## Before Shipping a Reference Page

- [ ] `# name [subtext]` present — the subtext is this page's `llms.txt` description
- [ ] Sections in template order, no extras
- [ ] Every parameter has a type line, a terse description, and a focused code example
- [ ] `---` separates core from optional parameters
- [ ] Optionality expressed in types, never in prose or badges
- [ ] Cross-links use absolute route paths
- [ ] Page added to the `vocs.config.ts` sidebar
- [ ] `vocs build` passes — twoslash blocks compile and links resolve
