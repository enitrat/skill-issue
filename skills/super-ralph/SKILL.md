---
name: super-ralph
description: >
  Build multi-phase AI development pipelines with the Smithers workflow engine (v0.8.2). Use when:
  (1) Setting up a SuperRalph workflow for a repo (focuses, focusDirs, focusTestSuites, agents)
  (2) Debugging a run (ticket explosion, duplicate tickets, stalled nodes)
  (3) Understanding the pipeline phases and what generates tickets
  (4) Avoiding common configuration mistakes that cause runaway ticket counts
---

# Super-Ralph

Ticket-driven multi-agent development. A `<SuperRalph>` component inside a Smithers workflow
drives a full pipeline: codebase review → ticket discovery → parallel TDD implementation → merge queue.

Runtime: Bun >= 1.3. VCS: jj-colocated git. State: SQLite (resumable).

---

## The Ticket Explosion Problem (Read This First)

SuperRalph generates tickets from **two independent sources** that run in parallel:

1. **`codebase-review:*`** — one agent per focus; each reads the codebase and emits `suggestedTickets`
2. **`discover`** — one global agent that reads specs and emits `tickets`

`selectAllTickets` merges both lists and **deduplicates by ticket ID** (review tickets win on collision).
The dedup only works when both sources produce the **same ID** for the same piece of work.
In practice they never do: `codebase-review:architecture` emits `RZMA-003`, `discover` emits
`encrypt-credentials-at-rest` — different IDs, no dedup, both get full 10-step pipelines.

Without proper configuration the explosion looks like:
- No `focusDirs` → all reviewers scan the whole repo, each finds all issues independently
- A catch-all focus (e.g. `"architecture"`) re-discovers everything the other 6 reviewers found,
  with different ticket IDs, so dedup doesn't fire
- No `setupHints` → reviewers re-ticket already-completed work
- Result: 7 focuses × ~10 tickets + discover's 5 = 75 tickets, ~80% overlap → 500+ wasted nodes

Note: `integration-test:*` nodes also have a `suggestedTickets` field but these are **string hints
only** — they do not enter the ticket pipeline. Only `codebase-review` and `discover` generate
runnable tickets.

**The rule: every ticket must be generatable by exactly one source, with a predictable ID.**

---

## Correct Focus Design

### The Three Mandatory Constraints

**1. Every focus must have `focusDirs`**

Without directory scoping, reviewers read the whole codebase and find everything.
`focusDirs` restricts each agent to its own slice.

```ts
// components/focusDirs.ts
export const focusDirs: Record<FocusId, string[]> = {
  "auth":        ["src/auth/", "src/middleware/auth.ts"],
  "api-routes":  ["src/routes/", "src/controllers/"],
  "build":       ["tsup.config.ts", "package.json", ".gitignore"],
};
```

**2. Every focus must have `focusTestSuites.setupHints` listing what's already done**

This prevents reviewers from re-discovering and re-ticketing completed work.

```ts
// components/focusTestSuites.ts
export const focusTestSuites = {
  "auth": {
    suites: ["bun test test/auth/"],
    setupHints: [
      "ALREADY DONE: JWT issuance, session management, SIWE — do not re-ticket",
      "GAPS: OAuth provider integration, 2FA flow — these need tickets",
    ],
    testDirs: ["test/auth/"],
  },
};
```

**3. No catch-all focuses**

A focus like `"architecture"` or `"general"` with no directory constraint will duplicate
everything every other focus finds. Every focus must map to a bounded, non-overlapping
directory set.

### Good vs Bad Focuses

```ts
// GOOD: bounded, non-overlapping, each maps to specific dirs
export const focuses = [
  { id: "build-tooling",  name: "Build system: tsup migration, .gitignore, dist cleanup" },
  { id: "auth-crypto",    name: "Credential encryption at rest: AES-GCM + PBKDF2" },
  { id: "query-hooks",    name: "TanStack Query: Suspense variants, handle-in-key pattern" },
  { id: "worker",         name: "Web Worker protocol: typed messages, timeout, crash recovery" },
] as const;

// BAD: overlapping, unbounded, catch-all
export const focuses = [
  { id: "architecture",   name: "Architecture" },           // reads everything, duplicates all
  { id: "security",       name: "Security improvements" },  // overlaps with any feature focus
  { id: "code-quality",   name: "Code quality" },           // undefined scope
] as const;
```

### When to Remove a Focus

