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

## 5. Diagnosing Suspiciously Fast Tasks

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

## 6. Manual Task Re-run via SQLite

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

## 7. Useful SQLite Inspection Queries

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

## 8. System Prompt Not Taking Effect

**Symptom**: Agent ignores system prompt instructions (e.g., workspace policy, JSON output requirement).

**Cause**: System prompt is built at import time in `agents.ts` via `await buildSystemPrompt()`. If you modify `system-prompt.ts`, the change only takes effect on a **new run** — not when resuming an existing one (Smithers caches the agent config).

**Fix**: Cancel the current run and start fresh:
```bash
bunx smithers cancel workflow.tsx --run-id <run-id>
./run.sh
```

---

## 9. Agent Produces Natural Language Instead of JSON

**Symptom**: Task fails with schema validation error. Agent output is prose without a JSON block.

**Cause**: CLI agents (claude, codex) default to natural language. Without explicit instructions, they forget to output JSON.

**Fix** (both are needed):
1. System prompt must include the `CRITICAL OUTPUT REQUIREMENT` block
2. `output={outputs.xxx}` must be passed to every `<Task>` (enables auto-retry on validation failure — up to 2 retries with error details)

---

## 10. Claude Agent Delegates to Sub-Agents, JSON Lost

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

## 11. Task Timeout (Default 300s)

**Symptom**: Task fails with `CLI timed out after 300000ms`. The agent was doing real work but didn't finish in time.

**Cause**: Smithers defaults to a 5-minute timeout per task. Complex tasks (research across large codebases, multi-file implementation) easily exceed this.

**Fix**: Add `timeoutMs` to heavy tasks:
```tsx
<Task
  id={props.id}
  agent={researcher}
  output={outputs.research}
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

## 12. Rate-Limited Agent Exhausts Retry Budget

**Symptom**: Task fails all retries immediately (sub-second each). Run log shows HTTP 429 or "rate limit exceeded" in the agent's stderr.

**Cause**: All retry attempts hit the same rate-limited model. Retrying Codex when Codex is rate-limited always fails immediately, burning the entire retry budget.

**Fix (v0.8.0+)**: Pass an agent array to `agent`. Smithers uses `agents[0]` on attempt 1, `agents[1]` on attempt 2, etc., automatically switching providers on each retry:

```tsx
import { CodexAgent, ClaudeCodeAgent } from "smithers-orchestrator";

const primary = new CodexAgent({ model: "gpt-5.3-codex", yolo: true, cwd });
const fallback = new ClaudeCodeAgent({ model: "claude-opus-4-6", permissionMode: "bypassPermissions", cwd });

<Task
  id={`${id}:implement`}
  output={outputs.implement}
  agent={[primary, fallback]}
  retries={3}
>
  ...
</Task>
```

> **Migration note**: The `fallbackAgent` prop was removed in v0.8.0. Replace `agent={primary} fallbackAgent={fallback}` with `agent={[primary, fallback]}`.

**Without agent arrays**: Cancel the run, wait for the rate limit to expire, then resume. Alternatively set `timeoutMs` high enough that the model's backoff period is covered, but this wastes wall-clock time.

---

## 13. Worktree Auto-Creation Failure

**Symptom**: Workflow fails at startup with an error like `fatal: '<path>' already exists` or `fatal: not a git repository` when using `<Worktree>`.

**Context (v0.7.1+)**: Smithers now auto-creates git/jj worktrees when `<Worktree path="...">` is used and the path doesn't exist. It walks up from the workflow file's directory to find the VCS root, then runs `git worktree add` or `jj workspace add`.

**Common causes and fixes**:

1. **Path already exists but isn't a worktree**: Git refuses to add a worktree at an existing directory.
   ```bash
   # Remove the stale directory first
   rm -rf /path/to/worktree
   # Then re-run — Smithers will recreate it
   ```

2. **No git/jj root found**: The workflow file is outside any git repository.
   ```bash
   # Check VCS root
   git -C /path/to/workflow/dir rev-parse --show-toplevel
   # If this fails, init a repo or move the workflow inside one
   ```

3. **Detached worktree from deleted branch**: A previous worktree was created from a branch that was since deleted.
   ```bash
   git worktree prune       # clean up stale worktree metadata
   git worktree list        # verify state
   ```

4. **jj workspace conflict**: `jj workspace add` fails if the workspace name conflicts.
   ```bash
   jj workspace list
   jj workspace forget <name>   # remove the stale one
   ```

---

## 14. Completed Phases Re-Run on Next Ralph Iteration

**Symptom**: A phase completed with `readyToMoveOn: true` in iteration N, but re-runs from scratch in iteration N+1. Tokens and time are wasted re-doing work.

**Cause**: `ctx.outputMaybe()` is **scoped to the current Ralph iteration**. When the loop advances to iteration N+1, `outputMaybe` looks for `iteration = N+1` in the database and finds nothing — so `isPhaseComplete` evaluates to `false` and the phase's `skipIf` doesn't trigger.

Internally, `outputMaybe` resolves like:
```ts
// key.iteration is undefined → falls back to the Ralph's current iteration
return (row.iteration ?? 0) === (key.iteration ?? currentIteration);
```

**Fix**: Use `ctx.latest()` instead of `ctx.outputMaybe()` for any cross-iteration decision:

```tsx
// WRONG — only sees current iteration, completed phases re-run
const finalReview = ctx.outputMaybe("finalReview", {
  nodeId: `${id}:final-review`,
});

// CORRECT — scans all iterations, returns highest
const finalReview = ctx.latest(
  "finalReview",
  `${id}:final-review`,
);
```

**Where to apply**: Any lookup whose result feeds into `skipIf`, loop `until` conditions, or `allPhasesComplete` checks. Keep `outputMaybe` for lookups that feed into prompts (you want the current iteration's data there).

| Method | Iteration Scope | Use For |
|---|---|---|
| `ctx.outputMaybe(table, { nodeId })` | Current iteration only | Reading earlier steps in same iteration for prompts |
| `ctx.latest(table, nodeId)` | Highest iteration across all | `skipIf`, loop termination, cross-iteration decisions |
