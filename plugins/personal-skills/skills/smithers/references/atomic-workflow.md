# Logical Unit Pipeline Pattern

The preferred workflow architecture: run the **full pipeline** (implement → test → review → fix → refactor → final-review) for each **logically complete unit of work**, not implement everything then review once.

---

## Core Principle

**Logical completeness, full validation.** Each Ralph iteration implements 1-2 logical units, then runs the entire quality pipeline. The final-review gate decides whether to loop for more units or move to the next phase.

**"Atomic" = one logical concern, NOT smallest possible diff.** A logical unit is the smallest change that is *independently meaningful*. Repetitive boilerplate that follows the same pattern N times is ONE unit:
- Adding 20 similar operator functions to a test suite = ONE unit
- Porting a test file with 14 similar test cases = ONE unit
- Copying 5 related contracts for a feature = ONE unit
- Adding a single complex function with novel logic = ONE unit

```
Pass 1: context → implement (unit A, B) → test → review → fix → refactor → final-review
                                                                                 ↓
                                                                    readyToMoveOn: false
                                                                                 ↓
Pass 2: context → implement (unit C, D) → test → review → fix → refactor → final-review
                                                                                 ↓
                                                                    readyToMoveOn: true → next phase
```

---

## nextLogicalUnit Chaining

The key mechanism: each implement step outputs what to do next. The next iteration's implement step receives this as its instruction.

### Implement Schema

```ts
export const ImplementSchema = z.object({
  filesCreated: z.array(z.string()),
  filesModified: z.array(z.string()),
  commitMessage: z.string(),
  whatWasDone: z.string().describe("Detailed description of the logical unit implemented"),
  nextLogicalUnit: z.string().describe(
    "Next logical unit of work. A logical unit is the smallest LOGICALLY COMPLETE change, " +
    "not the smallest possible diff. Repetitive boilerplate (e.g. adding N similar functions, " +
    "porting N similar test cases) is ONE unit, not N units."
  ),
});
```

### Implement Prompt (MDX)

```mdx
# Implement — {props.phase} — Pass {props.pass}

RULES:
- Implement one LOGICALLY COMPLETE unit of work
- Do NOT batch multiple UNRELATED changes
- DO batch RELATED repetitive work (same pattern applied N times = ONE unit)
- If the next work is templated boilerplate, do ALL of it in one step

{props.previousWork
  ? `Previous implementation did: ${props.previousWork.whatWasDone}\nNext logical unit to implement: ${props.previousWork.nextLogicalUnit}`
  : "Start with the first item from the plan."}

{props.failingTests ? `FIX THESE FAILING TESTS FIRST:\n${props.failingTests}` : ""}
{props.reviewFixes ? `Review fixes just applied: ${props.reviewFixes}` : ""}

## BATCHING RULE
If the next unit involves repetitive/templated work (same pattern applied N times),
do ALL instances in one step. Examples:
- Adding 10 operators with identical function signatures → ONE step
- Adding 3 test files that follow the same helper pattern → ONE step
- Porting N similar contracts with the same structure → ONE step

## GIT COMMIT RULES
- Make atomic commits — one logical concern per commit
- Repetitive/templated work (N similar items) is ONE commit, not N commits
- Format: "EMOJI type(scope): description"
- git add the specific files changed, then git commit
```

### Workflow Threading

```tsx
// implement-1 does unit A, outputs nextLogicalUnit: "add all euint32 operator tests"
<Task id={`${id}:implement-1`} output={outputs.implement} agent={codex}>
  {render(ImplementPrompt, {
    phase,
    previousWork: latestImplement1 ?? null,  // from previous Ralph pass
    failingTests: latestTest?.failingSummary ?? null,
    reviewFixes: latestReviewFix?.summary ?? null,
    implementPass: 1,
  })}
</Task>

// implement-2 picks up nextLogicalUnit from implement-1
<Task id={`${id}:implement-2`} output={outputs.implement} agent={codex}>
  {render(ImplementPrompt, {
    phase,
    previousWork: latestImplement1 ?? null,  // chains from implement-1
    implementPass: 2,
  })}
</Task>
```

The chain crosses Ralph iterations too: pass N's implement-2 outputs `nextLogicalUnit` → pass N+1's implement-1 picks it up.

### Final-Review Unit Override

The final-review agent has broader PRD context than the implementer. It can override an over-granular `nextLogicalUnit` with a properly batched instruction:

```ts
export const FinalReviewSchema = z.object({
  readyToMoveOn: z.boolean(),
  remainingIssues: z.array(z.string()),
  reasoning: z.string(),
  nextUnitOverride: z.string().nullable().describe(
    "If the implementer's nextLogicalUnit is too granular (e.g. 'add one more operator' when " +
    "10 similar operators remain), override with a batched instruction. Null if appropriate."
  ),
});
```

In `workflow.tsx`, prefer the reviewer's override:
```tsx
nextLogicalUnit={
  latestFinalReview?.nextUnitOverride ?? latestImplement?.nextLogicalUnit ?? null
}
```

