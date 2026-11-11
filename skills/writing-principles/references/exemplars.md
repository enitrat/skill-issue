# Exemplars

Real documents, each annotated with the one or two moves worth copying. Read the original when the move matters for what you are writing; the annotation is a pointer, not a substitute.

## Proposals and design documents

**Rust RFC template** — https://github.com/rust-lang/rfcs/blob/master/0000-template.md
- Splits the proposal into a *guide-level explanation* ("explain the proposal as if it was already included in the language and you were teaching it to another Rust programmer") and a *reference-level explanation* (interactions, corner cases, returning to the guide-level examples). This is use before specification as a required structure.
- Makes "Drawbacks: why should we not do this?" and "Rationale and alternatives: why is this design the best in the space of possible designs?" mandatory sections. The reasoning is part of the document, not a defence added afterwards.

**React Hooks RFC** — https://github.com/reactjs/rfcs/blob/main/text/0068-react-hooks.md
- Opens with one sentence ("In this RFC, we propose introducing Hooks to React."), three lines on what that enables, then a working example in the first screen. The reader holds a concrete instance before any argument.
- Sends the long detail to linked documents instead of making the RFC carry it. The template behind it asks for the motivation to be written so it "still works if the RFC is rejected".

**Design docs at Google (Malte Ubl)** — https://www.industrialempathy.com/posts/design-docs-at-google/
- "Goals and non-goals": non-goals are things that *could reasonably be goals* and are excluded on purpose, which tells the reader where the edges are.
- "Alternatives considered" is called one of the most important sections: the trade-offs are what gives the document long-term value. Also says when *not* to write one: when the design is not ambiguous.

**Architecture decision records (Michael Nygard)** — https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions
- One decision per record, one or two pages: context (the forces, stated neutrally), decision ("We will..."), consequences, the negative ones included.
- "We will write each ADR as if it is a conversation with a future developer": a reader with no context, months later, is the reader to write for.

## Narrative and argument

**Amazon's six-page narrative** — relayed by Brad Porter at https://www.anecdote.com/2018/05/amazons-six-page-narrative-structure/
- Replaces slides with prose because a narrative forces the writer to state how ideas relate and which matter more; bullets let them skip it.
- Bezos's description of a good memo is vertical logic in one line: "If you read the whole six-page memo, on page 2 you have a question but on page 4 that question is answered."

**The Pyramid Principle, summarised by Will Larson** — https://lethain.com/pyramid-principle/
- The compact statement of answer-first structure, the situation-complication-question-answer opening, and the rule that every point raises a question answered directly beneath it. Use it to grade a draft's structure.

## Teaching and explanation

**Bartosz Ciechanowski, "Lights and Shadows"** — https://ciechanow.ski/lights-and-shadows/
- Starts from nothing ("To talk about light we have to start in darkness"), adds one variable at a time with one demonstration each, and announces detours before taking them ("before we get there we have to take a few steps back"). Every new idea attaches to the one before it.

**Bret Victor, "Up and Down the Ladder of Abstraction"** — https://worrydream.com/LadderOfAbstraction/
- Understanding comes from moving between a concrete case and the general pattern, and back. In prose: an example, the pattern it belongs to, then the example the pattern explains.

**Diátaxis** — https://diataxis.fr/ (and the compass: https://diataxis.fr/compass/)
- Two questions sort any passage: does it serve action or understanding, and study or work? The four answers (tutorial, how-to, reference, explanation) are different jobs, and a passage that tries to do two of them does neither. "Describe and only describe" is the rule for reference.

## Reports and change descriptions

**Hugo Richard, "What my pull requests look like now"** — http://hugorcd.com/writing/what-my-pull-requests-look-like-now
- First line says who did what and whether a human reviewed it, so the reader knows how to read the rest.
- Evidence matched to the kind of change (the same page before and after; the same input on both sides), and a closing two or three sentences an outsider could follow: "if it doesn't make sense, the change probably doesn't either."

