# API Reference Documentation

Rules for writing API reference pages for hooks, functions, classes, and configuration objects.

## Page Template

Every API reference page follows a rigid section order. Predictability is the goal — readers learn the template once and navigate all pages by muscle memory.

### Query/Read API (hook or function that fetches data)

```
# hookName

One-sentence description.

## Import
[import statement]

## Usage
[code group: main file + config + optional ABI]

## Parameters
[type import]
### paramA
[type, description, code example]
### paramB
[type, description, code example]
---
### optionalParamC
[type, description, code example]

[shared query/read options include]

## Return Type
[type import]
[shared query result fields include]

[shared type imports include]

## Action / Underlying API
[link to lower-level API]
```

### Mutation/Write API (hook or function that changes state)

Same as query but with:
- Mutation-specific shared options (onSuccess, onError, onSettled)
- Mutation-specific return fields (mutate, mutateAsync, isIdle)
- Optional `## Type Inference` section for ABI/schema inference

### Configuration Object

```
# createConfig

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

```markdown
### address

`Address | undefined`

Address to get balance for. [`enabled`](#enabled) set to `false` if `address` is `undefined`.

::: code-group
```tsx [index.tsx]
import { useBalance } from 'sdk'

function App() {
  const result = useBalance({
    address: '0x4557B18E779944BFE9d78A672452331C186a9f48', // [!code focus]
  })
}
```
<<< @/snippets/config.ts[config.ts]
:::
```

### Rules

1. **Type on its own line** in backticks. No "Type:" prefix, no table column.
2. **Description is a terse fragment**, not a full sentence: "The contract's ABI." not "This parameter accepts the ABI of the contract."
3. **Every parameter gets a complete code example** with `// [!code focus]` highlighting the relevant line.
4. **Optional vs required** is communicated through the type itself: `| undefined` means optional. No badges.
5. **Horizontal rules (`---`) separate parameter groups**: core params above, optional/advanced below.
6. **Parameters section starts with type import**: `import { type UseBalanceParameters } from 'sdk'`
7. **Cross-link inferred params**: "Inferred from [`abi`](#abi) and [`functionName`](#functionname)."

## Return Type Documentation

### For hooks wrapping async state managers (TanStack Query, SWR, etc.)

Use shared includes for standard return fields (data, error, status, isLoading, refetch, etc.). Only document the data shape specific to this hook:

```markdown
## Return Type

```ts
import { type UseBalanceReturnType } from 'sdk'
```

### data
`{ decimals: number; symbol: string; value: bigint; }`
The balance data.

[shared result fields via include]
```

### For core functions

Document return fields individually:

```markdown
### accounts
`readonly [Address, ...Address[]]`
Connected accounts from connector.

### chainId
`number`
Connected chain ID from connector.
```

### For mutation hooks

Document `mutate` and `mutateAsync` with their parameter types, then standard mutation fields via shared include.

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
Use `twoslash` annotated code blocks for interactive hover information:
```ts twoslash
const result = useReadContract({
  abi: [...],
  functionName: 'balanceOf',
  //             ^? shows autocomplete options
})
result.data
//     ^? shows inferred return type
```

### Dedicated Type Inference section
For APIs with ABI/schema inference, add:
```markdown
## Type Inference
With [`abi`](#abi) configured, TypeScript infers correct types for
[`functionName`](#functionname), [`args`](#args), and the return type.
See the [TypeScript docs](/react/typescript) for more information.
```

### Complex nested types
Show inline as type literals. Do not create separate type pages for one-off shapes:
```
`{ decimals: number; symbol: string; value: bigint; }`
```

## Cross-Referencing

Every API reference page should cross-reference related APIs:

| Section | Links to | Example |
|---------|----------|---------|
| `## Action` | Underlying core function | `[getBalance](/core/api/actions/getBalance)` |
| `## Viem` / `## Underlying API` | External library function | `[readContract](https://viem.sh/docs/contract/readContract)` |
| Parameter descriptions | Other params on same page | `Inferred from [abi](#abi)` |
| Parameter descriptions | Config/Provider pages | `[Config](/react/api/createConfig#config)` |
| Type Inference section | TypeScript guide | `[TypeScript docs](/react/typescript)` |
| Deprecation badges | Migration guide | `<Badge type="warning">[deprecated](/react/guides/migrate-v2#change)</Badge>` |

## Error Documentation

### Per-function error types
Core function pages include an `## Error` section with the error type import:
```markdown
## Error
```ts
import { type ConnectErrorType } from '@sdk/core'
```
```

### Hook error handling
Hooks delegate errors to the async state manager. The shared result include documents the `error` field typed to the specific `ErrorType`.

### Centralized errors page
List all error classes by category with name, one-line description, and import statement. No elaborate explanation needed.

## Shared Content System

### Template variables for type interpolation

Each page defines variables that shared includes consume:

```html
<script setup>
const packageName = 'sdk'
const actionName = 'getBalance'
const typeName = 'GetBalance'
const TData = '{ decimals: number; symbol: string; value: bigint; }'
const TError = 'GetBalanceErrorType'
</script>
```

Shared files use `{{typeName}}`, `{{TData}}`, etc. to render correct types per page.

### Key shared files to maintain

| File | Content | Used by |
|------|---------|---------|
| `query-options.md` | Read/query parameters (enabled, gcTime, staleTime) | All query hooks |
| `query-result.md` | Read/query return fields (data, error, status) | All query hooks |
| `mutation-options.md` | Write/mutation parameters (onSuccess, onError) | All mutation hooks |
| `mutation-result.md` | Write/mutation return fields (mutate, mutateAsync) | All mutation hooks |

### Conditional rendering in shared files

Use conditional directives to show/hide options based on the including page:
```html
<div v-if="!hideOptions?.includes('gcTime')">
#### gcTime
...
</div>
```

## Connector / Plugin References

Factory functions (connectors, plugins, middleware) use a simpler template:

```
# connectorName
[description]

## Import
## Usage
## Parameters
```

No Return Type or Action sections — these are configuration factories, not runtime APIs.

Use the shared include + wrapper pattern: write connector docs once in `shared/connectors/`, include via thin wrapper pages that set framework-specific variables.
