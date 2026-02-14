---
name: smithers
description: >
  Build multi-phase AI development pipelines with the Smithers workflow engine. Use when:
  (1) Creating new Smithers workflows (workflow.tsx, components, schemas, agents)
  (2) Adding phases or steps to existing workflows
  (3) Implementing review loops, pass tracking, or phase gating
  (4) Debugging workflow orchestration issues (Ralph loops, ctx.output, data threading)
  (5) Writing MDX prompts with structured output schemas
  (6) Configuring CLI agents (ClaudeCodeAgent, CodexAgent)
---

# Smithers Workflow Engine

TypeScript framework for deterministic, resumable AI workflows using JSX.
Runtime: Bun >= 1.3. State: SQLite via Drizzle ORM. Validation: Zod schemas.

## Workflow Philosophy: Atomic Unit Pipeline

**Preferred pattern**: Run the full pipeline (implement → test → review → fix → refactor → final-review) for each **small atomic unit of work**. Do NOT implement everything then review once.

The outer Ralph loop drives this: each iteration implements 1-2 atomic units, validates them through the full quality pipeline, then the final-review gate either approves (phase done) or rejects (loop for more units). The `nextSmallestUnit` field in the implement schema chains work across iterations.

See [references/atomic-workflow.md](references/atomic-workflow.md) for the full pattern with examples.

## Core Execution Model

Render-schedule-execute loop:
1. **Render** — JSX tree → available tasks
2. **Schedule** — determine runnable tasks (dependencies + concurrency)
3. **Execute** — agent runs, output validates against Zod, persists to SQLite
4. **Re-render** — tree updates with new outputs, unblocking dependents
5. **Repeat** until done/failed

## JSX Primitives

| Component    | Purpose                                        |
|-------------|------------------------------------------------|
| `<Workflow>` | Root container                                 |
| `<Task>`     | Single agent work unit with schema validation  |
| `<Sequence>` | Sequential execution                           |
| `<Parallel>` | Concurrent execution with `maxConcurrency`     |
| `<Ralph>`    | Loop with `until` condition + `maxIterations`  |
| `<Branch>`   | Conditional routing                            |

## Project Structure (3-File Pattern)

```
scripts/my-workflow/
├── workflow.tsx              # thin composition root
├── smithers.ts              # createSmithers() schema registry
├── agents.ts                # CLI agent configs
├── config.ts                # constants, phase definitions
├── system-prompt.ts         # prompt assembly
├── run.sh                   # execution wrapper
├── components/
│   ├── StepName.tsx         # orchestration (Task wrapper)
│   ├── StepName.schema.ts   # Zod schema → auto SQLite table
│   └── StepName.mdx         # prompt template
└── prompts/                 # reusable context docs
```

Each step = 3 files (`.tsx` + `.schema.ts` + `.mdx`). Keep them in sync.

## Quick Start Pattern

```tsx
// smithers.ts — schema registry
export const { smithers, tables } = createSmithers({
  implement: ImplementSchema,
  review: ReviewSchema,
});

// workflow.tsx — composition root
export default smithers((ctx) => {
  const latestReview = ctx.outputMaybe("review", { nodeId: "review" });
  const done = latestReview?.approved ?? false;

  return (
    <Workflow name="my-workflow">
      <Ralph until={done} maxIterations={3} onMaxReached="return-last">
        <Sequence>
          <Implement nodeId="implement" outputSchema={ImplementSchema} />
          <Review nodeId="review" outputSchema={ReviewSchema} />
        </Sequence>
      </Ralph>
    </Workflow>
  );
});
```

## Production Patterns

See [references/atomic-workflow.md](references/atomic-workflow.md) for the **recommended atomic unit pipeline** pattern:
- **nextSmallestUnit Chaining** — each implement outputs what to do next, creating a directed chain across Ralph iterations
- **Full Pipeline Per Unit** — implement → test → review → fix → refactor → final-review for each 1-2 atomic units
- **Strict Final-Review Gate** — reject unless ALL criteria met, forcing more iterations until complete

See [references/patterns.md](references/patterns.md) for additional battle-tested patterns:
- **Outer Ralph Loop** — wrap multiple phases in one loop with per-phase gating
- **readyToMoveOn Gating** — FinalReview decides per-phase completion
- **Phase-Prefixed nodeIds** — avoid collisions in shared loops
- **Data Threading** — precise prop passing between steps
- **Pass Tracking** — record which pass completed which phases
- **Dual-Model Review** — parallel Claude + Codex reviews
- **ReviewFix Skip** — skip when both reviewers approved
- **SKIP_PHASES** — env-driven phase skipping

## Prerequisites

Before creating or running a Smithers workflow, verify **Jujutsu (jj)** is installed and initialized.
Smithers uses jj to snapshot filesystem state before each task, enabling `smithers revert` to roll back
individual task attempts. Without jj, `revert` silently fails (no `jj_pointer` recorded).

```bash
# Check if jj is installed
which jj || echo "jj not found — install via: brew install jj"

# Check if repo has jj initialized (colocated with git)
jj log --limit 1 2>/dev/null || echo "jj not initialized — run: jj git init --colocate"
```

If jj is not set up, ask the user to install and initialize it:
1. `brew install jj` (or `cargo install jj-cli`)
2. `jj git init --colocate` in the project root (coexists with `.git`)
3. `jj bookmark track <branch> --remote=origin` to track the main branch

## Key Rules

