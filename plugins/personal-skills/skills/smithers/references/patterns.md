# Production Smithers Patterns

Battle-tested patterns from building multi-phase AI development pipelines.

---

## 1. Outer Ralph Loop (Multi-Phase Iteration)

Wrap ALL phases in a single `<Ralph>` loop instead of giving each phase its own loop.
Phases that complete (`readyToMoveOn: true`) are skipped on subsequent passes.

```tsx
export default smithers((ctx) => {
  // ⚠️ CRITICAL: Use ctx.latest() for cross-iteration decisions (skipIf, loop termination).
  // ctx.outputMaybe() is SCOPED TO THE CURRENT ITERATION — it won't see outputs
  // from previous Ralph iterations. ctx.latest() returns the highest-iteration output.
  const phaseComplete = (id: string) => {
    const finalReview = ctx.latest(
      "finalReview",
      `${id}:final-review`,
    );
    return finalReview?.readyToMoveOn ?? false;
  };

  const allPhasesComplete = PHASES.every(({ id }) => phaseComplete(id));
  const passTracker = ctx.outputMaybe("passTracker", { nodeId: "pass-tracker" });
  const currentPass = passTracker?.totalIterations ?? 0;
  const done = currentPass >= MAX_PASSES || allPhasesComplete;

  return (
    <Workflow name="my-build">
      <Ralph
        until={done}
        maxIterations={MAX_PASSES * PHASES.length * 20}
        onMaxReached="return-last"
      >
        <Sequence>
          {PHASES.map(({ id, name }) => (
            <Sequence key={id} skipIf={phaseComplete(id) || SKIP_PHASES.has(id)}>
              {/* steps here, all using ${id}:step-name nodeIds */}
            </Sequence>
          ))}

          {/* Pass tracker at the end */}
          <Task id="pass-tracker" output={tables.passTracker} outputSchema={PassTrackerSchema}>
            {{ totalIterations: currentPass + 1, /* ... */ }}
          </Task>
        </Sequence>
      </Ralph>
    </Workflow>
  );
});
```

**Why**: Enables cross-phase refinement. Phase 2 can benefit from fixes made in phase 1's re-iteration. Single loop = simpler state management than nested loops.

**maxIterations formula**: `MAX_PASSES * numPhases * stepsPerPhase` — generous to account for Ralph's per-step counting.

---

## 2. readyToMoveOn Gating

A dedicated FinalReview step at the end of each phase decides whether the phase is done.

```ts
// FinalReview.schema.ts
export const FinalReviewSchema = z.object({
  readyToMoveOn: z.boolean(),  // the gate flag
  reasoning: z.string(),        // fed back to next pass's Implement step
  approved: z.boolean(),
  qualityScore: z.number().min(1).max(10),
  remainingIssues: z.array(z.object({
    severity: z.enum(["critical", "major", "minor"]),
    description: z.string(),
    file: z.string().nullable(),  // .nullable() not .optional() — OpenAI rejects optional
  })),
});
```

**Decision criteria** (in FinalReview.mdx):
- `readyToMoveOn: true` ONLY if: tests pass, typecheck passes, both reviewers approved (or issues minor only), all quality scores >= 7
- `readyToMoveOn: false`: the `reasoning` field explains what still needs work — this feeds into the next pass's Implement prompt

---

## 3. Phase-Prefixed nodeIds

When multiple phases share one Ralph loop, every `<Task>` needs a unique nodeId.

```tsx
// Pattern: ${phaseId}:${stepName}
<ContextGather nodeId={`${id}:context-gather`} />
<Implement     nodeId={`${id}:implement`} />
<Validate      nodeId={`${id}:validate`} />
<Review        nodeIdClaude={`${id}:review-claude`}
               nodeIdCodex={`${id}:review-codex`} />
<ReviewFix     nodeId={`${id}:review-fix`} />
<Refactor      nodeId={`${id}:refactor`} />
<FinalReview   nodeId={`${id}:final-review`} />
```

**Why**: Without prefixes, all phases write to the same nodeId and clobber each other's outputs. The prefix is also used in `ctx.outputMaybe()` lookups:

