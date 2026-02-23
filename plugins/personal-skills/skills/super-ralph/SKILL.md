---
name: smithers
description: >
  Initialize and configure super-ralph ticket-driven development workflows.
  Super-ralph is a batteries-included Smithers workflow that runs an infinite
  loop of: discover tickets → implement in parallel worktrees → TDD → review → land via merge queue.
  Use when:
  (1) Setting up a new super-ralph workflow in a repository
  (2) Customizing focuses, agent prompts, build/test commands, or review checklists
  (3) Configuring multi-agent fallback chains or per-focus test suites
  (4) Debugging super-ralph runs (resume, cancel, delete via the run manager)
  (5) Understanding the ticket pipeline (research → plan → implement → test → review → land)
---

# Super-Ralph Workflow

Ticket-driven development with multi-agent review loops. Wraps the Smithers engine
with a full pipeline: discover → research → plan → implement → test → review → land.

Runtime: Bun >= 1.3. VCS: jj-colocated git. State: SQLite (resumable).

## Init

```bash
uv run <skill-path>/scripts/init_super_ralph.py <target-dir> --root <relative-to-repo-root>
```

Options: `--name "My Project"`, `--id my-project`, `--no-install`, `--no-jj`.

This copies the template, patches placeholders, runs `bun install`, and initializes jj.

## Post-Init Customization (3 files)

### 1. `components/focuses.ts` — Domain Areas

Replace placeholder focuses with 6–15 areas matching your project's architecture.
Each focus drives CategoryReview audits, IntegrationTest suites, and ticket discovery.
Remove completed focuses to save agent time.

```ts
export const focuses = [
  { id: "auth", name: "Authentication (JWT, OAuth, sessions)" },
  { id: "api",  name: "REST API routes and middleware" },
  // ...
] as const;
```

### 2. `components/workflow.tsx` — Workflow Configuration

Fill in all `TODO` sections:

**Agent prompts** — project-specific instructions for each role (planning, implementation, testing, reviewing, reporting). Include architecture rules, security invariants, framework patterns, spec file paths.

**SuperRalph props:**

```tsx
specsPath="docs/specs/"                         // where spec docs live
referenceFiles={["SPEC.md", "src/", "test/"]}   // context for agents
buildCmds={{ ts: "pnpm run typecheck" }}        // must pass for build-verify
testCmds={{ unit: "pnpm test" }}                // must pass for test-verify
codeStyle="TypeScript strict, camelCase..."      // style guide for reviewers
reviewChecklist={["Spec compliance", ...]}       // violations → major/critical
```

**Agents** — adjust models per role, add fallback chains:

```tsx
agents={{
  planning: [
    new ClaudeCodeAgent({ model: "claude-opus-4-6", ... }),
    new GeminiAgent({ model: "gemini-2.5-pro", ... }),  // fallback
  ],
  implementation: new CodexAgent({ model: "gpt-5.3-codex", yolo: true, ... }),
  // ...
}}
```

### 3. `components/focuses.ts` — (optional) focusTestSuites / focusDirs

For per-focus test and directory hints, add `focusTestSuites.ts` and `focusDirs.ts`
then pass them as props to SuperRalph.

## Run

```bash
cd <target-dir> && bun run index.ts
```

The run manager shows all past runs with resume/cancel/delete options.

**Phase skipping:** `SKIPTO_PHASE=TICKETS bun run index.ts`
**Concurrency:** `WORKFLOW_MAX_CONCURRENCY=4 bun run index.ts`

## Pipeline Per Ticket

```
Research → Plan → [Implement → Test → BuildVerify → (SpecReview ∥ CodeReview) → ReviewFix?] → Report → MergeQueue
                  └──────────────── ValidationLoop (reruns if reviews fail) ────────────────┘
```

Global tasks run every Ralph iteration in parallel: UpdateProgress, CategoryReview (per focus),
Discover (3–5 new tickets), IntegrationTest (per focus).

## Key Requirements

- **jj** must be installed (`brew install jj`) — all VCS operations use jj, not raw git
- **bunfig.toml** with `preload = ["./preload.ts"]` is critical — without it, MDX prompts fail with `[object Object]` errors. This is the top-level preload (NOT `[run]` section)
- Agent `cwd` must point to the repo root (not the workflow directory)
- `delete process.env.CLAUDECODE` in index.ts allows Claude Code sub-processes inside a Claude Code session

## Resources

See [references/customization.md](references/customization.md) for the full SuperRalph props
reference, agent types, fallback chains, focus design guidelines, focusTestSuites/focusDirs
configuration, custom step overrides, and merge queue tuning.
