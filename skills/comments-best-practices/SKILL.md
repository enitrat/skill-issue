---
name: comments-best-practices
description:
  Strict procedure for classifying every code comment and JSDoc/TSDoc block as delete, move, encode,
  rewrite or keep, based on where the comment sits (field, type, function, parameter, inline) and
  what that location is allowed to say. Use when writing new comments, reviewing comments in a PR or
  a file, or cleaning up commentary. Trigger for "should I comment this", "review these comments",
  "is this comment necessary", "clean up comments", "write jsdoc", "document this function".
---

# Comments

A comment is unenforced prose next to code that changes. Nothing keeps it true. The default verdict
for any comment is **delete**; a comment stays only when it passes every step below.

The failure this skill exists to stop is **context in the wrong place**: a true sentence attached to
a symbol it does not describe. A field doc that explains a mechanism, or a type doc that says what
some operation does to the value, is wrong even when every word is accurate. It goes stale the day
that other code changes, and nobody editing that code will find it.

## Procedure

Run this for every comment in scope, one comment at a time. Step 1 judges the whole comment. Steps
2 to 6 judge **each clause separately**: split the comment into clauses first, and for each clause
stop at the first step that gives a verdict.

```
1. Tool directive, `@internal`-style tag, license header or codegen banner? → LEAVE, do not edit
2. Restates the name, the type, the signature or the next line?             → DELETE the clause
3. History, design process, or a pointer to a doc or ticket?                → DELETE the clause
4. Is the subject of the clause THIS symbol?
   └── No → the clause is foreign: MOVE it to its home (table below)
5. Is the clause on the whitelist for this location?
   └── No → DELETE the clause
6. Does a name, a type or `readonly` already state it to the caller?
   └── Yes → DELETE the clause. If a rename or a narrower type would state it, make that
             change and DELETE the clause
7. Clauses are left → REWRITE the comment from them, within the length cap.
   No clause is left → DELETE the comment. Never invent replacement text.
```

A clause **restates** when removing it leaves a reader of the declaration knowing exactly as much:
`/** The batch id. */` on `batchId`, `/** Options for send. */` on `SendOptions`.

Step 4 is the one agents skip. Do it literally: write the clauses out and name the subject of each.
The subject is the head noun the clause is about, so "the batch each leg landed in" is about the
batch and is not foreign.

Step 6 counts only what the caller sees in the declaration. A runtime assertion or a test does not
state anything to a caller, so a valid range still belongs in the field doc.

## Whitelist by location

A clause not listed for its location does not belong there, however useful it is.

### Field or property

Allowed, as a noun phrase about the value:

- what the value means, when the name does not say it
- its unit (`in wei`, `in chain seconds`)
- its valid values or range
- its default (`@defaultValue`)
- what `null`, `undefined` or empty means
- its relation to a sibling field of the same type
- for a callback: when it is called and with what

A value defined by an event is still described as a value. Write "the time after which the batch
can no longer settle", never "finalizing after this cancels the batch".

Never:

- what any function does with, to or after the value
- why the value exists or why it has a constraint
- an instruction to the caller ("send these first", "store this")
- who produces or consumes it

**A field whose name and type say it gets no comment.** Cap: one sentence.

Why: a field is data. Its behaviour lives in the operations that touch it, and each of those has its
own doc. A reader hovering a field wants to know what it holds, nothing else.

### Type, interface, class or constant

Allowed: what one instance represents. One sentence. For a union of literals, one line per member
saying what that member means.

Never:

- "What `x()` returns", "What `x()` takes", "Options for `x()`". The signature of `x` already says so,
  and the comment breaks when `x` is renamed.
- which operations create, change or consume it
- lifecycle narration that belongs to those operations

Why: the same type is reached from many call sites. A doc phrased around one of them is wrong at the
others.

### Function or method (the doc comment)

Allowed:

- a verb-phrase summary: what it returns, or what it does that the caller can observe
- preconditions the caller must meet
- `@throws`, one per error type, each with the condition that raises it
- `@param` / `@returns` only when they add meaning beyond the name and type; never a type
- `@example`, when the signature alone does not show how to call it: a generic that infers from its
  argument, an overload set, a builder. Each example must run on its own

Never:

- how it works: the algorithm, the order of internal calls, what it caches
- why it was designed this way
- what another function does, or what the caller usually does next
- a second copy of the doc on an overload or an override; document the first, and on the others say
  only what differs

Cap: one summary sentence, plus at most two sentences of contract.

Why: the doc comment is the caller's contract. A caller must be able to call the function correctly
without reading its body, and needs nothing about the body.

### Inline `//` comment

Allowed: one hazard a maintainer would trigger by "simplifying" the line below it. An external
constraint (an API quirk, a spec bug, an ordering requirement), a security or privacy reason, a
performance trap.