**Anthropic, "Communicating clearly" (prompting guide for Fable 5.2)** — https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/prompting-claude-fable-5-2
- Write for "an intelligent but low-context reader"; key points in the first few sentences; "do not use undefined references and ideas in line 1 that won't make sense until the reader reaches line 12." Also warns that hard length rules make prose choppy, which is why this skill states principles rather than limits.

**Cloudflare outage report** — https://blog.cloudflare.com/cloudflare-outage/
- The first paragraph states duration, what users saw, the cause, and what it was not. A reader who stops there has the whole story.

## A document to learn from by negative example

**The Columbia shuttle "tile penetration" slide, analysed by Edward Tufte** — https://www.edwardtufte.com/notebook/columbia-accident-investigation-board-the-boeing-powerpoint-slide/
- The title reassured ("Review of Test Data Indicates Conservatism for Tile Penetration"); the warning that conditions were far outside the tested range sat low on the slide, in small type, under nested bullets. The accident board found that the uncertainties that signalled danger "dropped out of the information chain".
- The lesson is structural: the title and the top position carry the real finding, including the bad news, and quantities keep their units.

## Worked case: a design-proposal page and its reader's comments

An HTML page proposed a redesigned vault API for an SDK and showed how an application would move onto it. It followed a template closely: a short answer first, a fixed sequence of sections, strict caps on words per section, tables and code in place of prose, provenance badges in the header. Its reader, the engineer who would present it to two teams, left eleven comments. Each maps to a principle the page broke.

| Reader's comment | What the page did | Principle broken |
|---|---|---|
| "You provide an 'answer' to a question that has not even been given." / "start by introducing the subject: why am I reading this, even? What are we trying to solve? THEN only we can add a TLDR." | Opened with the conclusion and three lines of code, before stating any problem. | §2 Pose the question first: a peer reader who did not ask needs the situation and complication before the answer. |
| "this is the core of the document and one of the part you made the most succint. It's hard to understand the reasoning and the thought schema that lead to this solution." | Reduced the "why this design" section to a table of entry points, to stay under a word cap. | §5 Spend words where the reasoning is. The thesis section must be the longest. |
| "I still have no idea what the previous shape looked like besides a bunch of isolated examples. Nor do I have what the new looks like and comparison side-by-side." | Showed the current API in trimmed fragments and the proposed one as a list of names. | §3 Set up, then pay off; §6 the comparison is the evidence: the same task in both worlds. |
| "This is not properly showing the public API of the SDK whose failure mode you want to highlight later on." | The "today" section did not establish what the "failures" section later relied on. | §3 Set up, then pay off. |
| "we don't understand if its from the super-app integration, the sdk design itself, or both together." | Listed failures as symptoms without saying what caused each. | §4 Diagnosis with causes. |
| "we are not introducing WHO they are and why they have different use cases enough ... I dont understand why a custodian wants JSON serialization." | Stated each consumer's needs as table cells, with no "because". | §4 Introduce the actors before their needs. |
| "its not even clear if this is a real requirement." | Included a requirement inferred from plausibility, presented as fact. | §6 Say what you did not establish; mark assumptions. |
| "'as JSON' maybe not but serializable, yes" | Overstated a property. | §6 Claim exactly what is true. |
| "I dont think that ZAMA sdk must export its vault definitions. It's app configuration." | Presented a contestable decision as settled, with no alternative shown. | §6 Show the alternatives you rejected, at each load-bearing decision. |
| "this is typically the kind of 'pills' ... I consider as 'slop text': it does not provide any value to reader." | Header badges: "Proposal, nothing decided", "Checked on...", "Sketch: compiled against...". | §5 Cut what does not teach. Metadata is not content. |
| "this is a good initial context for framing the debate. that's a nice one." | The domain section: the nouns and how they relate, in one diagram, before any argument. | What worked: §4 known before new, and §3 setting up what later sections use. |

The pattern behind the failures: the template optimised each section in isolation (short, dense, visual) and nothing optimised the thread between them. The reader got accurate parts and no argument.
