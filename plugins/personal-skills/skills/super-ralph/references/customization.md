# Super-Ralph Customization Reference

## SuperRalph Props

### Required

| Prop | Type | Description |
|------|------|-------------|
| `ctx` | `SmithersCtx` | Runtime context from `smithers()` wrapper |
| `outputs` | `RalphOutputs` | Schema references from `createSmithers` |
| `focuses` | `Array<{id, name}>` | Focus areas — must be non-overlapping, bounded scopes |
| `projectId` | `string` | Kebab-case identifier |
| `projectName` | `string` | Human-readable name |
| `specsPath` | `string` | Path to spec docs (relative to repo root) |
| `referenceFiles` | `string[]` | Reference doc/directory paths |
| `buildCmds` | `Record<string, string>` | Named build commands that must pass |
| `testCmds` | `Record<string, string>` | Named test commands that must pass |
| `codeStyle` | `string` | Code style description for reviewers |
| `reviewChecklist` | `string[]` | Review checklist items |
| `maxConcurrency` | `number` | Max parallel agent tasks |
| `agents` | `AgentConfig` | Per-role agent configuration |

### Optional (but `focusDirs` and `focusTestSuites` are effectively mandatory)

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `focusDirs` | `Record<FocusId, string[]>` | — | **Use always.** Restricts each codebase-review agent to specific directories. Without this, all reviewers scan the full repo and generate duplicate tickets. |
| `focusTestSuites` | `Record<FocusId, { suites: string[]; setupHints: string[]; testDirs: string[] }>` | — | **Use always.** `setupHints` is a `string[]` — each entry tells the reviewer what's already done in that area. Critical for preventing re-ticketing of completed work. |
| `taskRetries` | `number` | `3` | Per-task retry budget |
| `skipPhases` | `Set<string>` | `new Set()` | Phases to skip on iteration 0 |
| `commitConfig` | `{ prefix?: string; mainBranch?: string; emojiPrefixes?: string }` | `{ prefix: "📝", mainBranch: "main", emojiPrefixes: "✨ feat, 🐛 fix, ♻️ refactor, 📝 docs, 🧪 test" }` | Commit message configuration |
| `testSuites` | `Array<{ name: string; command: string; description: string }>` | `[]` | Named test suites for the test step. If empty, `testCmds` is used. |
| `preLandChecks` | `string[]` | `[]` | Fast checks run in worktree before entering merge queue (unit tests, typecheck) |
| `postLandChecks` | `string[]` | `[]` | Slow checks run after rebase in merge queue (E2E, integration). If set, overrides `testCmds` for CI. |
| `mergeQueueOrdering` | `"report-complete-fifo" \| "priority" \| "ticket-order"` | `"report-complete-fifo"` | Queue ordering: fifo by report completion, by ticket priority, or by discovery order |
| `mergeQueueId` | `string` | `"land-queue"` | Merge queue coordinator ID — isolates state between concurrent queues |
| `maxSpeculativeDepth` | `number` | `3` | Max speculative queue entries rebased+tested in parallel |

---

## Focus Design Rules

### Non-overlapping, directory-bounded scopes

Every focus must:
1. Map to a distinct, non-overlapping set of directories (enforced via `focusDirs`)
2. Have `setupHints` that explicitly state what's already done in that area
3. Be removed once the area reaches production quality

```ts
// focuses.ts
export const focuses = [
  // Each focus = one bounded subsystem
  { id: "build-tooling",  name: "Build system: tsup, .gitignore, dist, source maps" },
  { id: "auth-crypto",    name: "Credential encryption: AES-GCM + PBKDF2 at rest" },
  { id: "query-patterns", name: "TanStack Query: Suspense variants, handle-in-key" },
  { id: "worker",         name: "Web Worker: typed protocol, timeouts, crash recovery" },
  { id: "test-app",       name: "Reference app: Vite scaffold, components, Playwright E2E" },
] as const;

// focusDirs.ts — MANDATORY, one entry per focus
export const focusDirs = {
  "build-tooling":  ["package.json", "tsup.config.ts", ".gitignore", "scripts/"],
  "auth-crypto":    ["src/core/signature-cache.ts", "src/types/"],
  "query-patterns": ["src/erc7984/useConfidentialBalance.ts", "src/erc7984/", "src/hooks/"],
  "worker":         ["src/worker/"],
  "test-app":       ["packages/test-app/"],
};

// focusTestSuites.ts — MANDATORY, setupHints are critical
export const focusTestSuites = {
  "build-tooling": {
    suites: ["bun run build"],
    setupHints: [
      "ALREADY DONE: .gitignore updated, dist removed from git",
      "GAP: tsup migration not done — tsc still used, no code splitting, no source maps",
    ],
    testDirs: ["scripts/"],
  },
  "auth-crypto": {
    suites: ["bun run test test/unit/phase2/signature-cache.test.ts"],
    setupHints: [
      "ALREADY DONE: buildCacheKey SHA-256 hash (SEC-002), AES-GCM encrypt/decrypt (SEC-001)",
      "GAP: CREDENTIAL_ENCRYPTION_FAILED / CREDENTIAL_DECRYPTION_FAILED error codes missing",
    ],
    testDirs: ["test/unit/phase2/"],
  },
};
```

### Anti-patterns that cause ticket explosion

