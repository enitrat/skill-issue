---
name: writing-principles
description: First principles for writing a document another person reads to understand something or decide something — reports, proposals, design and API docs, RFCs, status updates, postmortems, explainers, PR descriptions, memos, and the prose inside HTML artifacts. It covers having a thesis, posing the reader's question before answering it, ordering information so understanding builds, spending words where the reasoning is, and earning the reader's trust. Use it whenever you write or restructure anything longer than a few paragraphs for someone else, review such a document, or turn research into a write-up, even if the user only says "write this up", "make an artifact", "draft the proposal" or "summarise for the team".
---

# Writing principles

A document moves understanding from a head that has it to a head that does not, through a channel the reader controls: their attention. They can stop at any line. Everything below follows from three facts about that reader:

- **They read to answer a question they hold.** A sentence that answers no question they hold is noise, however true.
- **They have none of your context.** They are intelligent, but they have not seen your files, your conversations or your reasoning, and they may be switching in from other work.
- **Their attention is spent, not given.** Each paragraph must pay for the attention it costs by moving them closer to the point.

These are principles, not steps. A document that follows a template can still fail all three; a document that serves all three rarely needs one. When a principle and a habit conflict, the principle wins; when two principles conflict, ask which serves this reader at this point in the document.

## 1. Know what you think before you arrange it

Most unclear writing is unclear thinking that has been formatted. Before structure, before headings, write the point in two or three plain sentences a newcomer would follow. If you cannot, the thinking is not finished, and no layout will hide it.

- **The thesis.** A document worth reading defends a position: "the vault logic should move into the SDK, because every host rebuilds it and gets it wrong". A subject ("vault API redesign") is a category, not a point. The thesis is the thread every section pulls on; a section that does not advance it, or prepare the reader for it, belongs in another document.
- **Interrogate it.** Ask "why does this matter?", then "is that really why?", until the honest answer appears. The first answer is usually the writer's reason; the reader's reason is underneath it.
- **Draft to discover, then restructure to deliver.** You think in the order you found things out. The reader needs them in the order that builds understanding. Those are different orders, and the second draft exists to convert one into the other.

## 2. Pose the question before you answer it

An answer lands only on a question the reader already holds. Give a conclusion before the reader knows what problem it solves and it reads as an assertion with no reason to believe it.

The opening's job is to make the reader hold the question, in as few lines as their context allows:

- **Situation:** what the reader already knows and agrees with. It anchors them on familiar ground.
- **Complication:** what changed, what is broken, or what is at stake. This is the hook: the tension that makes the situation untenable.
- **Question:** the one the complication raises. It can stay implicit when it is obvious.
- **Answer:** your thesis.

How much of this you need depends on the reader:

- **They asked the question themselves** (an executive who requested the recommendation, a reviewer waiting on a status): lead with the answer. Situation and complication shrink to a clause.
- **They did not ask, or they are skeptical** (a proposal to another team, a design that changes their code): build the situation and complication first. A skeptical reader who meets the answer first stops reading.

Either way, the first screen answers "why am I reading this?" before it answers anything else.

## 3. Make each part answer the question the previous part raised

A reader keeps reading while every section resolves a question they now hold and raises the next one. That chain is the "fil conducteur". When it breaks, the reader feels lost even if each section is clear on its own.

- **Vertical logic.** Every claim raises "why?", "how?" or "so what?". The material directly after it answers that. If you cannot name the question a section answers, it is in the wrong place, or it should not exist.
- **Set up, then pay off.** Anything a later section relies on is established earlier, at the depth that section needs. A "before" shown in fragments cannot support an "after" argued in full. Equally, nothing is set up that is never used.
- **Headings carry claims, and read alone they tell the story.** "Five failures in today's hosts" is a label; "Each host rebuilds the join lifecycle, and gets cancel wrong" is a claim. Read only the headings in sequence: if the argument does not hold, the structure is wrong, whatever the prose says.
- **Causal links carry the reasoning.** "Because", "so", "but", "which means" make the reader's next step predictable. Bullets drop them: a list of facts shows effects without causes. Use prose wherever ideas depend on each other, and lists only for items that are truly parallel.

## 4. Order information so understanding builds

At every scale, from sentence to document, the reader must be able to attach each new piece to something they already hold.

