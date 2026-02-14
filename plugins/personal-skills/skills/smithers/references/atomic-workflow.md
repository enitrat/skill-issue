# Atomic Unit Pipeline Pattern

The preferred workflow architecture: run the **full pipeline** (implement → test → review → fix → refactor → final-review) for each **small atomic unit of work**, not implement everything then review once.

---

## Core Principle

**Small changes, full validation.** Each Ralph iteration implements 1-2 atomic units (one struct, one function, one interface), then runs the entire quality pipeline. The final-review gate decides whether to loop for more units or move to the next phase.

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

## nextSmallestUnit Chaining

The key mechanism: each implement step outputs what to do next. The next iteration's implement step receives this as its instruction.

### Implement Schema

```ts
export const ImplementSchema = z.object({
  filesCreated: z.array(z.string()),
  filesModified: z.array(z.string()),
  commitMessage: z.string(),
  whatWasDone: z.string().describe("Detailed description of the atomic unit implemented"),
  nextSmallestUnit: z.string().describe("The next smallest atomic unit of work to implement"),
});
```

### Implement Prompt (MDX)

```mdx
# Implement — {props.phase} — Pass {props.pass}

RULES:
- Implement the SMALLEST ATOMIC UNIT of work possible — one struct, one function, one interface
- Do NOT batch multiple unrelated changes

{props.previousWork
  ? `Previous implementation did: ${props.previousWork.whatWasDone}\nNext smallest unit to implement: ${props.previousWork.nextSmallestUnit}`
  : "Start with the first item from the plan."}

{props.failingTests ? `FIX THESE FAILING TESTS FIRST:\n${props.failingTests}` : ""}
{props.reviewFixes ? `Review fixes just applied: ${props.reviewFixes}` : ""}

## GIT COMMIT RULES
- Make atomic commits — one logical change per commit
- Format: "EMOJI type(scope): description"
- git add the specific files changed, then git commit

## REQUIRED OUTPUT
{props.schema}
```

### Workflow Threading

```tsx
// implement-1 does unit A, outputs nextSmallestUnit: "implement iterator interface"
<Task id={`${id}:implement-1`} output={tables.implement} outputSchema={ImplementSchema} agent={codex}>
  {render(ImplementPrompt, {
    phase,
    previousWork: latestImplement1 ?? null,  // from previous Ralph pass
    failingTests: latestTest?.failingSummary ?? null,
    reviewFixes: latestReviewFix?.summary ?? null,
    implementPass: 1,
  })}
</Task>

// implement-2 picks up nextSmallestUnit from implement-1
<Task id={`${id}:implement-2`} output={tables.implement} outputSchema={ImplementSchema} agent={codex}>
  {render(ImplementPrompt, {
    phase,
    previousWork: latestImplement1 ?? null,  // chains from implement-1
    implementPass: 2,
  })}
</Task>
```

The chain crosses Ralph iterations too: pass N's implement-2 outputs `nextSmallestUnit` → pass N+1's implement-1 picks it up.

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

| Aspect | Big-Batch (anti-pattern) | Atomic Pipeline |
|--------|--------------------------|-----------------|
| Implement scope | Everything at once | 1-2 units per pass |
| Review quality | Reviewer overwhelmed by massive diff | Reviewer focuses on small change |
| Test feedback | Tests run once at the end | Tests run after each unit |
| Fix cost | Late-discovered issues require large rewrites | Issues caught early, cheap to fix |
| Git history | 1-3 giant commits | Many small atomic commits |
| Agent reliability | Agents struggle with large tasks | Agents excel at focused tasks |
| Resumability | Failed run loses all progress | Failed run keeps completed units |

---

## Sizing Guidelines

| Phase complexity | Implement steps per pass | Recommended MAX_PASSES |
|-----------------|--------------------------|----------------------|
| Simple (1 struct + tests) | 1 | 3 |
| Medium (module with 3-5 functions) | 2 | 5 |
| Complex (subsystem with multiple modules) | 2 | 8-10 |

For complex phases, prefer more passes with fewer units each over fewer passes with more units.