```tsx
const latestImpl = ctx.outputMaybe("implement", { nodeId: `${id}:implement` });
```

---

## 4. Data Threading Chain

Each step reads the previous step's output and passes only the fields the next step needs.

```
ContextGather → gaps, contextFilesWritten
    ↓
Implement → summary, filesCreated, filesModified
    ↓
Validate → testsPass, typecheckPass, testOutput, typecheckOutput
    ↓
Review[parallel] → approved, issues, summary (per reviewer)
    ↓
ReviewFix → summary (what was fixed)
    ↓
Refactor → summary
    ↓
FinalReview → readyToMoveOn, reasoning
    ↓ (feeds back to Implement on next pass)
```

**Critical threading points**:
- `FinalReview.reasoning` → `Implement.finalReviewFeedback` (next pass)
- `Validate.testOutput` → `Implement.failingTests` (next pass, only if tests failed)
- `ReviewFix.summary` → `Implement.reviewFixSummary` (avoid re-doing already-fixed issues)
- `Review.issues` → `Implement.previousIssues` (next pass)

```tsx
// workflow.tsx — data threading example
<Implement
  nodeId={`${id}:implement`}
  gaps={latestContext.gaps ?? []}
  contextFilesWritten={latestContext.contextFilesWritten ?? []}
  pass={currentPass + 1}
  previousIssues={[
    ...(latestReviewClaude?.issues ?? []),
    ...(latestReviewCodex?.issues ?? []),
  ]}
  previousSummary={latestImplement?.summary}
  finalReviewFeedback={latestFinalReview?.reasoning}
  failingTests={
    latestValidate && !latestValidate.testsPass
      ? latestValidate.testOutput
      : undefined
  }
  reviewFixSummary={latestReviewFix?.summary}
/>
```

---

## 5. Pass Tracking

An inline `<Task>` at the end of the `<Sequence>` (inside Ralph) records which pass just completed.

```ts
export const PassTrackerSchema = z.object({
  totalIterations: z.number(),
  phasesRun: z.array(z.string()),
  phasesComplete: z.array(z.string()),
  summary: z.string(),
});
```

```tsx
<Task id="pass-tracker" output={tables.passTracker} outputSchema={PassTrackerSchema}>
  {{
    totalIterations: currentPass + 1,
    phasesRun: PHASES.filter(({ id }) => !SKIP_PHASES.has(id) && !phaseComplete(id)).map(({ id }) => id),
    phasesComplete: PHASES.filter(({ id }) => phaseComplete(id)).map(({ id }) => id),
    summary: `Pass ${currentPass + 1} of ${MAX_PASSES} complete.`,
  }}
</Task>
```

**Why**: Gives the outer Ralph loop a persisted counter. `ctx.outputMaybe("passTracker")` reads the latest pass number, enabling the `currentPass >= MAX_PASSES` termination condition.

---

## 6. Dual-Model Review (Parallel)

Run two reviewers in parallel, each with `continueOnFail` so one failing doesn't block the other.

```tsx
export function Review({ nodeIdClaude, nodeIdCodex, outputSchema, ...props }) {
  return (
    <Parallel>
      <Task
        id={nodeIdClaude}
        output={tables.reviewClaude}
        outputSchema={outputSchema}
        agent={reviewerClaude}
        continueOnFail
      >
        <ReviewPrompt reviewer="Claude Opus" {...props} />
      </Task>
      <Task
        id={nodeIdCodex}
        output={tables.reviewCodex}
        outputSchema={outputSchema}
        agent={reviewerCodex}
        continueOnFail
      >
        <ReviewPrompt reviewer="Codex" {...props} />
      </Task>
    </Parallel>
  );
}
```

**Why**: Different models catch different issue classes. Claude Opus excels at architectural judgment; Codex at implementation rigor. `continueOnFail` prevents one timeout from blocking the entire pipeline.

---

## 7. ReviewFix with Skip Logic

Skip the fix step when both reviewers approved (nothing to fix).

