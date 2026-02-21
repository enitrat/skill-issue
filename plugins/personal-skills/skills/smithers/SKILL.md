---
name: smithers
description: >
  Build multi-phase AI development pipelines with the Smithers workflow engine (v0.8.0). Use when:
  (1) Initializing a new Smithers project in a target directory (use the init CLI)
  (2) Adding phases or steps to existing workflows
  (3) Implementing review loops, pass tracking, or phase gating
  (4) Debugging workflow orchestration issues (Ralph loops, ctx.output, data threading)
  (5) Writing instruction MDX files for project configs
  (6) Configuring agents or per-role overrides
---

# Smithers Workflow Engine

TypeScript framework for deterministic, resumable AI workflows using JSX.
Runtime: Bun >= 1.3. State: SQLite via Drizzle ORM. Validation: Zod schemas. Version: 0.8.0.

## Init CLI

```bash
uv run /path/to/skills/smithers/scripts/skill_smithers.py <target-dir>
uv run scripts/skill_smithers.py ./scripts/my-workflow --name my-workflow --no-install
```

Copies the full template into `<target-dir>`, runs `bun install`, and initializes git + jj (skips each if already present). Requires `jj` on PATH: `brew install jj`.

## Project Config Setup

The workflow engine (`<target-dir>/`) is project-agnostic — never edit it per project. All domain-specific content lives in a separate config directory:

```
projects/<my-project>/smithers-config/
  config.ts            # ProjectConfig (name, phases, cwd, instructions, agents)
  instructions/        # MDX files injected into component prompts
    research.mdx, plan.mdx, implement.mdx, test.mdx,
    code-review.mdx, prd-review.mdx, review-fix.mdx,
    final-review.mdx, update-progress.mdx
  output/
    context/           # agents write context docs here (create empty)
    plans/             # agents write plan docs here (create empty)
  run.sh               # launcher
```

**`config.ts`** must satisfy the `ProjectConfig` interface (see `<target-dir>/types/project.ts`). Key fields:

- `phases` — ordered list of `{ id, name, description, metadata? }` — the outer loop iterates over these
- `cwd` — absolute path to the repo root where agents run
- `instructions` — map of step name → imported MDX function (e.g. `research: ResearchInstructions`)
- `agents.systemPromptContent` — project context injected into every agent's system prompt

**`instructions/*.mdx`** are additive — they fill the `{props.projectInstructions}` slot in each generic component prompt. Write only what's domain-specific (spec references, file paths, rules). Phase `metadata` fields are available as `{props.fieldName}`.

**`run.sh`** sets `SMITHERS_PROJECT` and invokes the engine:

```bash
#!/usr/bin/env bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "<target-dir>"
export SMITHERS_PROJECT="$SCRIPT_DIR/config.js"
bunx smithers run workflow.tsx
```

Run with: `./projects/<my-project>/smithers-config/run.sh`

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
| `<Worktree>` | Run tasks in an isolated git/jj worktree (auto-created if missing) |

## Task Props

| Prop            | Type                        | Purpose                                                             |
|----------------|------------------------------|---------------------------------------------------------------------|
| `id`           | `string`                    | Unique node ID (phase-prefix for multi-phase loops)                 |
| `output`       | `ZodObject`                 | **Required.** Pass `outputs.xxx` from `createSmithers`. Enables schema validation, auto-retry, and JSON instructions. Never pass a string — that API was removed in v0.7.1. |
| `agent`        | `AgentLike \| AgentLike[]`  | Agent or array of agents `[primary, fallback1, fallback2, ...]`. Tries in order: attempt 1 uses `agents[0]`, attempt 2 uses `agents[1]`, etc. (capped at last). Replaces the old `fallbackAgent` prop. |
| `retries`      | `number`                    | Retry budget on failure                                             |
| `timeoutMs`    | `number`                    | Per-attempt timeout in milliseconds                                 |
| `skipIf`       | `boolean`                   | Skip execution when true                                            |
| `continueOnFail`| `boolean`                  | Don't block siblings when this task fails                           |

## Available Agents

| Agent             | Import                        | CLI Required  | Notes                                      |
|------------------|-------------------------------|---------------|--------------------------------------------|
| `ClaudeCodeAgent` | `smithers-orchestrator`       | `claude`      | Default reviewer/researcher                |
| `CodexAgent`      | `smithers-orchestrator`       | `codex`       | Default implementer                        |
| `GeminiAgent`     | `smithers-orchestrator`       | `gemini`      | Google Gemini CLI                          |
| `KimiAgent`       | `smithers-orchestrator`       | `kimi`        | Kimi CLI; **thinking=true and stream-json by default** (v0.8.0); supports `agent: "okabe"`, MCP configs |
| `AmpAgent`        | `smithers-orchestrator`       | `amp`         | Amp CLI; supports `thread` (continue existing thread), `visibility`, `mcpConfig`, `dangerouslyAllowAll` |
| `PiAgent`         | `smithers-orchestrator`       | `pi`          | Pi CLI                                     |

## Key Rules

1. **Always pass `output={outputs.xxx}`** to `<Task>` — enables schema validation, auto-retry, and auto-appended JSON output instructions. Pass the ZodObject from `createSmithers`'s `outputs` return — string keys were removed in v0.7.1.
2. **Use `ctx.outputMaybe()`** not `ctx.output()` — gracefully handles missing outputs during first render
3. **Use `ctx.latest()` for cross-iteration decisions** — `outputMaybe` is scoped to the current Ralph iteration; use `ctx.latest(table, nodeId)` for `skipIf`, loop `until`, and `allPhasesComplete` checks
4. **Use `.nullable()` never `.optional()` in Zod schemas** — OpenAI structured outputs rejects `.optional()` fields
5. **Phase-prefix nodeIds** when multiple phases share a loop — `${phaseId}:step-name`
6. **Set `continueOnFail` on review Tasks** — one reviewer failing shouldn't block the other
7. **Use agent arrays for rate-limit resilience** — set `agent={[primary, fallback]}` on heavy tasks so retry attempts switch to a different model automatically. The old `fallbackAgent` prop was **removed in v0.8.0**.

## Workflow Philosophy

**Atomic unit pipeline**: run the full pipeline (implement → test → review → fix → final-review) for each logically complete unit of work. Do NOT implement everything then review once.

**"Atomic" = one logical concern, not smallest diff**: 20 similar operators = ONE unit. Porting 14 similar test cases = ONE unit. The outer Ralph loop iterates until all phases pass the FinalReview gate.

## Resources

- [references/atomic-workflow.md](references/atomic-workflow.md) — logical unit pipeline, nextLogicalUnit chaining, batching heuristics
- [references/patterns.md](references/patterns.md) — outer Ralph, gating, data threading, pass tracking, dual-model review
- [references/troubleshooting.md](references/troubleshooting.md) — dirty git, OpenAI schema errors, stale runs, SQLite debugging