Never: what the code does, a section label, a summary of the block.

Cap: one line, directly above the line it protects. If it needs a second line, the code is unclear:
extract a named function or variable and delete the comment.

Why: "what" is the code's job and rots first. "Why not the obvious way" is the only thing the code
cannot say.

### File or module header

None, apart from a license header.

## Where a foreign clause goes

| The clause says                                      | Its home                                           |
| ---------------------------------------------------- | -------------------------------------------------- |
| what operation X does to this value                  | the doc of X                                       |
| when an error is raised                              | `@throws` on the function that raises it           |
| a rule the value always obeys                        | a type, `readonly`, an assertion, or a test        |
| why the code is written this way, for a maintainer   | one `//` line above the code                       |
| why the design is this way, alternatives, trade-offs | the PR or a design doc. Not the code               |
| how to use this in a flow, what to do next           | the guide. Not the code                            |
| a mechanism the caller cannot observe                | nowhere. Delete it                                 |

If the home already says it, delete the clause. If the home's own whitelist forbids the clause, the
clause has no home in code: delete it.

**A clause the caller needs to avoid a bug is never deleted before its home holds it.** A
precondition, a privacy or safety hazard, an ordering requirement: write it into the function doc
first, as a precondition, then remove it from the field or type. If that function is outside the
files you may edit, leave the clause where it is and report it.

## Tells

Each of these in a field or type doc means a foreign clause is present. Find the clause and run
step 4 on it.

- a causal word: `because`, `so`, `so that`, `since`, `which means`, `in order to`, or a colon
  followed by a reason
- a verb whose subject is not the symbol: "a claim leaves…", "the router pulls…", "the SDK reads…"
- the name of another function, type, file or test
- a time word: `after`, `once`, `until`, `when the caller`, `later`
- `we`, `deliberately`, `previously`, `for now`, `note that`, `always`, `never`

## Worked examples

| Before                                                                                                             | Verdict                                                                                             | After                                                                |
| ------------------------------------------------------------------------------------------------------------------ | --------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------- |
| `/** The batch. */` on `batchId: bigint`                                                                           | Step 2: restates the name                                                                           | _(no comment)_                                                       |
| `/** The account that must send the calls: their encryption proofs are bound to it. */` on `account`               | Step 4: the clause after the colon is a mechanism. Step 2: the rest restates the name               | _(no comment)_                                                       |
| `/** The account's encrypted deposit, or null when the read named no account. A claim or quit leaves a zero. */`   | Step 4: second sentence is about `claim` and `quit`. Move it to their docs                          | `/** The account's encrypted deposit, or null when no account was given. */` |
| `/** What deposit and redeem return. */` on `JoinOutcome`                                                          | Step 4: the only clause is about `deposit` and `redeem`. Nothing is left                             | _(no comment)_                                                       |
| `/** Options for prepareDeposit. */` on `JoinOptions`                                                              | Step 2: restates a signature                                                                        | _(no comment)_                                                       |
| A method doc: "Reads the state, then the request id, then decrypts publicly and encodes the callback."             | Whitelist: that is the algorithm                                                                    | `/** Builds the call that settles a dispatched batch. */`            |
| `// loop over the legs` above a `for`                                                                              | Step 2                                                                                              | _(no comment)_                                                       |
| `// Every leg's token is decrypted together: a lone decrypt would tell the relayer which vault was picked.`        | Inline, one hazard, cannot be encoded                                                               | keep as is                                                           |
| A 4-line `//` block explaining a caching scheme                                                                    | Over the cap: the code is unclear                                                                   | extract `readFixedOnce(…)`, delete the comment                       |

## JSDoc mechanics

- Never write a type in a tag. `@param value the value to clamp`, never `@param {number} value`.
  Why: the compiler enforces the signature and nothing enforces the tag.
- Never restate a keyword the language enforces: no `@private` on a `private` member, no `@readonly`
  on `readonly`.
- `/** */` is for the caller. `//` is for the maintainer. Never put maintainer notes in `/** */`:
  they ship in the published types and the IDE hover.
- When the project requires a doc on every exported symbol, write the shortest sentence that passes
  the whitelist. Never pad it to look complete.

## Never touch

`eslint-disable`, `oxlint-disable`, `biome-ignore`, `prettier-ignore`, `@ts-expect-error`,
`@ts-ignore`, `@ts-check`, `"use client"`, `"use server"`, codegen banners, license headers.

## Writing new code

Write the code with no comments. Then add a comment only where step 7 of the procedure would be
reached. A comment written before the code is finished describes code that no longer exists.

## Reviewing

Classify every comment in scope; none passes by default. The review is done when each one has a
verdict and the file matches it. Report the counts (deleted, moved, encoded, rewritten, kept) and
list every clause that was moved, with its new home, so the reviewer can check nothing was lost.