1. **Always pass `outputSchema`** to `<Task>` — enables auto-validation, retry, and `{props.schema}` injection
2. **End every MDX prompt** with `## REQUIRED OUTPUT\n{props.schema}` — agents need explicit format instructions
3. **System prompt must include** JSON output requirement — CLI agents default to natural language
4. **Use `ctx.outputMaybe()`** not `ctx.output()` — gracefully handles missing outputs during first render
4b. **Use `ctx.latest()` for cross-iteration decisions** — `outputMaybe` is scoped to the current Ralph iteration; use `ctx.latest(table, nodeId)` for `skipIf`, loop `until`, and `allPhasesComplete` checks (see [troubleshooting #14](references/troubleshooting.md))
5. **Thread data precisely** — pass only the fields each step needs, not entire output objects
6. **Phase-prefix nodeIds** when multiple phases share a loop — `${phaseId}:step-name`
7. **Use `skipIf` on `<Sequence>` and `<Task>`** for conditional execution
8. **Set `continueOnFail` on review Tasks** — one reviewer failing shouldn't block the other
9. **Use `.nullable()` NEVER `.optional()` in Zod schemas** — OpenAI's structured outputs API rejects optional fields (see below)

## CLI Agent Config

```ts
// Claude — for review, context gathering, architectural judgment
new ClaudeCodeAgent({
  model: "claude-opus-4-6",
  systemPrompt,
  cwd: REPO_ROOT,
  permissionMode: "acceptEdits", // or "default" for read-only review
});

// Codex — for implementation, code generation, refactoring
new CodexAgent({
  model: "gpt-5.3-codex",
  fullAuto: true,
  cwd: REPO_ROOT,
  sandbox: "read-only", // for review-only agents
});
```

## Git Commit Rules (Per Step Type)

Every workflow step that modifies files should include git commit instructions in its MDX prompt.
Agents must make **atomic commits** — one logical change per commit, not one giant batch.

**Format**: `EMOJI type(scope): description` where scope = `{props.phase}` or phase ID.

### Research / Context Gathering

```
git add docs/context/{props.phase}.md && git commit -m "♻️ refactor({props.phase}): gather context and reference materials"
```

### Implementation

```mdx
## GIT COMMIT RULES
- Make atomic commits — one logical change per commit
- Commit EACH smallest unit of work separately, do NOT batch everything into one commit
- Use emoji prefixes: 🐛 fix, ♻️ refactor, 🧪 test, ⚡ perf
- Format: "EMOJI type(scope): description"
- Examples:
  - "♻️ refactor({props.phase}): add RocksDB adapter with get/put/delete"
  - "🧪 test({props.phase}): add unit tests for RocksDB adapter"
  - "🐛 fix({props.phase}): handle missing key edge case in get()"
- git add the specific files changed, then git commit with the emoji message
```

### Tests

```mdx
## GIT COMMIT RULES
If any tests fail and you need to fix code to make them pass, commit each fix atomically:
- git add the specific files, then commit
- Format: "🐛 fix(SCOPE): what was fixed"
- Example: "🐛 fix({props.phase}): correct batch write ordering"

If you add new test files, commit them:
- Format: "🧪 test(SCOPE): what was tested"
- Example: "🧪 test({props.phase}): add edge case tests for iterator"
```

### Refactors / ReviewFix

```mdx
## GIT COMMIT RULES
- Make atomic commits — one refactor per commit
- Use emoji prefixes: ♻️ refactor, 🐛 fix, 🧪 test, ⚡ perf
- Format: "EMOJI type(scope): description"
- Examples:
  - "♻️ refactor({props.phase}): extract shared iterator logic into helper"
  - "🐛 fix({props.phase}): correct error propagation in iterator"
  - "🧪 test({props.phase}): add coverage for iterator edge cases"
- git add the specific files changed, then git commit with the emoji message
- Each meaningful refactor gets its own atomic commit
```

## MDX Prompt Template

```mdx
# Step Name — Pass {props.pass}

{props.context ? `## Context\n${props.context}` : ""}

## Instructions

1. Read relevant files BEFORE making changes
2. [Domain-specific instructions]

## REQUIRED OUTPUT

You MUST end your response with a JSON object matching this schema:

{props.schema}
```

## Zod Schema Pattern

```ts
import { z } from "zod";

// Implement schema with nextSmallestUnit for atomic chaining
export const ImplementSchema = z.object({
  filesCreated: z.array(z.string()),
  filesModified: z.array(z.string()),
  commitMessage: z.string(),
  whatWasDone: z.string().describe("What atomic unit was implemented"),
  nextSmallestUnit: z.string().describe("Next smallest atomic unit to implement"),
});

// Generic step schema
export const StepSchema = z.object({
  summary: z.string(),
  line: z.number().nullable(),      // use .nullable() for optional fields
  suggestion: z.string().nullable(), // NEVER use .optional()
});
```

Smithers auto-adds `runId`, `nodeId`, `iteration` columns — don't include them in your schema.

**CRITICAL: `.nullable()` not `.optional()` for non-required fields.**
OpenAI's structured outputs API requires every property to be in the `required` array — it does not support optional properties. When Smithers converts Zod to JSON Schema for CodexAgent, `.optional()` produces a property missing from `required`, which OpenAI rejects with:
```
'required' is required to be supplied and to be an array including every key in properties
```
Use `.nullable()` instead — the agent sends `null` for absent values, and the property stays in `required`.

## Resources

### references/
- [atomic-workflow.md](references/atomic-workflow.md) — **Recommended**: Atomic unit pipeline pattern (nextSmallestUnit chaining, full pipeline per unit, strict gates)
- [patterns.md](references/patterns.md) — Production workflow patterns (outer Ralph, gating, data threading, pass tracking)
- [troubleshooting.md](references/troubleshooting.md) — Common failures and fixes (dirty git, OpenAI schema errors, stale runs, SQLite debugging)