---

## Strict Final-Review Gate

The final-review must be strict enough to **reject** when there's still work to do, forcing another Ralph iteration.

```mdx
# Final Review — STRICT GATE: {props.phase}

REFUSE to approve unless ALL criteria are met:
- ALL tests pass (unit, spec, integration)
- ALL public functions have tests
- ALL errors are handled (no silent failures)
- Architecture matches reference implementation
- Code style is clean
- Implementation is COMPLETE for this phase

Set readyToMoveOn: true ONLY if you genuinely cannot find ANYTHING to improve.

If readyToMoveOn: false, explain exactly what must be fixed — this feeds into the next pass's implement step.
```

The `reasoning` field from a rejected final-review feeds back into the next iteration's context/implement prompts, creating a directed feedback loop.

---

## Full Pipeline Per Phase (Workflow Structure)

```tsx
<Ralph until={done} maxIterations={MAX_PASSES * phasesPerIteration}>
  <Sequence>
    {PHASES.map(({ id, name }) => (
      <Sequence key={id} skipIf={isPhaseComplete(id)}>
        {/* 1. Gather/refresh context */}
        <Task id={`${id}:context`} ...>
          <ContextPrompt previousFeedback={latestFinalReview} />
        </Task>

        {/* 2. Implement 1-2 atomic units */}
        <Task id={`${id}:implement-1`} ...>
          <ImplementPrompt previousWork={latestImplement} implementPass={1} />
        </Task>
        <Task id={`${id}:implement-2`} ...>
          <ImplementPrompt previousWork={latestImplement1} implementPass={2} />
        </Task>

        {/* 3. Test everything */}
        <Task id={`${id}:test`} ...>
          <TestPrompt />
        </Task>

        {/* 4. Review */}
        <Task id={`${id}:review`} ...>
          <ReviewPrompt filesCreated={...} testResults={...} />
        </Task>

        {/* 5. Fix review issues */}
        <Task id={`${id}:review-fix`} skipIf={noIssues} ...>
          <ReviewFixPrompt issues={...} />
        </Task>

        {/* 6. Refactor */}
        <Task id={`${id}:refactor`} ...>
          <RefactorPrompt />
        </Task>

        {/* 7. Final gate — loops back if not ready */}
        <Task id={`${id}:final-review`} ...>
          <FinalReviewPrompt testResults={...} />
        </Task>
      </Sequence>
    ))}

    {/* Pass tracker */}
    <Task id="pass-tracker" ...>
      {{ totalIterations: currentPass + 1, ... }}
    </Task>
  </Sequence>
</Ralph>
```

---

## Why This Pattern Works

| Aspect | Big-Batch (anti-pattern) | Over-Granular (anti-pattern) | Logical Unit Pipeline |
|--------|--------------------------|------------------------------|----------------------|
| Implement scope | Everything at once | One function per iteration | 1-2 logical units per pass |
| Review quality | Reviewer overwhelmed | Reviewer rubber-stamps trivial diffs | Reviewer focuses on meaningful change |
| Test feedback | Tests run once at end | Tests run but catch nothing new | Tests run after each logical change |
| Fix cost | Large rewrites | Wasted iterations on boilerplate | Issues caught early, cheap to fix |
| Git history | 1-3 giant commits | 50 trivial commits | Clean, meaningful commits |
| Iteration count | 1-2 (too few) | 20+ (too many) | 3-8 (right-sized) |
| Agent reliability | Agents struggle with huge tasks | Agents waste capacity on repetition | Agents work on focused, meaningful tasks |

---

## Anti-Pattern: Over-Granular Chaining

**Symptom:** `nextLogicalUnit` says "add operator X" → next iteration adds one operator → says "add operator Y" → repeat 15 times.

**Root cause:** Agent interprets "atomic" as "smallest possible diff" instead of "smallest logically complete change".

**Fix:** The batching rule in the implement prompt + the final-review `nextUnitOverride` field. If the reviewer sees over-granular chaining, it overrides with a batched instruction like "add ALL remaining operators in one step".

**Detection heuristic:** If 3+ consecutive iterations each produce structurally identical diffs (same pattern, different values), the unit size is too small. The final-review should batch the remaining instances.

---

## Sizing Guidelines

| Phase complexity | Implement steps per pass | Recommended MAX_PASSES |
|-----------------|--------------------------|----------------------|
| Simple (1 struct + tests) | 1 | 3 |
| Medium (module with 3-5 functions) | 2 | 5 |
| Complex (subsystem with multiple modules) | 2 | 8-10 |
| Repetitive (N similar items, same pattern) | 1-2 (batch ALL) | 3 |

**Repetitive work sizing:** If a phase involves N items following the same pattern (operators, test cases, similar contracts), size it as 1-2 implement steps that batch ALL items, not N steps with 1 item each. The agent should recognize templated work and do it all at once.