- **Known before new.** Begin a sentence with what the reader has and end it on what is new: the end of a sentence is where emphasis falls. The same holds for paragraphs and sections. Never use a term in line one that only makes sense at line twelve.
- **Concrete, then the pattern, then the concrete case that the pattern explains.** A general claim with no instance is hard to believe; an instance with no generalisation teaches nothing transferable. Move down and up this ladder deliberately.
- **Use before specification.** Show what using the thing looks like, as if it already existed, before its precise grammar, edge cases and invariants. Then return to the same examples when you specify.
- **Problem before solution, stated so it would survive the solution being rejected.** If the motivation only makes sense given your design, it is a justification, not a problem.
- **Diagnosis before prescription, with causes, not only symptoms.** "Cancel can reveal the chosen vault" is a symptom. Who causes it — the library, its caller, or both — decides where the fix belongs, so say it.
- **Introduce the actors before their needs.** A requirement makes sense only once the reader knows who has it and what about their situation creates it.

## 5. Spend words where the reasoning is

Length is not the enemy; unearned length is. A uniform density rule ("three sentences per section") starves exactly the part that carries the argument and pads the parts that should be a single line.

- **The core gets the most words.** The section that answers "why this, and not something else?" carries the thesis; it holds the reasoning chain, the alternatives considered, and why they lose. Compressing it into a list of names is the most common way a proposal fails.
- **Reference material gets the fewest.** Lists of entry points, addresses, flags and versions are looked up, not read. Keep them compact and out of the reading path.
- **Each kind of content serves a different need.** Explaining why, teaching how to use, giving steps to follow, and describing precisely for lookup are different jobs for different moments. Mixing them in one passage fails all of them. Keep each passage one kind, and let the document's order follow the reader's path through them.
- **Cut what does not teach.** Every sentence, label, badge and pill either moves the reader toward the point or costs attention for nothing. Metadata, provenance tags and decorative labels are not content. Omit needless words, but never the word that carries a cause.
- **Pictures for structure and change, prose for reasoning.** A diagram earns its place when it shows how parts connect or what changes between two states. Text placed inside boxes is still text. A table earns its place for facts the reader compares along the same axes.

## 6. Earn trust

A reader who does not trust a claim discards the reasoning built on it. Trust comes from what the reader can check.

- **Evidence over assertion, and the comparison is the evidence.** "Compared to what?" Show the same task before and after, the same input on both sides, the same unit. A specific number beats "most"; a real excerpt beats a description of it.
- **Show the alternatives you rejected and why, at each load-bearing decision.** A choice presented as settled invites the reader to argue with it; a choice shown against its alternatives invites them to check your reasoning.
- **Say what you did not establish.** Mark assumptions as assumptions, especially requirements. An invented requirement, once spotted, discounts everything else on the page.
- **Claim exactly what is true.** "Serializable", not "JSON", when that is what you mean. Overclaiming is cheap to write and expensive to be caught at.
- **State the bad news where the reader will see it.** The finding that matters most goes in the title and the opening, even when it is uncomfortable. A reassuring headline over a buried warning is how readers miss the one thing they needed.

## 7. Write for someone who is not you

The more you know, the harder it is to remember what it was like not to know it. Every unclear passage you write will look clear to you.

- **Name things by what the reader recognises.** Use the term their field already uses, not one you coined while working. Define each term the reader may not know where it first appears, in a few words, or remove it.
- **Plain words, active voice, the actor as subject and the action as verb.** "The SDK reads the batch from the chain", not "batch state retrieval is performed on-chain".
- **Concise is not elliptical.** Cut words the reader does not need, never steps of reasoning they do. A reader who has to reconstruct a missing step has stopped reading your document and started writing their own.

## 8. Reread as the reader

Distance is the only reliable editor. Before you hand a document over, read it as someone who has only the page:

- Do the first lines tell me why I am reading this, before they tell me anything else?
- Read only the headings. Is that the argument?
- For each section: which question does it answer, and did the previous section make me ask it?
- Where is the thesis defended at length? Is that the longest part?
- Is there one sentence anywhere I could delete without losing anything? Delete it.
- Can I state the conclusion in two plain sentences after reading? If a reader could not, the document has not done its job.

When the stakes justify it, give the draft to someone with no context — a person, or a fresh agent that sees only the text — and ask them to restate the point of each section. Every place they stumble is a place the document assumed what it should have said.

## References

Read these when the situation calls for them, not by default:

- `references/document-shapes.md` — how the principles above take shape in common document types (status update, decision request, design or API proposal, explainer, strategy, postmortem, change description), and what the first lines of each must do. Shapes, not templates: start from the reader, then check the shape.
- `references/exemplars.md` — real documents worth imitating and one worth avoiding, each annotated with the specific move to copy, plus a worked case: a design-proposal page and the eleven comments its reader left on it, mapped to the principles each one broke.
- `references/sources.md` — where each principle comes from, for when you need to go deeper or cite it.
