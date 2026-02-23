# Super-Ralph Customization Guide

## SuperRalph Props Reference

All props are passed to `<SuperRalph>` in `components/workflow.tsx`.

### Required Props

| Prop | Type | Description |
|------|------|-------------|
| `ctx` | `SmithersCtx` | Runtime context (from `smithers()` wrapper) |
| `outputs` | `RalphOutputs` | Schema references (from `createSmithers`) |
| `focuses` | `Array<{id, name}>` | Domain focus areas for discovery/review |
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

### Optional Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `taskRetries` | `number` | `3` | Per-task retry budget |
| `progressFile` | `string` | `"PROGRESS.md"` | Progress summary file |
| `findingsFile` | `string` | `"docs/test-suite-findings.md"` | Integration test findings |
| `skipPhases` | `Set<string>` | `new Set()` | Phases to skip on iteration 0 |
| `focusTestSuites` | `Record<FocusId, {...}>` | — | Per-focus test suite hints |
| `focusDirs` | `Record<FocusId, string[]>` | — | Per-focus directory hints for reviewers |
| `preLandChecks` | `string[]` | — | Fast checks run in worktree before landing |
| `postLandChecks` | `string[]` | — | Slow checks run after merge queue rebase |
| `maxSpeculativeDepth` | `number` | `3` | Merge queue speculation depth |

## Agent Configuration

### Agent Types

```ts
import { ClaudeCodeAgent, CodexAgent, GeminiAgent, KimiAgent } from "smithers-orchestrator";
```

| Agent | CLI | Key Options |
|-------|-----|-------------|
| `ClaudeCodeAgent` | `claude` | `model`, `systemPrompt`, `cwd`, `dangerouslySkipPermissions`, `timeoutMs` |
| `CodexAgent` | `codex` | `model`, `systemPrompt`, `cwd`, `yolo`, `config: { model_reasoning_effort }`, `timeoutMs` |
| `GeminiAgent` | `gemini` | `model`, `systemPrompt`, `cwd`, `yolo`, `timeoutMs` |
| `KimiAgent` | `kimi` | `model`, `systemPrompt`, `cwd`, `yolo`, `thinking`, `timeoutMs` |

### Fallback Chains

Pass agent arrays for rate-limit resilience. Attempt 1 uses `agents[0]`, attempt 2+ uses the next:

```ts
agents: {
  planning: [
    new GeminiAgent({ model: "gemini-2.5-pro", ... }),
    new ClaudeCodeAgent({ model: "claude-opus-4-6", ... }),
  ],
}
```

### Role Mapping

| Role | Steps Using It |
|------|---------------|
| `planning` | Research, Plan, Discover |
| `implementation` | Implement, ReviewFix |
| `testing` | Test, BuildVerify, IntegrationTest |
| `reviewing` | SpecReview, CodeReview, CategoryReview |
| `reporting` | Report, UpdateProgress |
| `mergeQueue` | Land (optional, has built-in default) |

## Pipeline Per Ticket

Each ticket goes through this pipeline (inside a jj worktree):

```
Research → Plan → [Implement → Test → BuildVerify → (SpecReview ∥ CodeReview) → ReviewFix?] → Report → MergeQueue
                  └──────────────────── ValidationLoop (reruns if review finds issues) ──────┘
```

## Focus Areas Design

Good focuses have clear boundaries and match your project's architecture:

```ts
// Good: maps to distinct code areas, agent knows where to look
{ id: "auth", name: "Authentication (JWT, OAuth, session management)" },
{ id: "api",  name: "REST API routes and middleware" },

// Bad: too broad, agents generate unfocused tickets
{ id: "code", name: "All code" },
```

Remove focuses when they reach production quality — saves agent cycles.

## Phase Skipping

Skip phases on the first iteration via env var:

```bash
SKIPTO_PHASE=TICKETS bun run index.ts    # Skip progress/codebase-review/discover
SKIPTO_PHASE=DISCOVER bun run index.ts   # Skip only progress and codebase-review
```

## focusTestSuites and focusDirs

Optional per-focus hints that help agents know what to test/review:

```ts
export const focusTestSuites: Record<FocusId, { suites: string[]; setupHints: string; testDirs: string[] }> = {
  auth: {
    suites: ["pnpm test -- --grep auth"],
    setupHints: "Requires TEST_JWT_SECRET env var",
    testDirs: ["test/auth/"],
  },
};

export const focusDirs: Record<FocusId, string[]> = {
  auth: ["src/auth/", "src/middleware/auth.ts"],
};
```

## Custom Step Overrides

Override any pipeline step with a custom component via props:

```tsx
<SuperRalph
  {...baseProps}
  codeReview={
    <SuperRalph.CodeReview
      agent={primaryAgent}
      additionalAgents={[
        { agent: secondAgent, outputKey: "code_review_second" },
      ]}
      reviewChecklist={checklist}
    />
  }
/>
```

Available override props: `updateProgress`, `discover`, `integrationTest`, `categoryReview`,
`research`, `plan`, `implement`, `test`, `buildVerify`, `specReview`, `codeReview`,
`reviewFix`, `report`, `land`.
