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
