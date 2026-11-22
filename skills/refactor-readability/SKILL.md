---
name: refactor-readability
description: Refactor agent-written code so a human can read it. Names things from the domain, organizes files by the noun they own, deletes before it moves, reuses before it adds, and locks behavior with tests first. Use when a codebase or module feels bloated, duplicated, over-typed, badly named or hard to follow, after a burst of agent work, before a rewrite, or when the user says "make this readable", "simplify", "clean up agent code", "fix the naming", "refactor for readability".
---

# Refactor for readability

Agent code fails the same ways: it adds code instead of using what exists, invents names, adds types and wrappers nobody asked for, and grows until nobody follows it. Fix it in the order below. Behavior never changes.

## Hard rules

- Behavior never changes. A fix is a second change: note the bug, refactor around it.
- Touch only the target. Every changed line must trace to the request, or the diff cannot be reviewed.
- Delete before you move. A helper, context or wrapper hides complexity; it does not remove it.
- Rename and reorganize before anything breaks: while there are no consumers, a rename is one commit. Afterwards it is a migration.

## Names

A reader who never saw the glossary must guess what a name means. If they cannot, rename.

1. **Function = verb + noun.** `parseInvoice`, `loadUser`, `chargeCard`. Never a bare `run`, `handle`, `process`, `send`, `get`. Why: at a call site the bare word names nothing, and a name that hides a cost (a network call, a prompt, a write) must warn about it: `fetchPrices`, not `prices`.
2. **Type and field = the domain's own noun.** `customerId`, not `member`; `kind`, not `verb`; `order`, not `row`. Never a grammar word, a storage word, or the parent's name inside a field (`order.orderStatus`).
3. **A generic noun carries what it belongs to.** `ShippingRates`, `UserSettings`, `PaymentEvent`, never `Rates`, `Settings`, `Event`, `data`, `info`, `config`, `item`, `group`. Test: if the name fits three unrelated things in the repo, it names none of them. Why: a bare noun is true of everything, so it explains nothing.
4. **A plain word beats a word we invented.** Use `retry`, not `reconcile`; `queue`, not `pipeline`, when it is one; `daily`, not `d1` or `tier2`. Test: would a new hire guess it without the glossary? Invent a term only when no plain word is correct, then define it. Jargon from another field (trading, ML, ops) counts as invented.
5. **One concept, one word.** When two compete, pick one and put the loser on an avoid-list in `CONTEXT.md`. When one word means two things, split it.
6. **Name what it is, never when it arrived.** No `legacy`, `current`, `new`, `main`, `V2`, `-r1` in anything a reader sees. No `Manager`, `Handler`, `Helper`, `Utils`, `Enhanced`.
7. **Mirror the outside world.** A field the database, external API, spec or existing library already names keeps that name (`stripeCustomerId`, not `payerId`). Do not coin a third word for the same thing.
8. **Name the scope that varies.** An environment, region or tenant is always in the name (`orders-prod`, `queue-eu`), never an unnamed default that silently means one of them.
9. **Do not repeat the container.** `billing.invoices`, not `billing.billing_invoices`; `user.email`, not `user.userEmail`.

Before renaming more than a handful of names, write the vocabulary table (concept, name, replaces, avoid) into `CONTEXT.md`. Names are binding once it lands. Show the user the table before you apply it.

If a concept is hard to name, or the user says they do not understand it (a vague `meta`, `handler` or `manager`), the design is wrong, not the label. Delete or merge the concept.

## Organization

- **One file, one job, named for the noun it owns.** `invoice-totals.ts`, `retry-policy.ts`. A file doing three unrelated jobs is split by job. Why: a reader finds code by name and should never open a file to learn what it is.
- **Order inside a file:** exports first, most important first; helpers follow in the order they are first used; types used only here sit just above their first use.
- **Deep modules.** A small interface over real behavior. A pass-through layer (a function whose body is one call, a per-method options file, a barrel that re-exports) fails the deletion test: delete it and see whether complexity reappears at callers. If it does not, it stays deleted.
- **Cap the reader's path.** A flow is followable in three files. Beyond that, merge.
- **Few, concrete types.** No generic parameter, alias family or factory to make a signature flexible. Type a shared setting once (a `Register` augmentation) instead of at every use. Delete a type that restates another; derive it.
- **No implicit state machines.** A set of booleans that must agree is a status field in disguise. Make the status explicit.
- **A convention may be broken only with its why written down** at the break. Break it where the convention's machinery has no real use.
- **Docs and explanations go wide, then narrow.** Summary first, detail below. A wall of text is a structure problem; fix the structure, not the prose.

## Process

### 1. Scope

One target: a module, a page, a feature. If none is given, run step 2 over the repo and propose one. Never "the whole codebase" in one pass.

### 2. Analyze (read-only)

Ranked report: file, problem, action from step 3. Look for:

- Files over 1,000 lines; pages or components over 500.
- Functions with 10+ decision paths, or a CRAP score of 10+ when a tool exists.
- Duplicate blocks 80% similar or more.
- New code that reimplements something already in the repo. Search for the existing abstraction before judging any new helper. This is the most common agent mistake.
- Thin wrappers, one-use helpers, pass-through layers.
- Names failing the Names rules, listed as a before/after table.
- Files failing the Organization rules.
- `any`, `Record<string, unknown>`, casts that hide a mismatch, types that restate types.
- Comments that narrate code, explain a workaround or are stale.
- Tests and fixtures that assert nothing other tests or types do not.
- Features with the most complexity for the least use. List them and stop; deleting a feature is the user's call.

Stop at the report if the user asked for analysis only.

### 3. Decide per finding

Take the first branch that applies.

```
Unused or never executed?                      → DELETE
An existing abstraction already does this?     → REPLACE with it, delete the copy
Thin wrapper, one-use helper, pass-through?    → INLINE
One unit with several jobs, or 10+ branches?   → SPLIT by job, name each for its job
Name, order or comment problem only?           → RENAME / REORDER, touch nothing else
```

Answer no finding with a new abstraction (context, provider, base class, config object, generic) unless a second real caller exists today. Why: agents add these to cut line count and they hide data flow. A smaller diff that is harder to follow is a regression.

### 4. Apply

- Delete comments that narrate or explain a workaround; refactor so the workaround disappears or delete both. Keep a comment only for what code cannot show (a browser quirk, an external constraint).
- Replace `any` and `Record<string, unknown>` with the real shape, or `unknown` narrowed at the boundary. If readability and exact typing conflict, readability wins unless the type prevents a real class of bug.
- Push state down and pass less; no context to avoid prop drilling. Remove effects, flags, fallbacks, defensive branches and compat shims for uncommitted code that nothing needs.
- Do not shrink functions for their own sake. Ten two-line functions read in order are worse than one clear forty-line function.

### 5. Loop in small steps

- One finding or tight group per step, from the top of the report.
- After each step run characterization tests, type check and lint. On failure, revert that step.
- Re-run the complexity and duplication check on touched files. If the numbers did not drop, the step moved complexity: revert it.
- A rename step is complete only when `rg` finds no old name in code, docs, config and tests.
- Stop when nothing is left above the thresholds or the next step needs a behavior change.

### 6. Report

Files changed, lines added and removed, before/after complexity, the rename table, what was deleted, bugs left alone, features proposed for deletion, and any decision needed from the user.
