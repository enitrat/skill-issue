---
name: own-it
description: Review or redesign code as its owner, from the product need and first principles, hunting accidental complexity and compensating code. Use for /own-it, "this codebase is yours", architecture reviews, model or API-shape reviews, pre-merge design passes, cleanup after a big refactor, or whenever asked to find compensating code or propose redesigns from first principles. Combines with poteto-mode, thermos, emil-prep-for-prod and similar review skills.
---

# Own it

The argument names the scope: a PR, a branch, a package, a feature or a whole
repo. Anything after it is extra context or a deliverable; follow it.

## Stance

This codebase is yours: what it's for and how it's built are your call, and you'll
keep building on it. What exists now is a rough indicator of what must be built, not
a constraint. Challenge its shape when the product need says so.

Don't assume code answers a real need because it exists. Take a Cartesian approach:
doubt each piece until the product need justifies it.

## Method

1. **Product need first.** Find out what the scope is for: the product and business
   requirements, the users, the external systems it talks to. Read the Linear issue,
   PR body, specs and docs the scope references before reading the code. State the
   need in a few plain sentences.
2. **Read Parnas.** Read [references/parnas-1972.md](references/parnas-1972.md).
   Decompose by the design decisions most likely to change, not by processing steps.
   Each module hides one decision.
3. **Split the complexity.** Essential complexity is what the product need demands.
   Accidental complexity is what our design choices created. Name each piece as one
   or the other.
4. **Find compensating code**: code that exists to patch an earlier bad design
   (adapters between our own formats, guards against states the model should make
   impossible, duplicated or near-duplicated types, conversions, flags that
   special-case a leaky abstraction, docs explaining a workaround). For each piece,
   propose the redesign under which it would never have been written.
5. **Shrink the model.** Reduce the number of types, concepts and notions. Align on
   one strong core type model and remove conversions between formats.

## Rules

- No compensating code survives. A full rewrite is fine if it removes it.
- Justify every departure from the current approach, and every place you keep it.
- Don't add defensive programming or guards to cover a weak model; fix the model.
- Keep public API changes deliberate: list each one and the reason.
- Use plain words. Name things after the product domain, not the implementation.

## Report

Lead with a short summary in plain words, then:

- **Modules**: each module and the decision it hides.
- **Compensating code**: each piece, where it is, and the redesign that removes it.
- **Delete**: what goes away.
- **Public API changes**, if any, with the reason for each.

When the user asked for changes, not a report, apply the redesign and give the same
sections as the summary of what changed.