| Anti-pattern | Effect | Fix |
|---|---|---|
| Focus named `"architecture"` with no dirs | Reads everything, duplicates all other focuses | Split into bounded subsystems or delete |
| No `focusDirs` entry for a focus | Reviewer scans full repo, finds everything | Add dirs immediately |
| No `setupHints` in `focusTestSuites` | Reviewer re-tickets completed work | List what's done explicitly |
| Review and discover use **different IDs** for same work | Dedup misses — both get full pipelines | Scope reviewers so they can't generate tickets for what discover already owns; or coordinate ticket IDs |
| Keeping completed focuses active | Wastes agent cycles re-reviewing done code | Remove and comment out when area is production-ready |

> **Dedup only works on ID match.** `selectAllTickets` deduplicates review+discover tickets by ID
> (review wins). If `codebase-review:architecture` emits `RZMA-011` and `discover` emits
> `handle-in-key-balance-refactor` for the same work, dedup doesn't fire and both pipelines run.

---

## Agent Configuration

### Agent Types

```ts
import { ClaudeCodeAgent, CodexAgent, GeminiAgent, KimiAgent } from "smithers-orchestrator";
```

| Agent | Key Options |
|-------|-------------|
| `ClaudeCodeAgent` | `model`, `systemPrompt`, `cwd`, `dangerouslySkipPermissions`, `timeoutMs` |
| `CodexAgent` | `model`, `systemPrompt`, `cwd`, `yolo`, `config: { model_reasoning_effort }`, `timeoutMs` |
| `GeminiAgent` | `model`, `systemPrompt`, `cwd`, `yolo`, `timeoutMs` |
| `KimiAgent` | `model`, `systemPrompt`, `cwd`, `yolo`, `thinking`, `timeoutMs` |

### Agent Arrays — Round-Robin + Fallback

Pass arrays for two benefits:
- **Round-robin across tickets**: ticket N uses `agents[N % len]` as primary (load balancing)
- **Ordered fallback on retry**: if attempt 1 fails, attempt 2 uses the next agent in the rotated list

```ts
agents: {
  planning: [
    new GeminiAgent({ model: "gemini-2.5-pro", systemPrompt: PLANNING_PROMPT, ... }),
    new ClaudeCodeAgent({ model: "claude-opus-4-6", systemPrompt: PLANNING_PROMPT, ... }),
    new CodexAgent({ model: "gpt-5.3-codex", systemPrompt: PLANNING_PROMPT, ... }),
  ],
}
// Ticket 0: primary=Gemini, fallbacks=[Claude, Codex]
// Ticket 1: primary=Claude, fallbacks=[Codex, Gemini]
// Ticket 2: primary=Codex,  fallbacks=[Gemini, Claude]
```

### Role Mapping

| Role | Pipeline Steps |
|------|---------------|
| `planning` | Research, Plan, Discover |
| `implementation` | Implement, ReviewFix |
| `testing` | Test, BuildVerify, IntegrationTest |
| `reviewing` | SpecReview, CodeReview, CategoryReview |
| `reporting` | Report, UpdateProgress |
| `mergeQueue` | Land (optional, has built-in default) |

---

## Pipeline Per Ticket

```
Research → Plan → Implement → Test → BuildVerify → (SpecReview ∥ CodeReview) → ReviewFix? → Report → Land
```

`ReviewFix` is **conditional** — it only runs when SpecReview or CodeReview returns a non-`"none"` severity.
There is no loop back to Implement. If ReviewFix is insufficient, the report still completes and the ticket
lands. The outer `<Ralph>` loop reruns the whole workflow on the next iteration for evicted tickets.

Each step is a separate agent invocation. 10 steps × N tickets = total node count.
Keep ticket count proportional: 5-10 focuses × 5-8 tickets each = 25-80 tickets = 250-800 nodes.

---

## Planning Prompt Pattern

Always structure planning prompts with an explicit "already done" section:

```ts
const PLANNING_PROMPT = `You are implementing <project> improvements based on <spec>.

## Mandatory reading before planning any ticket
1. Read <spec-path> — full specification
2. Read relevant source files in <src-path>

## ALREADY IMPLEMENTED — do not re-ticket these
- <Feature A>: fully done, all tests passing
- <Feature B>: implemented at <file>, exported from <index>

## Gaps to address (these need tickets)
- <Gap 1>: <what's missing and where>
- <Gap 2>: <what's missing and where>

## Constraints
- <Hard constraint 1>
- <Hard constraint 2>
`;
```

---

## Phase Skipping

```bash
# Skip progress/codebase-review/discover (use when codebase already reviewed)
SKIPTO_PHASE=TICKETS bun run index.ts

# Skip only progress and codebase-review
SKIPTO_PHASE=DISCOVER bun run index.ts
```

Phase skip order (for `SKIPTO_PHASE`): `PROGRESS` → `CODEBASE_REVIEW` → `DISCOVER` → `TICKETS` → `INTEGRATION_TEST`

**All phases run in parallel** — they are all inside a single `<Parallel>` on each iteration.
`SKIPTO_PHASE` skips phases whose index comes before the target, not runs them sequentially.

---

## Custom Step Overrides

Any pipeline step can be replaced by passing a `ReactElement` prop. The built-in
`SuperRalph.*` compound components are **passthrough stubs** — they render nothing on their
own. They exist as JSX markers so you can pass custom elements with recognizable names:

```tsx
// The prop takes any ReactElement — build your own or use a library component
<SuperRalph
  {...baseProps}
  codeReview={<MyMultiReviewerCodeReview agents={[codex, gemini, claude]} checklist={checklist} />}
  land={<MyCustomLandStep mergeStrategy="squash" />}
/>
```

Override-able props (all accept `ReactElement | undefined`):
`updateProgress`, `discover`, `integrationTest`, `categoryReview`,
`research`, `plan`, `implement`, `test`, `buildVerify`, `specReview`, `codeReview`,
`reviewFix`, `report`, `land`.
