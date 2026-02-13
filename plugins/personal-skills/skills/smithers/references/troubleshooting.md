# Smithers Troubleshooting

Common issues encountered when building and running Smithers workflows.

---

## 1. Codex Agent Refuses to Work on Dirty Git

**Symptom**: Implement step completes in seconds with empty `filesCreated`/`filesModified`. Summary says something like "Per workspace safety rules, I paused to avoid interfering with unexpected changes."

**Cause**: Codex's built-in model behavior proactively runs `git status` and refuses to work when it sees uncommitted changes. This is NOT configurable via `profile: "yolo"` or any CLI flag — it's baked into the model.

**Fix**: Add a workspace policy to the system prompt:
```
## WORKSPACE POLICY
Uncommitted changes in the worktree are expected and normal.
Do NOT refuse to work because of dirty git state. Proceed with implementation regardless.
Other agents in this workflow may have made changes that are not yet committed.
```

**Prevention**: Commit or stash changes before running the workflow, and include the workspace policy in every system prompt.

---

## 2. OpenAI Rejects `.optional()` in Zod Schemas

**Symptom**: CodexAgent task fails immediately with:
```
Invalid schema for response_format 'codex_output_schema':
'required' is required to be supplied and to be an array including every key in properties. Missing '<field>'.
```

**Cause**: OpenAI's structured outputs API requires ALL properties to be in the JSON Schema `required` array. It does not support optional properties. When Smithers converts a Zod schema with `.optional()` fields to JSON Schema, those fields are omitted from `required`, and OpenAI rejects the schema.

**Fix**: Replace `.optional()` with `.nullable()` in all Zod schemas:
```ts
// WRONG — breaks OpenAI structured outputs
line: z.number().optional(),
suggestion: z.string().optional(),

// CORRECT — agent sends null for absent values
line: z.number().nullable(),
suggestion: z.string().nullable(),
```

**Note**: This only affects schemas sent to CodexAgent (OpenAI). ClaudeCodeAgent (Anthropic) handles `.optional()` fine. But use `.nullable()` everywhere for consistency — a schema may be shared across agents.

---

## 3. `smithers revert` Fails — "Attempt has no jjPointer recorded"

**Symptom**: Running `smithers revert` returns `{ "success": false, "error": "Attempt has no jjPointer recorded" }`.

**Cause**: Smithers uses Jujutsu (jj) to snapshot the filesystem before each task. Without jj installed and initialized, the `jj_pointer` column in SQLite stays empty, and `revert` has nothing to restore from.

**Fix**: Install and initialize jj:
```bash
brew install jj                              # install
jj git init --colocate                       # init colocated with git
jj bookmark track master --remote=origin     # track main branch
```

**Workaround without jj**: Manually clear task outputs from SQLite to force re-execution (see "Manual Task Re-run via SQLite" below).

---

## 4. Stale Runs Blocking New Runs

**Symptom**: Warning on startup:
```
⚠ Found 1 run(s) still marked as 'running':
  <run-id> (started ...)
  Use 'smithers cancel' to mark them as cancelled, or 'smithers resume' to continue.
```

**Cause**: A previous run was killed (Ctrl-C, crash, terminal closed) but never marked as cancelled in SQLite.

**Fix**:
```bash
# Cancel by run ID (requires full UUID)
bunx smithers cancel workflow.tsx --run-id <full-uuid>

# Find run IDs
bunx smithers list workflow.tsx --limit 5
```

---

## 5. React "key" Warning on Mapped Elements

**Symptom**: Runtime warning: `Each child in a list should have a unique "key" prop.`

**Cause**: When using `PHASES.map()` to render `<Sequence>` elements inside a Ralph loop, React needs a `key` prop on each mapped element. But Smithers' `SequenceProps` type doesn't include `key`, so TypeScript rejects it.

**Root cause**: Smithers' `jsxImportSource` re-exports React's runtime functions but not the JSX type namespace that includes `IntrinsicAttributes` (which provides `key`). This is a Smithers bug.

**Workaround**:
```tsx
// @ts-expect-error — Smithers SequenceProps lacks key but React runtime needs it
<Sequence key={id} skipIf={...}>
```

---

## 6. Diagnosing Suspiciously Fast Tasks

**Symptom**: A task (e.g., implement) completes in seconds when it should take minutes.

**Diagnosis**: Query the SQLite database for the task's output:
```bash
# Check what the agent actually produced
sqlite3 smithers.db "SELECT node_id, summary FROM implement WHERE run_id = '<run-id>';"

# Check attempt state
sqlite3 smithers.db "SELECT node_id, state, started_at_ms, finished_at_ms FROM _smithers_attempts WHERE run_id = '<run-id>' ORDER BY started_at_ms;"
```