Remove a focus as soon as its area reaches production quality. Keeping done focuses active
wastes agent cycles re-reviewing complete code. Add a comment explaining why it was removed
(see plue's `focuses.ts` for the pattern).

---

## Planning Prompt Must List Completed Work

The `PLANNING_PROMPT` passed to agents must explicitly list what is already implemented.
Without this, planners re-ticket completed features.

```ts
const PLANNING_PROMPT = `You are implementing <project> improvements.

## Already implemented — DO NOT re-ticket
- Authentication: JWT, sessions, SIWE all working
- Error hierarchy: FhevmError and all 12 subclasses exported
- Build: dist/ in .gitignore, tsc passing

## Gaps to address (create tickets for these only)
- Credential encryption at rest (plaintext keypair in localStorage)
- Suspense hook variants (5 hooks need useSuspenseQuery wrappers)
- tsup migration (currently using tsc, no code splitting)
`;
```

---

## Workflow File Structure

```
scripts/smithers-factory/
├── index.ts              # Run manager (interactive resume/cancel UI)
├── smithers.ts           # createSmithers() bootstrap
├── config.ts             # WORKFLOW_MAX_CONCURRENCY, WORKFLOW_TASK_RETRIES
├── components/
│   ├── workflow.tsx      # <SuperRalph> wiring
│   ├── focuses.ts        # Focus definitions (ONLY non-overlapping, bounded scopes)
│   ├── focusDirs.ts      # Directory hints per focus (MANDATORY)
│   └── focusTestSuites.ts # Setup hints per focus (MANDATORY)
└── react-sdk-rfc003-build.db   # SQLite state (auto-created)
```

---

## Minimal Correct workflow.tsx

```tsx
import { ClaudeCodeAgent } from "smithers-orchestrator";
import { SuperRalph } from "super-ralph";
import { WORKFLOW_MAX_CONCURRENCY, WORKFLOW_TASK_RETRIES } from "../config";
import { outputs, smithers, Workflow } from "../smithers";
import { focuses } from "./focuses";
import { focusDirs } from "./focusDirs";
import { focusTestSuites } from "./focusTestSuites";

const REPO_ROOT = new URL("../../..", import.meta.url).pathname.replace(/\/$/, "");

// CRITICAL: list completed work here so agents don't re-ticket it
const PLANNING_PROMPT = `...
## Already done — skip these
- ...
## Gaps that need tickets
- ...
`;

export default smithers((ctx) => (
  <Workflow name="my-factory">
    <SuperRalph
      ctx={ctx}
      outputs={outputs}
      focuses={focuses}
      focusDirs={focusDirs}           {/* MANDATORY — scopes each reviewer */}
      focusTestSuites={focusTestSuites} {/* MANDATORY — prevents re-ticketing done work */}
      projectId="my-project"
      projectName="My Project"
      specsPath="docs/"
      referenceFiles={["docs/spec.md", "src/index.ts"]}
      buildCmds={{ typecheck: "bun run typecheck", build: "bun run build" }}
      testCmds={{ unit: "bun run test" }}
      codeStyle="TypeScript strict, ESM-only"
      reviewChecklist={["Spec compliance", "Type safety", "Test coverage"]}
      maxConcurrency={WORKFLOW_MAX_CONCURRENCY}
      taskRetries={WORKFLOW_TASK_RETRIES}
      agents={{
        planning: new ClaudeCodeAgent({
          model: "claude-sonnet-4-6",
          systemPrompt: PLANNING_PROMPT,
          cwd: REPO_ROOT,
          dangerouslySkipPermissions: true,
          timeoutMs: 30 * 60 * 1000,
        }),
        implementation: new ClaudeCodeAgent({
          model: "claude-sonnet-4-6",
          systemPrompt: IMPLEMENTATION_PROMPT,
          cwd: REPO_ROOT,
          dangerouslySkipPermissions: true,
          timeoutMs: 60 * 60 * 1000,
        }),
        testing: new ClaudeCodeAgent({ ... }),
        reviewing: new ClaudeCodeAgent({ ... }),
        reporting: new ClaudeCodeAgent({ ... }),
      }}
    />
  </Workflow>
));
```

---

## Configuration Review (Mandatory Before Running)

After creating all config files, **always run a validation pass using `AskUserQuestion`**
before starting the workflow. This catches ticket explosion setups before they waste hours.

### What to Review

Do three `AskUserQuestion` calls in sequence:

**Call 1 — Focus scope review (one question per focus, up to 4 at a time)**

For each focus, show the focus name + its `focusDirs` + `setupHints` as a markdown preview.
The user can comment on any that have wrong scope or missing hints.

```
AskUserQuestion([
  {
    question: "Does focus 'build-tooling' look correctly scoped?",
    header: "build-tooling",
    options: [
      { label: "Looks good", description: "Dirs and hints are correct" },
      { label: "Has issues", description: "I'll describe in notes" },
    ],
    // markdown preview shows:
    // Focus: build-tooling — Build system: tsup, .gitignore, dist
    // Dirs: ["package.json", "tsup.config.ts", ".gitignore"]
    // Already done: [...]
    // Gaps: [...]
  },
  // ... up to 3 more focuses per call
])
```

Batch up to 4 focuses per call. For 8 focuses that's 2 calls.

**Call 2 — Overlap and catch-all check**

One question, 3 options:

```
AskUserQuestion([
  {
    question: "Do any focuses overlap in scope or act as a catch-all for the whole codebase?",
    header: "Overlap check",
    options: [
      { label: "No overlap — all focuses are bounded", description: "Safe to proceed" },
      { label: "One focus is too broad", description: "I'll name it in notes" },
      { label: "Multiple focuses overlap", description: "Need to redesign" },
    ],
  },
  {
    question: "Does the planning prompt's 'already done' list look complete?",
    header: "Planning prompt",
    options: [
      { label: "Complete", description: "Nothing missing from the done list" },
      { label: "Missing items", description: "Agents may re-ticket completed work" },
    ],
  },
])
```

**Call 3 — Final gate**

```
AskUserQuestion([
  {
    question: "Ready to start the workflow?",
    header: "Start run",
    options: [
      { label: "Start", description: "Configuration looks correct" },
      { label: "Fix first", description: "Make the changes I noted, then re-review" },
    ],
  },
])
```

Only proceed past this gate when the user selects "Start". If they select "Fix first",
apply their notes and repeat from Call 1 for affected focuses.

### Review Checklist (verify each before proceeding)

- [ ] Every focus has a `focusDirs` entry with at least one directory
- [ ] No focus has dirs that overlap with another focus's dirs
- [ ] No focus is named `"architecture"`, `"general"`, `"code-quality"`, or any other catch-all
- [ ] Every focus has `setupHints` that list completed work in that area
- [ ] Planning prompt has an explicit `ALREADY IMPLEMENTED` section
- [ ] Planning prompt has an explicit `GAPS` section with what needs tickets
- [ ] Total expected tickets (focuses × avg tickets/focus) stays below ~60

---

## Debugging a Run via SQLite

```bash
DB="scripts/smithers-factory/react-sdk-rfc003-build.db"

# Run status
sqlite3 $DB "SELECT run_id, status, datetime(created_at_ms/1000,'unixepoch','localtime') FROM _smithers_runs ORDER BY created_at_ms DESC LIMIT 5;"

# Overall progress
sqlite3 $DB "SELECT state, COUNT(*) FROM _smithers_nodes WHERE run_id='<id>' GROUP BY state;"

# Currently active nodes
sqlite3 $DB "SELECT node_id, state, datetime(updated_at_ms/1000,'unixepoch','localtime') FROM _smithers_nodes WHERE run_id='<id>' AND state='in-progress';"

# Ticket-level breakdown
sqlite3 $DB "
SELECT
  CASE WHEN node_id LIKE '%:%' THEN substr(node_id,1,instr(node_id,':')-1) ELSE node_id END as ticket,
  SUM(CASE WHEN state='finished' THEN 1 ELSE 0 END) as done,
  SUM(CASE WHEN state='in-progress' THEN 1 ELSE 0 END) as active,
  SUM(CASE WHEN state='pending' THEN 1 ELSE 0 END) as pending
FROM _smithers_nodes WHERE run_id='<id>'
GROUP BY ticket ORDER BY done DESC;
"

# What discover generated (the 5 high-level tickets)
sqlite3 $DB "SELECT tickets FROM discover WHERE run_id='<id>';" | python3 -c "import sys,json; [print(t['id'],'-',t['title']) for t in json.loads(sys.stdin.read())]"

# What a category reviewer generated (check for overlap)
sqlite3 $DB "SELECT suggested_tickets FROM category_review WHERE run_id='<id>' AND node_id='codebase-review:architecture';" | python3 -c "import sys,json; [print(t['id'],'-',t['title']) for t in json.loads(sys.stdin.read())]"
```

---

## Resume / Cancel

```bash
# Interactive run manager
bun run index.ts

# Skip phases on fresh start (when codebase is already reviewed)
SKIPTO_PHASE=TICKETS bun run index.ts
```

---

## Props Reference

See [references/customization.md](references/customization.md) for the full `<SuperRalph>` props table,
agent fallback chains, per-focus configuration, and pipeline step overrides.