```tsx
<Task
  id={nodeId}
  output={tables.reviewFix}
  outputSchema={outputSchema}
  agent={implementer}
  skipIf={allApproved || totalIssues === 0}
>
  <ReviewFixPrompt
    claudeIssues={claudeIssues}
    codexIssues={codexIssues}
    testsPass={testsPass}
    testOutput={testOutput}
  />
</Task>
```

**Why**: Saves agent invocation cost and time when reviews pass cleanly.

---

## 8. Config-Driven Phase Management

Centralize all configuration:

```ts
// config.ts
export const MAX_PASSES = 5;

export const SKIP_PHASES = new Set(
  (process.env.SKIP_PHASES ?? "").split(",").map(s => s.trim()).filter(Boolean),
);

export const PHASES = [
  { id: "phase-1-compliance", name: "Compliance & Type System" },
  { id: "phase-2-skills", name: "Skills Refactor" },
  { id: "phase-3-api", name: "Public API Surface" },
] as const;

export type PhaseId = (typeof PHASES)[number]["id"];

export const MODELS = {
  implementer: "gpt-5.3-codex",
  reviewerClaude: "claude-opus-4-6",
  reviewerCodex: "gpt-5.3-codex",
  contextGatherer: "claude-opus-4-6",
  finalReviewer: "claude-opus-4-6",
  refactorer: "gpt-5.3-codex",
} as const;
```

**Run modes**:
- All phases: `./run.sh`
- Single phase: `SKIP_PHASES=phase-2-skills,phase-3-api ./run.sh`
- Or: `./run.sh phase-1-compliance` (script sets SKIP_PHASES for you)

---

## 9. Schema Registry (createSmithers)

Maps table names to Zod schemas. Auto-generates SQLite tables with `runId`, `nodeId`, `iteration` columns.

```ts
export const { smithers, tables } = createSmithers({
  contextGather: ContextGatherSchema,
  implement: ImplementSchema,
  validate: ValidateSchema,
  reviewClaude: ReviewSchema,
  reviewCodex: ReviewSchema,   // same schema, different table
  reviewFix: ReviewFixSchema,
  refactor: RefactorSchema,
  finalReview: FinalReviewSchema,
  passTracker: PassTrackerSchema,
});
```

`ctx.outputMaybe("implement", { nodeId: "phase-1:implement" })` returns typed output from the `implement` table filtered by nodeId. Type inference works automatically — no casts needed.

---

## 10. System Prompt JSON Enforcement

Every agent's system prompt must include:

```
CRITICAL OUTPUT REQUIREMENT:
When you have completed your work, you MUST end your response with a JSON object
wrapped in a code fence. The JSON format is specified in your task prompt.
```

Without this, CLI agents (claude, codex) produce natural language and forget the JSON output.

---

## Anti-Patterns

| Anti-Pattern | Why It Fails | Do Instead |
|---|---|---|
| `ctx.outputMaybe()` for `skipIf` / loop termination | Scoped to current iteration — can't see previous iterations' outputs, so completed phases re-run | Use `ctx.latest(table, nodeId)` for any cross-iteration decision |
| Nested Ralph loops (per-phase inner loop) | Complex state, no cross-phase benefits | Single outer Ralph with `skipIf` gating |
| Hardcoded nodeIds in shared loop | Phases clobber each other's outputs | Phase-prefix: `${id}:step-name` |
| Passing entire output objects as props | Bloated prompts, wasted tokens | Destructure and pass only needed fields |
| `ctx.output()` (not Maybe) | Throws on first render when no output exists | Always use `ctx.outputMaybe()` |
| MDX prompt without `{props.schema}` | Agents guess the JSON format, fail validation | Always end with `## REQUIRED OUTPUT\n{props.schema}` |
| Missing `outputSchema` on `<Task>` | No auto-validation, no retry, no schema injection | Always pass `outputSchema` |
| No `continueOnFail` on parallel reviews | One timeout kills both | Add `continueOnFail` to each parallel Task |
| `.optional()` in Zod schemas | OpenAI structured outputs rejects properties missing from `required` array | Use `.nullable()` — agent sends `null`, property stays required |
