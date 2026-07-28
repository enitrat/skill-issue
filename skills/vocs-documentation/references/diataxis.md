# Diátaxis Ground Truths

Distilled from [diataxis.fr](https://diataxis.fr) (Daniele Procida). These are the framework facts
that underpin the four-type router in SKILL.md. Consult this file when a page resists
classification, when a review finds mixed content, or when deciding documentation structure.

## The model

Documentation serves a practitioner of a craft, and a craft has exactly two dimensions
([Foundations](https://diataxis.fr/foundations/)):

- **action vs cognition** — practical steps (doing) vs propositional knowledge (thinking)
- **acquisition vs application** — study (learning the craft) vs work (using it)

Two binary dimensions yield exactly four quadrants — four documentation types, not three or five,
and no fifth to invent. Every piece of content belongs to one quadrant.

## The compass

The decision tool ([The compass](https://diataxis.fr/compass/)). Ask two questions of any content —
existing or planned: *action or cognition?* *acquisition or application?*

| If the content… | …and serves the user's… | …then it is |
|---|---|---|
| informs action | acquisition of skill (study) | a **tutorial** |
| informs action | application of skill (work) | a **how-to guide** |
| informs cognition | application of skill (work) | **reference** |
| informs cognition | acquisition of skill (study) | **explanation** |

Apply it at any zoom level — a whole page, a section, a single sentence. It works both directions:
classifying content in front of you, and choosing the form for a user need.

| | Tutorial | How-to guide | Reference | Explanation |
|---|---|---|---|---|
| answers | "Can you teach me to…?" | "How do I…?" | "What is…?" | "Why…?" |
| form | a lesson | a series of steps | dry description | discursive discussion |
| analogy | teaching a child to cook | a recipe | the label on a food packet | a book on culinary history |

## Blur: the map's failure modes

Each type shares a property with its neighbors, and that affinity is what makes types bleed into
each other ([The map](https://diataxis.fr/map/)). The blur pairs:

- tutorials ↔ how-to guides (both guide action)
- how-to guides ↔ reference (both serve work)
- reference ↔ explanation (both propositional knowledge)
- explanation ↔ tutorials (both serve study)

The single most common conflation in software docs is **tutorial vs how-to guide**
([Tutorials and how-to guides](https://diataxis.fr/tutorials-how-to/)). They look alike — ordered
practical steps promising success — but serve opposite needs. Distinguishing tests:

| Tutorial (study) | How-to guide (work) |
|---|---|
| Provides a learning experience; what matters is what the learner *does* and encounters | Directs work toward a result |
| Contrived, safe setting; path fully managed; eliminates the unexpected | Real world; must prepare for the unexpected |
| One path, no choices or alternatives | Forks and branches: "if this, then that" |
| Explicit about basics (where to type, what to click) | Assumes that as implicit knowledge |
| Responsibility lies with the teacher | Responsibility lies with the user |
| Must be complete end-to-end | Practical usability beats completeness; starts and ends at meaningful points, user joins it to their work |
| Concrete and particular throughout | General, adaptable to variations |

**Tutorial ≠ basic, how-to ≠ advanced.** A how-to guide can cover a mundane routine; a tutorial can
teach an advanced skill to an expert (an experienced anaesthetist still takes a *lesson* for a new
technique). The axis is study vs work, never difficulty.

**Reference vs explanation** ([Reference and explanation](https://diataxis.fr/reference-explanation/)):
the test is whether the reader turns to it *while executing a task* (reference) or *away from the
work, to think about it* (explanation). Rules of thumb: boring, unmemorable, lists and tables →
reference; readable in the bath, answers "can you tell me about…?" → explanation. The common slip is
reference examples growing into explanation — bad for both: the reference gets interrupted, the
explanation never develops properly. Move it out and link.

## Per-type ground truths

### Tutorials ([source](https://diataxis.fr/tutorials/))

- The first rule of teaching: **don't try to teach**. Provide an experience through which learning
  happens; explanation *blocks* learning by pulling attention away from doing.
- A tutorial is a contract where nearly all responsibility falls on the teacher. The exercise must
  be *meaningful* (sense of achievement), *successful* (completable), *logical*, and *usefully
  complete* (encounters every tool/concept the learner needs).
- What the learner *does* is not what they *learn* — they learn names, tools, workflows, relations
  through the doing. Design the journey around required encounters, not around the artifact built.
- Deliver visible results early and often; every step produces a comprehensible result.
- Maintain a narrative of the expected: "You will notice…", "The output should look like…", and
  flag likely failure signs ("If you don't see X, you probably forgot Y").
- Point out what to notice — observation is an active skill; close the learning loop in passing.
- Encourage repetition: learners re-run steps to confirm the world is reliable. Make steps
  repeatable wherever possible.
- All learning moves from concrete/particular to general/abstract. Stay concrete; the general
  patterns *will* emerge — you don't need to state them.
- Aspire to perfect reliability. One wrong promised result destroys confidence in the tutorial, the
  product, and the learner themselves. You can't be there to rescue them. Test with real users —
  you will not find the flaws yourself.
- Expect tutorials to be the most maintenance-heavy docs: changes cascade through the whole
  journey, unlike discrete fixes elsewhere.
- Say "In this tutorial we will create…", never "you will learn…" (presumptuous, poor pattern).

### How-to guides ([source](https://diataxis.fr/how-to-guides/))

- **Write from the user's problem, not the machinery's operations.** "How to deploy X for need Y"
  answers a human project; "click Deploy to deploy" is machinery walkthrough — information anyone
  competent already has, addressed to no need. A guide may cut across several tools; the user's
  goal defines its scope, not the product's feature list.
- Not merely procedures: real problems don't always reduce to linear steps. Guides may fork,
  overlap, have multiple entry/exit points, and call on the user's judgement — "actions" include
  thinking and decisions.
- Omit the unnecessary: practical usability over completeness.
- Seek *flow*: order steps by how the user thinks and acts, not just by hard dependencies.
  Minimize context switches, don't make the user hold thoughts open for long, avoid jumping back
  to earlier concerns. The best guides feel like they *anticipate* the user.
- Use conditional imperatives: "If you want x, do y. To achieve w, do z."
- Titles state the task exactly: "How to integrate application performance monitoring" — not
  "Integrating…" (ambiguous: about whether?) and never a bare noun phrase ("Application
  performance monitoring"). Search engines reward this as much as humans do.
- The list of how-to guides frames the picture of what the product can do; well-chosen guides are
  usually the most-read section of documentation.

### Reference ([source](https://diataxis.fr/reference/))

- **Describe and only describe.** Neutral description is unnatural — the pull to explain, instruct
  and opine is constant; resist it and link out instead.
- Reference is austere and authoritative; users *consult* it, they don't read it. They need truth
  and certainty — a firm platform to stand on while working.
- Reference is neutral about the user's purpose (a chart serves the navigator and the magistrate
  equally). Do not organize it around tasks.
- Structure mirrors the machinery: if a method belongs to a class in a module, the docs show the
  same relationship — a map corresponds to its territory. Side effect: gaps become visible.
- Consistency is what makes reference usable: standard patterns, same information in the same
  place in the same format everywhere. Reference is not the place for varied, delightful prose.
- Examples illustrate without explaining — the sanctioned way to add context to reference.
- Wrong material mixed into reference is not just noise; like a recipe printed among allergy
  information, it undermines material that must be reliable.

### Explanation ([source](https://diataxis.fr/explanation/))

- Understanding-oriented, read *away from* the product ("the only docs you might read in the
  bath"). Less urgent than the other three, but not less important: without it a practitioner's
  knowledge is fragmented and their practice anxious.
- Each page should bear an implicit "About…" in front of its title, and it helps to write against
  a real or imagined *why* question — explanation is otherwise unboundedly open-ended.
- Make connections, provide context: design decisions, history, constraints, implications.
- Opinion and perspective are *allowed and required* here — weigh alternatives, admit trade-offs,
  consider counter-examples. This is the one quadrant where that's true.
- Keep it bounded: explanation tends to absorb instructions and description. Those already have
  homes; letting them creep in damages the explanation and hides them from their proper place.

## Working with Diátaxis ([source](https://diataxis.fr/how-to-use-diataxis/), [start here](https://diataxis.fr/start-here/))

- It's a **guide, not a plan**. Never scaffold four empty sections and fill them in ("It's
  horrible"). Structure emerges *because* content improved, from the inside out — like organic
  growth, well-formed cells produce a well-formed organism.
- Work iteratively: take the page in front of you, ask *what user need does this serve? how well?
  what one small change improves it?* — make that change, publish it, repeat. Every step in the
  right direction is worth publishing immediately; don't batch big tranches.
- Documentation is never *finished*, but at every stage it can be *complete* — like a plant:
  useful now, healthy, ready for the next stage.
- Applying the framework to existing docs reliably *exposes* hidden functional defects — e.g.
  mirroring reference to code structure reveals coverage gaps; stripping explanation from a
  tutorial reveals steps where the reader was left to figure things out alone
  ([Quality](https://diataxis.fr/quality/)).
- Functional quality (accuracy, completeness, consistency) is objective, measurable, and a
  precondition; deep quality (flow, fit to needs, anticipating the user, feeling good to use) is
  what distinguishes excellent docs and is what the four-type discipline protects — chiefly by
  preventing purpose-crossing interruptions.

## Structure at scale ([source](https://diataxis.fr/complex-hierarchies/))

- Default hierarchy: four top-level sections, each with a landing page; add sub-groups (with their
  own landing pages) inside a section as it grows.
- Landing pages read like overviews — headings and introductory prose that contextualize links,
  never bare link dumps. Lists longer than ~7 items need breaking up unless mechanically ordered.
- When another axis intersects (per-framework tracks, user/developer/contributor audiences,
  per-platform docs): Diátaxis is four *kinds*, not four mandatory boxes. Split by whatever the
  product *is to each user* first (three effective products → three doc sets), and apply the four
  types within. Mixed arrangements are fine — e.g. shared tutorial, fully separated contributor
  how-tos — as long as no page muddles forms. Complex structures are acceptable when logical and
  patterned; muddled types never are.
