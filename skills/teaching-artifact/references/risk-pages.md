# Risk and alternatives pages

Read this when the spine tree sends you here: the reader must choose between alternatives, or must know the risks of something we depend on (a protocol, a vendor, a version).

## Spines

```
Risks of one thing
  → Context · Short answer + risk strip · How it works · Fit with our flows · Risks · Open decisions · Reference
Choosing between alternatives
  → Context · Short answer + risk strip · Shared base (once) · One section per alternative · Side by side · Shared risks · Open decisions · Reference
```

## Alternatives

- Each alternative's section has the same blocks in the same order (intro, how it works, outcomes, risks), because the reader compares by position. Same order, not same counts: never add a filler card to match.
- Alternatives must differ on an axis the reader can decide on. Before building, write the side-by-side table's rows; if two options get the same value on every row, merge them or cut one. Why: options that look alike leave the reader with nothing to decide.
- Keep at most 3 alternatives on the page. Cut the rest in the outline's cut list.
- A risk every alternative carries goes once, in the shared risks, with one severity chip per alternative ("A: Med · B: High").
- In the side-by-side table, mark the riskier cell, not the "winner".

## Short answer + risk strip

- A dark block: a verdict headline with one highlighted phrase, at most two sentences, then at most 5 risk chips.
- Each chip shows its severity and links to its card. Order by severity, then harm to users' money, then availability. Five is the ceiling: past it the first chips stop looking more urgent than the rest.

## Outcome matrices

- States of the external system as rows, our flows as columns.
- Cells are verb phrases naming what the user gets ("Settles", "Refunds deposit at deadline", "Stuck until unpaused"), never adjectives or model rule names. Cells sit on ok/warn/bad tints with a key.
- Below 600 px the matrix reflows into stacked rows (kit `.matrix`).

## Risk cards

- Anatomy, in order: calm specific title ("Withdrawals thin at high utilization", not "Bank run"), severity chip, optional gauge with its date, one or two sentences on what we lose, one `→` mitigation line.
- Each card states one concrete failure scenario: the inputs or state, and what the user sees. A risk the reader cannot picture is theory; show how it is triggered.
- One severity scale across alternatives. Severity matches what the team plans to do: a risk that bites only under a choice the team is not making is Low; if the product call is open, mark the rating conditional on it.
- A mitigation is an action our system can take. Trace it through the flow, checking what the system can see at that moment; a check on a value it does not know yet is not a mitigation. Messaging users is a product call and goes to Open decisions.

## Safety and scope

- Say what stays safe once, where the reader's first fear lives (principal, earnings, user data), scoped to the states it holds in.
- Something the product chose not to do is not a risk. One sentence where relevant; never a chip, card or row.
