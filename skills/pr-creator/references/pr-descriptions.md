# Writing Good PR Descriptions

PR descriptions are permanent records documenting what changed and why. Write them for future developers who need to understand code evolution.

## Structure

### First Line (Title)

- Concise summary of the specific modification
- Imperative mood: "Add feature" not "Adding feature" or "Added feature"
- Stands alone when viewed in PR lists or git log
- Followed by blank line
- Respect conventional commit message format (e.g., "feat(api): add caching to API responses")

**Good**: "feat(api): remove size limit on RPC server message freelist"
**Bad**: "fix(api): fix bug", "updates", "wip"

### Body

Expand on the summary with:

- **Context**: What problem exists? What's the current state?
- **Rationale**: Why this approach? What alternatives were considered?
- **Details**: Implementation specifics reviewers need to know
- **Limitations**: Known compromises or future work
- **References**: Bug numbers, design docs, benchmarks

## Examples

### Feature Addition

```markdown
feat(api): add response caching for GET endpoints

Servers with high read traffic benefit from caching repeated queries.
This adds a Redis-backed cache with configurable TTL for all GET
endpoints in the API layer.

Key changes:
- Add Redis client configuration in config/cache.ts
- Create caching middleware with TTL support
- Apply to /users, /products, /orders endpoints

Cache invalidation happens on relevant mutations via pub/sub.
Metrics available at /metrics/cache for hit/miss rates.

Closes #42
```

### Refactoring

```markdown
refactor(api): extract TimeKeeper dependency from Task class

Construct Task with TimeKeeper to use its TimeStr and Now methods
directly. Add Now method to Task, eliminating the need for the
borglet() getter.

This advances the goal of decoupling the Borglet Hierarchy by
removing implicit dependencies and making time handling explicit.

No behavior changes - existing tests pass.
```

### Bug Fix

```markdown
fix(api): fix race condition in connection pool cleanup

The cleanup goroutine could access the pool map while a new connection
was being added, causing intermittent panics under load.

Root cause: Missing mutex lock in cleanupStaleConnections().

Fix: Acquire write lock before iterating pool entries.

Added regression test that reproduces the race with -race flag.

Fixes #156
```

### Small Change Needing Context

```markdown
chore(build): create Python3 build rule for status.py

Allows existing Python3 consumers to depend on the adjacent rule
rather than managing their own copy. This encourages Python3 adoption
across the codebase and simplifies automated build file refactoring.

Part of the broader py2->py3 migration tracked in #89.
```

## What to Avoid

- **"Fix bug"** - Which bug? What was wrong?
- **"Update code"** - What changed? Why?
- **"WIP"** - PRs should be complete units of work
- **"Misc changes"** - Be specific
- **Implementation-only descriptions** - Include the "why"

## Tags (Optional)

Use tags to categorize: `[perf]`, `[refactor]`, `[bugfix]`, `[feature]`

Keep tags brief in the title. Longer categorization can go in the body.

## Before Submitting

Review the description after addressing feedback - initial intent may have changed during review. Update the description to match the final state.
