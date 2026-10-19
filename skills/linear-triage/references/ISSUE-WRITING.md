# Writing issues

The reader is a teammate from another seat (engineer, designer, product) who was not
in the conversation. The issue gives them a model of the problem and the system it
lives in, then hands them the work. **They own the solution.** The issue points;
it does not prescribe.

**Only what matters is written.** A line earns its place when the reader would get
the problem wrong without it. When unsure, cut. Expect to cut half the first draft.

## Pick the shape

| Shape | When | Sections |
| --- | --- | --- |
| **Task** | We know what to do | What · Why · How |
| **Open question** | We found something and the fix is a decision | Question · What we found · Options |
| **Bug** | Observed behaviour differs from expected | What happens · Expected · How to reproduce |

An open question never gets a task's shape. Picking a fix for it is the decision
the issue exists to ask for.

## Sections

- **What**: the change in product terms, one short paragraph or a few bullets.
  What the user, operator or caller can do afterwards.
- **Why**: the problem, grounded in the concrete case (who reported it, what they
  saw). Then **explain the system** so the reader understands it in one read: the
  terms they need, defined once; what happens when (a short timeline); what can
  and cannot be seen. A table or a `text` diagram when it shows the mechanism
  better than prose. One real example link beats a paragraph.
- **How**: open with "Guidance only. <seat> owns the final shape." Then 2–5
  pointers: existing code or prior art to start from, a link, a constraint that
  would make a reasonable approach wrong. Open points stay listed as open.
- **Question**: one sentence ending in `?`.
- **What we found**: the evidence, with links (tx, PR, dashboard, thread).
- **Options**: numbered, each one line with its cost. The last is
  "Something else?". Say who decides.

## Cut

- Implementation detail the owner will work out: file-by-file plans, state
  machines, edge-case lists, API sketches, step-by-step setup.
- Facts the reader cannot check: internal third-party state, numbers nobody can
  reproduce.
- Out-of-scope trivia, asks to other teams, history of how we got here.
- Done-when checklists, constraint lists, estimates in the body, "Summary" or
  "Next steps" sections, "As a user…".
- "X, not Y" framing. Say what the thing is.

## Process

1. Read the conversation for the incident, the reasons and the open questions.
2. Draft to the shape. Check every claim against a source; cut what you can't link.
3. **Prune**: for each line, would the reader get the problem wrong without it?
   If not, delete. Then halve the How.
4. Tighten with `/pstack:technical-writing`, then `/unslop`.
5. Present the body with title, project, assignee and labels. Create on approval.

## Examples

Open question:

````markdown
**Question.** Bundled grouped deposits revert with `HCUTransactionDepthLimitExceeded`
once a group has 5+ vaults. How should grouped deposits work?

## What we found
Each bundle leg rewrites the user's balance handle, so HCU depth stacks ~1.15M per
leg. The router touches the balance once; its legs stack ~217k each.

```text
bundle:  bal ─[leg1 1.15M]─ bal ─[leg2]─ … ─[leg5]   → ~5.13M > 5M cap
router:  bal ─ router ─[217k]─ … ─[217k]              → ~2.04M
```

Live Sepolia: [bundle tx](https://sepolia.etherscan.io/tx/0x6b15…) passed only because
every batch was empty; [router tx](https://eth-sepolia.blockscout.com/tx/0x3448…) passes.

## Options
1. Cap groups at 4 vaults.
2. Send every grouped deposit through the router.
3. Something else?

Mathieu decides.
````

Task (trimmed from SUP-646):

````markdown
## What
Add a "See your rewards on Merkl" action everywhere the app shows rewards. For a
confidential campaign it opens the campaign's Merkl rewards page; for a public one,
the incentives explainer, with a note that public rewards pay out after the end.

## Why
Flowdesk lenders report they can't see their rewards on Merkl. That's expected for
their campaign, and nothing in the app says so.

| | Public campaign | Confidential campaign |
| --- | --- | --- |
| Targets | The public vault share | The cShare |
| Visible on Merkl | Nothing for the holder | Accrued rewards, live |
| Paid | After it ends, via a retroactive confidential campaign | On claim, from Oct 12 |

Example: [this rewards page](https://app.merkl.xyz/campaign-rewards?campaignId=0x11d1…)
shows a confidential campaign's accrued rewards.

## How
Guidance only. UX and product own the final shape.
- Reuse one action in position, dashboard and the APY sparkle.
- Open: the retroactive campaign gets a new ID. How does the app learn it?
````