**Common causes**:
- Agent refused to work (dirty git — see issue #1)
- Schema validation failed and agent returned minimal output
- Agent hit a permissions error and bailed early

---

## 7. Manual Task Re-run via SQLite

When `smithers revert` isn't available (no jj), you can force a task to re-run by clearing its records:

```sql
-- Replace <run-id> and <node-id> with actual values
-- Clear attempt record
DELETE FROM _smithers_attempts WHERE run_id = '<run-id>' AND node_id = '<node-id>';

-- Clear node record
DELETE FROM _smithers_nodes WHERE run_id = '<run-id>' AND node_id = '<node-id>';

-- Clear output data (table name matches schema registry key)
DELETE FROM implement WHERE run_id = '<run-id>' AND node_id = '<node-id>';
```

Then resume the run:
```bash
bunx smithers resume workflow.tsx --run-id <run-id>
```

Smithers will re-render, see the missing output, and re-execute the task.

**Important**: Don't do this on a live/running workflow — cancel it first.

---

## 8. Useful SQLite Inspection Queries

```bash
# List all tables
sqlite3 smithers.db ".tables"

# See all attempts for a run
sqlite3 smithers.db "SELECT node_id, attempt, state FROM _smithers_attempts WHERE run_id = '<run-id>' ORDER BY started_at_ms;"

# See all completed nodes
sqlite3 smithers.db "SELECT node_id FROM _smithers_nodes WHERE run_id = '<run-id>';"

# Check a specific output table
sqlite3 smithers.db "PRAGMA table_info(implement);"
sqlite3 smithers.db "SELECT node_id, summary FROM implement WHERE run_id = '<run-id>';"

# Check pass tracker
sqlite3 smithers.db "SELECT * FROM pass_tracker WHERE run_id = '<run-id>';"
```

---

## 9. System Prompt Not Taking Effect

**Symptom**: Agent ignores system prompt instructions (e.g., workspace policy, JSON output requirement).

**Cause**: System prompt is built at import time in `agents.ts` via `await buildSystemPrompt()`. If you modify `system-prompt.ts`, the change only takes effect on a **new run** — not when resuming an existing one (Smithers caches the agent config).

**Fix**: Cancel the current run and start fresh:
```bash
bunx smithers cancel workflow.tsx --run-id <run-id>
./run.sh
```

---

## 10. Agent Produces Natural Language Instead of JSON

**Symptom**: Task fails with schema validation error. Agent output is prose without a JSON block.

**Cause**: CLI agents (claude, codex) default to natural language. Without explicit instructions, they forget to output JSON.

**Fix** (all three are needed):
1. System prompt must include the `CRITICAL OUTPUT REQUIREMENT` block
2. Every MDX prompt must end with `## REQUIRED OUTPUT\n{props.schema}`
3. `outputSchema` must be passed to every `<Task>` (enables auto-retry on validation failure — up to 2 retries with error details)

---

## 11. MDX Prompts Render as `[object Object]`

**Symptom**: Agent receives `[object Object]` as its prompt instead of rendered markdown. The agent has no instructions and improvises. Visible in the DB:
```bash
sqlite3 smithers.db "SELECT substr(meta_json, 1, 200) FROM _smithers_attempts LIMIT 1;"
# {"prompt":"[object Object]", ...}
```

**Cause**: MDX files need Smithers' MDX compilation plugin registered via Bun's preload system. Without it, `.mdx` imports are raw JSX element objects, not rendered strings.

**Fix**: Create `preload.ts` and register it in `bunfig.toml`:
```ts
// preload.ts
import { mdxPlugin } from "smithers-orchestrator/mdx-plugin";
mdxPlugin();
```
```toml
# bunfig.toml
preload = ["./preload.ts"]
```

---

## 12. Claude Agent Delegates to Sub-Agents, JSON Lost

**Symptom**: Task times out or produces no JSON. The agent's response text says something like *"All the structured JSON output was provided at the end of my earlier response"* or references sub-agent results.

**Cause**: Claude Code's `Task` tool spawns background sub-agents. The JSON output ends up in a sub-agent's response, not in the main stdout that Smithers captures. Smithers only reads `stdout.trim()` from the final CLI execution — it does not accumulate text across multi-turn conversations or sub-agent results.

**How Smithers extracts JSON** (6 strategies in order):
1. Check `result._output` / `result.output` (structured output)
2. Parse full `result.text` if it starts with `{`
3. Search for ` ```json\n{...}\n``` ` code fences in main text
4. Search code fences in `result.steps[]` backwards
5. `extractBalancedJson()` from steps (balanced brace matching)
6. `extractBalancedJson()` from full text
7. If all fail → follow-up prompt: "output ONLY a valid JSON"

**Fix**: Add these rules to the system prompt:
```
## CRITICAL: Output Rules

1. DO NOT delegate to sub-agents or background tasks. Do all work yourself
   in the main conversation. Do not use the Task tool to spawn agents.
2. DO NOT respond early. Wait until ALL your work is fully complete before
   producing any final output. Never say "I'll do X" — do X, then report.
3. Your FINAL message MUST end with a raw JSON object matching the schema
   in your task prompt. No markdown fences. No text after the JSON.
4. Never reference "earlier responses" — your output is captured from a
   single response. All content must be in that one response.
```

---

## 13. Task Timeout (Default 300s)

**Symptom**: Task fails with `CLI timed out after 300000ms`. The agent was doing real work but didn't finish in time.

**Cause**: Smithers defaults to a 5-minute timeout per task. Complex tasks (research across large codebases, multi-file implementation) easily exceed this.

**Fix**: Add `timeoutMs` to heavy tasks:
```tsx
<Task
  id={props.id}
  agent={researcher}
  output={tables.research}
  outputSchema={ResearchSchema}
  timeoutMs={3_600_000}  // 1 hour
  retries={3}            // generous retry budget
>
```

**Recommended timeouts**:
| Task Type | Timeout | Retries |
|-----------|---------|---------|
| Research / Context Gather | 1 hr (3,600,000ms) | 3 |
| Implement | 1 hr (3,600,000ms) | 5 |
| Validate (build/test) | 10 min (600,000ms) | 2 |
| Review | 10 min (600,000ms) | 1 |
| FinalReview | 10 min (600,000ms) | 1 |
| ReviewFix | 30 min (1,800,000ms) | 3 |

**Why generous retries**: When a task exhausts its retry budget, `smithers resume` cannot re-attempt it — the run fails immediately. Setting retries high (3-5) for long tasks avoids dead runs from transient failures (network timeouts, API errors, schema issues). Unused retries cost nothing.

---

## 14. Zod 4 Schema Conversion — `type: "None"` Error

**Symptom**: Codex agent fails immediately with:
```
Invalid schema for response_format 'codex_output_schema':
schema must be a JSON Schema of 'type: "object"', got 'type: "None"'.
```

**Root cause**: A chain of three interacting issues in `smithers-orchestrator@0.6.0`:

1. Smithers depends on `zod@^4.3.6` but dropped `zod-to-json-schema` from its own deps when migrating to Zod 4
2. `zod-to-json-schema@3.25.1` gets pulled in **transitively** via `ai` → `@ai-sdk/ui-utils`
3. `zod-to-json-schema` v3 doesn't understand Zod 4 schemas — it **silently** returns `{"$schema":"..."}` with no `type`, no `properties`
4. The Codex CLI reads `type: undefined` → sends `type: "None"` → OpenAI rejects it

**Verified**: The dynamic `await import("zod-to-json-schema")` in `CodexAgent.buildCommand` is wrapped in try/catch and designed to silently skip when the module isn't installed. But since v3 IS installed (transitively), the import succeeds and produces garbage.

```ts
// What zodToJsonSchema v3 produces for a Zod 4 schema:
zodToJsonSchema(z.object({ name: z.string() }));
// → {"$schema":"http://json-schema.org/draft-07/schema#"}  ← EMPTY

// What Zod 4's built-in produces:
z.object({ name: z.string() }).toJSONSchema();
// → {"type":"object","properties":{"name":{"type":"string"}},...}  ← CORRECT
```

**Fix**: Apply a patch to replace `zodToJsonSchema()` with Zod 4's native `.toJSONSchema()`:

1. Create `patches/smithers-orchestrator@0.6.0.patch`:
```diff
--- a/src/agents/cli.ts
+++ b/src/agents/cli.ts
@@ -830,8 +830,7 @@
     if (!this.opts.outputSchema && params.options?.outputSchema) {
       try {
-        const { zodToJsonSchema } = await import("zod-to-json-schema");
-        const jsonSchema = zodToJsonSchema(params.options.outputSchema);
+        const jsonSchema = params.options.outputSchema.toJSONSchema();
         const schemaFile = join(
```

2. Add to `package.json`:
```json
"patchedDependencies": {
  "smithers-orchestrator@0.6.0": "patches/smithers-orchestrator@0.6.0.patch"
}
```

3. Run `bun install` — Bun auto-applies the patch.

**Verify**: Check the patched file:
```bash
grep -A1 "outputSchema" node_modules/smithers-orchestrator/src/agents/cli.ts | grep toJSONSchema
# Should show: const jsonSchema = params.options.outputSchema.toJSONSchema();
```
