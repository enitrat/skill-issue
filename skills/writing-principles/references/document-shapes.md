# Document shapes

Each common document type is the same principles under different reader conditions: who asked, how much they already hold, and what they must do after reading. The shapes below are what practitioners converged on for those conditions. Use them to check a draft, not to generate one: a document that fills every section of a shape can still have no thesis.

For each shape: the reader's state, the first lines' job, the usual order, and the trap specific to it.

## Status update or handover

- **Reader's state:** they asked, or the update is expected. They hold the question ("where are we?").
- **First lines:** the current state and what you need from them, with urgency. Not "I looked at...".
- **Order:** bottom line first; then situation, background, your assessment, your recommendation (SBAR, from hospital handovers). Evidence and detail last, for whoever keeps reading.
- **Trap:** skipping the recommendation. Handover formats exist because people describe the situation and stop before saying what should happen.

## Decision request

- **Reader's state:** they must choose, often between other demands, and may not yet know there is a choice.
- **First lines:** the recommendation and what you need from them, by when. Situation only as much as the ask needs to make sense.
- **Order:** situation, complication, the question, your answer; then the two to four reasons, grouped so they neither overlap nor leave a gap; then the alternatives and why they lose; then risks. Supporting data in an appendix.
- **Trap:** presenting options without a recommendation, or options that do not visibly differ on anything the reader cares about.

## Design or API proposal

- **Reader's state:** peers who did not ask for the change, will have to live with it, and are entitled to be skeptical.
- **First lines:** what is proposed, in one sentence, then the problem it solves. A short example of the proposal in use comes within the first screen.
- **Order:** the problem, stated so it would survive the proposal being rejected; who has it, and what about their situation creates it; the current shape, complete enough that the problems can point at it; the proposal taught through use, as if it already existed; the reasoning: for each load-bearing decision, the problem it answers, the alternative considered, and why it loses; then the precise specification, returning to the same examples; drawbacks ("why should we not do this?"); how it rolls out; open questions.
- **Trap:** the reasoning section reduced to a list of entry points. The reader can then see what the design is but not why, and the one part they needed to judge is missing.

## Explainer or teaching document

- **Reader's state:** they want to understand something and have chosen to spend time on it; they hold curiosity, not a question.
- **First lines:** what the reader will be able to see or do at the end, and why that is worth it, in concrete terms. Start from a case they can picture, not a definition.
- **Order:** the simplest observable case; add one variable at a time, each with its own example or demo; announce detours before taking them; combine the pieces at the end.
- **Trap:** front-loading vocabulary. Terms defined before the reader has a reason to need them do not stick.

## Strategy narrative

- **Reader's state:** they need to align on a direction and will judge the reasoning, not only the conclusion.
- **First lines:** the diagnosis and the central choice: "the problem is X, so we will do Y".
- **Order:** diagnosis of the situation (what is actually going on, and why); the guiding policy that follows from it; the coherent actions that carry it out. Written as narrative, with causal links, rather than as bullets.
- **Trap:** a vague diagnosis. Strategies fail most often because the problem was never stated precisely.

## Postmortem

- **Reader's state:** affected people and their managers. They want to know what happened, whether it is understood, and whether it will recur.
- **First lines:** what happened, for how long, who was affected, and whether the cause is understood, in one paragraph, without blame.
- **Order:** impact; timeline with times; root cause deep enough to explain the trigger and why the defences did not stop it; what was done; what will change, with owners.
- **Trap:** a timeline without a cause, or a cause that stops at the trigger.

## Change description (pull request)

- **Reader's state:** a reviewer deciding how closely to look.
- **First lines:** who did what, and whether a human has already reviewed it.
- **Order:** the problem in a paragraph; evidence matched to the kind of change (the same view before and after; the same input on both sides; the same workload measured; real output; the code a user would write); details; what was not checked; two or three plain sentences an outsider could follow.
- **Trap:** a description longer than the diff it describes, made of claims instead of evidence.

## Final report from an agent

- **Reader's state:** someone who did not watch the work happen and is switching in from something else.
- **First lines:** the outcome, in terms a reader who saw none of the work can use.
- **Order:** key points first; self-contained; ends with what was found, what was done, and what is next.
- **Trap:** narrating the process in the order it happened instead of reporting the result.
