---
name: change-description
description: Write or rewrite a PR body, changeset, or change summary for a reviewer who has not read the code. Use when opening a PR, when asked to write, rewrite, shorten or update a PR description, or when summarising a branch's changes.
---

# Change description

The reader is a reviewer or operator with a few minutes who has not read the code.
The description is a **briefing**: it gives them a model of the system as it now
stands, shows the decisions they are asked to accept, and lists what they must do to
merge and deploy safely.

**Only what matters is written.** Every line carries something the reader must know
or do. A section, step, risk or caveat with nothing important in it is left out
entirely, without a placeholder: a body with no deploy steps has no deploy section
and no sentence saying so. When unsure whether an item clears the bar, cut it.

## Scope

- Describe the whole diff against the branch the PR merges into. For a stacked PR
  that is the parent branch, not `main`.
- Describe the system as it is after the merge. On every update, rewrite the body
  from scratch from the current diff, and keep it no longer than before unless the
  scope grew. A patched body accretes; a rewritten one reads in one go.
- Rewrite the PR title with the body when the scope moved.

## Size by change

| Change | Form |
| --- | --- |
| Tiny (one fix, one rename) | 1–3 lines, no headings |
| Small (one behaviour) | Summary and What's new, a few lines each |
| Large or operational | The skeleton below, with only the sections that have content |

## Skeleton

1. **`Closes <TICKET>`** on the first line when a ticket exists. Ticket ids stay out
   of the prose.
2. **`## Summary`**: two short paragraphs. Open on the one idea the change is built
   on, named in bold and defined in a sentence. Then the problem it solves, grounded
   in the concrete case or incident. Blockers, and anything that breaks on merge, go
   in a `> [!IMPORTANT]` callout right after.
3. **`## What's new`**: bold-led bullets in product terms: what a user, operator or
   caller can now do or sees differently. New first, changed next, fixed last.
   Formulas and algorithms go in How it is built, if a reviewer needs them.

Each section below appears only when it has something important to say:

4. **`## How it is built now`**: when the change has a shape worth seeing. A
   `mermaid` diagram of the flow or layers, then the few ideas the design rests on
   as 2–5 numbered lines. A `diff` block when callers or open branches must apply
   renames.
5. **`## Decisions`**: at most three choices a reviewer is likely to question, each
   one line: the choice and the constraint that forced it. Name an alternative only
   when a reviewer would propose it. Mark a choice that blocks the merge **Open
   decision** and say what it waits on. Reviewers answer these.
6. **`## Before you merge and deploy`**: actions the merge itself requires (env,
   secrets, infra, migrations, on-chain, workflow inputs). Numbered imperative steps
   grouped by time: before the merge, right after the deploy, later. Each step gives
   its expected output. A `> [!WARNING]` only at a real point of no return. A
   rollout that runs later, by hand, belongs in a runbook: link it in one line.
7. **`## Risks`**: failures this diff can plausibly cause, as a table of risk and the
   symptom an operator would see.
8. **`## How it was tested`**: when testing tells the reviewer something the diff
   doesn't, such as a dry run against production data, or an important path that
   never ran.

## Writing

- **Short.** Most bodies land under 2k characters; a large operational one under 4k.
  Past that, the body is carrying something that belongs in the diff, a doc or a
  runbook.
- **Zoom out.** System, flows and decisions. Internals a reviewer can read in the
  diff stay in the diff.
- **Show, then tell.** A `mermaid` diagram, a before/after table or a real dry-run
  table carries a mechanism better than prose. Use as many as the mechanisms need.
- **Consequences, not mechanics.** "Merging before the apply makes `/api/fund` fail
  at boot on mainnet", not "ordering matters".
- **Durable facts.** CI status, counts that drift, commit history, the process that
  produced the change, and stack or review scaffolding stay out: GitHub shows them.
- **In scope.** Steps, risks and warnings concern what this PR does and the team
  controls. Asks to a third party and work for a later PR stay out unless they block
  the merge.
- **Outcome, not history.** Each decision states what was chosen. The designs tried
  and dropped on the way stay in the conversation.

## Process

1. Commit and push first, so the body describes the pushed head.
2. Read the diff against the base, and the conversation for the incidents, reasons
   and open questions behind each decision.
3. For a large diff, map it with two read-only Sonnet subagents in parallel: one for
   features and architecture, one for merge and deploy touchpoints (env, infra,
   workflows, on-chain, dependencies, revert safety). Both cite files.
4. **First pass: draft.** Get the content right, using `/show-me` for diagrams.
5. Check every claim against the diff; cut what you cannot point to.
6. **Prune** what is said. For every section, bullet, step, row and callout, ask: without it,
   would the reviewer approve something they shouldn't, or an operator break
   something? If not, delete it. Expect to cut a third of the draft. The items the
   author deleted by hand in past bodies:
   - steps that ask a third party for something
   - risks that are speculative, or that restate a step
   - a second `[!WARNING]`, or one that repeats a step
   - internal moves and small fixes (a helper relocated, an `.env.example` line)
   - sentences that say a section is empty or nothing is needed
   - stack and review scaffolding, commit SHAs

   A section left with one item becomes a sentence in the nearest section.
7. **Second pass: tighten** how it is said. Rewrite every sentence, applying
   `/pstack:technical-writing`:
   - One idea per sentence, in the words an engineer would say out loud.
   - Plain terms over jargon. A project term the reader needs is defined once in a
     clause; any other term becomes a plain description.
   - Direct statements. Drop throat-clearing, hedges, stacked clauses and
     ornamental phrasing ("note that", "in order to", "this ensures that").
   - A sentence that survives losing a word loses it. Recheck the length target.
8. Run `/unslop` on the result.
9. Publish with `gh pr edit --body-file` (or `gh pr create`) without asking. Report
   the corrections to the previous body, and any doc or comment in the diff that
   contradicts the code, to the user.

See [references/examples.md](references/examples.md) for a tiny, a small and an
operational body.
