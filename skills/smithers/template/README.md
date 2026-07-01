# Smithers Workflow Engine

A generic, reusable multi-phase development workflow built on
[smithers-orchestrator](https://smithers.sh). The core workflow is
project-agnostic — all domain-specific content lives in a separate project
config.

## Structure

```
scripts/smithers-factory/
  components/                           # Generic workflow components
    index.ts                            # Barrel export
    schemas.ts                          # Schema registry for createSmithers()
    PassTracker/schema.ts
    UpdateProgress/{index.tsx, prompt.mdx, schema.ts}
    PhasePipeline/
      index.tsx                         # Phase lifecycle: Research → Plan → ValidationLoop → FinalReview
      Research/{index.tsx, prompt.mdx, schema.ts}
      Plan/{index.tsx, prompt.mdx, schema.ts}
      FinalReview/{index.tsx, prompt.mdx, schema.ts}
      ImplementAndValidate/
        index.tsx                       # Implement → Test → Review → Fix sequence
        shared.ts                       # Issue schema shared across reviews
        Implement/{index.tsx, prompt.mdx, schema.ts}
        Test/{index.tsx, prompt.mdx, schema.ts}
        Review/
          index.tsx                     # Parallel wrapper for CodeReview + PRDReview
          CodeReview/{index.tsx, prompt.mdx, schema.ts}
          PRDReview/{index.tsx, prompt.mdx, schema.ts}
        ReviewFix/{index.tsx, prompt.mdx, schema.ts}
  types/project.ts                      # ProjectConfig interface
  agents.ts                             # Agent factory with per-role overrides
  smithers.ts                           # Framework bootstrap (DB + caching)
  workflow.tsx                          # Root workflow (outer Ralph loop over phases)
  project.ts                            # Loads project config via SMITHERS_PROJECT env var
  utils.ts                              # renderInstructions() helper
  preload.ts                            # Bun MDX loader plugin
```

## How It Works

### Project Loading

The workflow is project-agnostic. At runtime, it loads a project config via
dynamic import:

```
run.sh                          project.ts                        workflow.tsx / agents.ts / components
  │                               │                                 │
  │  export SMITHERS_PROJECT=     │  const configPath =             │  import { project }
  │    "./config.js"              │    process.env.SMITHERS_PROJECT │    from "./project.js"
  │                               │  export const project =         │
  └──────────────────────────────►│    await import(configPath)    ─┘
```

`project.ts` reads the `SMITHERS_PROJECT` env var (defaults to
`./projects/template-smithers/smithers-config/config.js`) and dynamically imports
it. Every other module imports `project` from this single entry point.

### Workflow Lifecycle

Each phase goes through this pipeline:

```
         ┌─ outer Ralph loop re-runs incomplete phases ─┐
         ▼                                              │
Research → Plan → Implement → Test → CodeReview ∥ PRDReview → ReviewFix → FinalReview
                  └──────────── ImplementAndValidate ────────────────────┘
```

- **Research**: Gathers reference material, writes a context doc
- **Plan**: Creates an implementation plan from research findings
- **ImplementAndValidate**: Runs once per pass (iteration comes from the outer
  Ralph loop)
  - **Implement**: Writes code using plan + feedback from prior pass
  - **Test**: Runs build + test suite
  - **CodeReview + PRDReview**: Run in parallel — code quality and spec
    compliance
  - **ReviewFix**: Addresses review issues (skipped if both reviews approve)
- **FinalReview**: Gatekeeper — decides if the phase is complete
  (`readyToMoveOn`)

The outer loop (`Ralph`) iterates over all phases up to `maxPasses` times.
Completed phases are skipped on subsequent passes.

### Caching

Smithers caching is enabled (`<Workflow cache>`). Cache keys include the prompt
text, so:

- Re-runs after crashes skip completed steps
- Changing project instructions invalidates affected caches
- Iterative steps (ImplementAndValidate) get different prompts each pass due to
  feedback, so they don't hit cache inappropriately

### Two-Layer Prompt System

Each component has a **generic prompt** (`prompt.mdx`) co-located in its folder.
These define the task structure and generic instructions. Project instructions
are **injected into** (not replacing) the generic prompt via a
`{props.projectInstructions}` slot.

**Project instructions are additive** — there is no mechanism to override a
generic prompt entirely. The generic prompt always controls the overall
structure, and project content fills the domain-specific section.

```
Generic prompt (co-located)               Project instructions (in project config)
┌───────────────────────────────┐         ┌──────────────────────────────┐
│ # RESEARCH — {phaseName}      │         │ ## PRD                       │
│                               │         │ Read lib/FOUNDRY_PRD.md  │
│ ## Objective                  │         │                              │
│ Gather reference material...  │         │ ## Reference Files           │
│                               │  inject │ - library-solidity/lib/FHE.. │
│ ## Project-Specific Instructions│  ───►  │ - hardhat-plugin-v3/src/...  │
│ {props.projectInstructions}   │         └──────────────────────────────┘
│                               │
│ ## Generic Research Steps     │    ← always present, not overridable
│ 1. Read spec docs...         │
│ 2. Write context document... │
└───────────────────────────────┘
```

The injection flow:

1. Component calls `renderInstructions("research", phase.metadata)`
2. This loads the project's `instructions/research.mdx` and renders it with
   phase metadata as props
3. The rendered string is passed as `projectInstructions` to the generic
   `prompt.mdx`

## Creating a New Project

To use this workflow on a different PRD/codebase:

### 1. Create a project directory

```
projects/<your-project>/smithers-config/
  config.ts
  instructions/
    research.mdx
    plan.mdx
    implement.mdx
    test.mdx
    code-review.mdx
    prd-review.mdx
    review-fix.mdx
    final-review.mdx
    update-progress.mdx
  output/
    context/.gitkeep
    plans/.gitkeep
  run.sh
```

### 2. Define your project config (`config.ts`)

Your config must satisfy the `ProjectConfig` interface:

```ts
import type { ProjectConfig } from "../../../scripts/smithers-factory/types/project.js";

// Import your instruction templates
import ResearchInstructions from "./instructions/research.mdx";
// ... (one per step)

const config: ProjectConfig = {
  name: "My Project",
  workflowName: "my-project", // Used for DB naming + cache scoping
  phases: [
    {
      id: "phase-0-foundation",
      name: "Foundation Layer",
      description: "Implement the core foundation...",
      metadata: {
        // Arbitrary data passed to instruction templates
        specSections: ["2.1", "2.2"],
        referenceFiles: ["src/core.ts", "src/types.ts"],
      },
    },
    // ... more phases
  ],
  maxPasses: 5,
  maxReviewRounds: 5,
  cwd: "/path/to/your/repo", // Agents' working directory
  outputDir: "projects/my-project/smithers-config/output",
  instructions: {
    research: ResearchInstructions,
    plan: PlanInstructions,
    implement: ImplementInstructions,
    test: TestInstructions,
    "code-review": CodeReviewInstructions,
    "prd-review": PRDReviewInstructions,
    "review-fix": ReviewFixInstructions,
    "final-review": FinalReviewInstructions,
    "update-progress": UpdateProgressInstructions,
  },
  agents: {
    systemPromptContent: `
      ## PROJECT CONTEXT
      You are building ...

      ## RULES
      ...
    `,
    overrides: {
      // Optional per-role overrides
      implementer: { model: "gpt-5.3-codex" },
      researcher: { model: "claude-opus-4-6" },
    },
  },
};

export default config;
```

### 3. Write instruction templates

Each instruction MDX file receives the phase's `metadata` as props. Example
`instructions/research.mdx`:

```mdx
## Spec Reference

Read `docs/SPEC.md` sections {props.specSections}

## Reference Files

- {props.referenceFiles}
```

The `metadata` values are stringified before injection:

- Arrays are joined with `\n- `
- Other values are converted via `String()`

### 4. Create a launcher (`run.sh`)

```bash
#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SMITHERS_DIR="$(cd "$SCRIPT_DIR/../../../scripts/smithers-factory" && pwd)"

cd "$SMITHERS_DIR"
export SMITHERS_PROJECT="$SCRIPT_DIR/config.js"

# ── Check for runs that need attention (running or cancelled) ─────────────────
PENDING_JSON=$(bunx smithers list workflow.tsx --limit 20 2>/dev/null \
  | jq -c '[.[] | select(.status == "running" or .status == "cancelled")]' 2>/dev/null || echo "[]")

PENDING_COUNT=$(echo "$PENDING_JSON" | jq 'length')

if [[ "$PENDING_COUNT" -gt 0 ]]; then
  echo "Found $PENDING_COUNT run(s) that can be resumed:"
  echo ""
  echo "$PENDING_JSON" | jq -r '.[] | "  [\(.status)] \(.runId)  started \(.createdAtMs / 1000 | todate)"'
  echo ""

  while IFS= read -r run; do
    RUN_ID=$(echo "$run" | jq -r '.runId')
    STATUS=$(echo "$run" | jq -r '.status')
    STARTED=$(echo "$run" | jq -r '.createdAtMs / 1000 | todate')

    # Query last attempt from DB for context
    DB_PATH="$SMITHERS_DIR/smithers.db"  # adjust to your DB filename
    LAST_ATTEMPT=$(sqlite3 "$DB_PATH" \
      "SELECT node_id, state, attempt FROM _smithers_attempts \
       WHERE run_id = '$RUN_ID' ORDER BY started_at_ms DESC LIMIT 1;" 2>/dev/null || echo "")

    echo "  [$STATUS] $RUN_ID"
    echo "  Started : $STARTED"
    if [[ -n "$LAST_ATTEMPT" ]]; then
      LAST_NODE=$(echo "$LAST_ATTEMPT" | cut -d'|' -f1)
      LAST_STATE=$(echo "$LAST_ATTEMPT" | cut -d'|' -f2)
      LAST_ATTEMPT_N=$(echo "$LAST_ATTEMPT" | cut -d'|' -f3)
      echo "  Last    : $LAST_NODE  ($LAST_STATE, attempt $LAST_ATTEMPT_N)"
    fi
    echo ""
    read -r -p "  [r]esume  [d]iscard  [s]kip → " choice </dev/tty
    echo ""

    case "$(echo "$choice" | tr '[:upper:]' '[:lower:]')" in
      r)
        echo "Resuming $RUN_ID..."
        exec bunx smithers resume workflow.tsx --run-id "$RUN_ID"
        ;;
      d)
        if [[ "$STATUS" == "running" ]]; then
          # Cancel first so smithers cleans up internal state, then stamp as failed
          # so it won't reappear in the running/cancelled filter next time.
          bunx smithers cancel workflow.tsx --run-id "$RUN_ID" 2>/dev/null || true
        fi
        sqlite3 "$DB_PATH" \
          "UPDATE _smithers_runs SET status = 'failed', finished_at_ms = strftime('%s','now') * 1000 \
           WHERE run_id = '$RUN_ID';" 2>/dev/null || true
        echo "  Discarded."
        ;;
      *)
        echo "  Skipped."
        ;;
    esac
  done < <(echo "$PENDING_JSON" | jq -c '.[]')
fi

# ── Start a new run ───────────────────────────────────────────────────────────
echo "Starting new run..."
bunx smithers run workflow.tsx
```

### 5. Run it

```bash
./projects/my-project/smithers-config/run.sh

# Or run a single phase:
./projects/my-project/smithers-config/run.sh phase-0-foundation
```

## Agent Roles

| Role            | Default Model   | Mode                | Description                                               |
| --------------- | --------------- | ------------------- | --------------------------------------------------------- |
| `implementer`   | gpt-5.3-codex   | yolo (write)        | Writes code, fixes compilation errors                     |
| `researcher`    | claude-opus-4-6 | default (read-only) | Gathers reference material, writes plans, tracks progress |
| `prdReviewer`   | claude-opus-4-6 | default (read-only) | Verifies spec/PRD compliance                              |
| `codeReviewer`  | claude-opus-4-6 | default (read-only) | Reviews code quality, conventions, security               |
| `finalReviewer` | claude-opus-4-6 | default (read-only) | Gatekeeper — decides phase completion                     |

Override any role in your project config:

```ts
agents: {
  overrides: {
    implementer: { model: "different-model", timeoutMs: 7200000 },
    researcher: { systemPrompt: "Additional role-specific instructions..." },
  },
}
```

## Schemas

All schemas are generic and co-located with their components. Key output tables:

| Table          | Schema            | Purpose                                          |
| -------------- | ----------------- | ------------------------------------------------ |
| `research`     | ResearchSchema    | Context file path, findings, references read     |
| `plan`         | PlanSchema        | Plan file path, implementation steps, files list |
| `implement`    | ImplementSchema   | Summary, files created/modified, commit messages |
| `test_results` | TestSchema        | Build/test pass status, failing summary          |
| `prd_review`   | PRDReviewSchema   | Severity, issues with references, spec coverage  |
| `code_review`  | CodeReviewSchema  | Severity, issues, quality dimensions             |
| `review_fix`   | ReviewFixSchema   | Fixes made, false positives, resolution status   |
| `final_review` | FinalReviewSchema | readyToMoveOn gate, quality score, reasoning     |
| `pass_tracker` | PassTrackerSchema | Pass number, phases run/complete                 |
| `progress`     | ProgressSchema    | Progress markdown, per-phase completion %        |

Schemas use `.nullable()` (never `.optional()`) due to OpenAI structured outputs
constraints.

## Environment Variables

| Variable           | Default                                              | Description                       |
| ------------------ | ---------------------------------------------------- | --------------------------------- |
| `SMITHERS_PROJECT` | `./projects/template-smithers/smithers-config/config.js` | Path to project config            |
| `SKIP_PHASES`      | (none)                                               | Comma-separated phase IDs to skip |
| `USE_CLI_AGENTS`   | `1`                                                  | Force CLI agent mode              |
| `SMITHERS_DEBUG`   | (none)                                               | Show engine errors                |
