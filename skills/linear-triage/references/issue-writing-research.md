# Issue-Writing Research Notes (2026-08)

Evidence base behind [ISSUE-WRITING.md](ISSUE-WRITING.md). Consult when a rule is challenged or needs recalibrating. Deep-research synthesis, 2026-08-03.

## Evidence-backed findings

| Finding | Source |
|---|---|
| Users read 20–28% of words on a page; ~half only when ≤111 words. Each added 100 words gets ~18% read. | [NN/g, How Little Do Users Read?](https://www.nngroup.com/articles/how-little-do-users-read/) |
| F-pattern: attention concentrates on first lines, first words of lines, left edge; ~80% of viewing above the fold. | [NN/g F-pattern](https://www.nngroup.com/articles/f-shaped-pattern-reading-web-content-discovered/) |
| Inverted pyramid (conclusion first) measurably improves comprehension of scanned text. | [NN/g, Inverted Pyramid](https://www.nngroup.com/articles/inverted-pyramid/) |
| Bug reports: developers rank steps-to-reproduce, stack traces, test cases as most valuable; top complaint is incomplete info, then inaccurate repro steps. Survey n=466. | [Bettenburg et al., FSE 2008](https://thomas-zimmermann.com/publications/files/bettenburg-fse-2008.pdf) |
| 3,180 Copilot-authored PRs: self-contained issues +16.65% merge rate, well-scoped +16.44%, concrete steps +7.58%, named files +6.4–7.2%. **Body length and comment verbosity inversely correlate with success.** | [arXiv:2512.21426](https://arxiv.org/html/2512.21426v1) |
| Removing solution hints from issue text halves agent resolution rates (42.1%→21.8% SWE-bench Lite; 51.7%→25.9% Verified). The "How"/Pointers content is load-bearing. | [SWE-Bench+, arXiv:2410.06992](https://arxiv.org/html/2410.06992v2) |
| LLM positional attention is U-shaped: beginning and end attended, middle degrades. | [Lost in the Middle](https://arxiv.org/abs/2307.03172), [Found in the Middle](https://arxiv.org/pdf/2406.16008) |
| Context rot: all 18 frontier models tested degrade as input grows, well before window limits. | [Chroma, 2025](https://www.trychroma.com/research/context-rot) |

**Key convergence:** humans and LLMs share the same failure zone — the middle of the document. One U-shaped layout serves both audiences; no need for two documents.

**Key tension resolved:** self-containment helps while length hurts → raise information density, not word count. Long issues correlate with underspecified thinking, not thorough specification.

**No study establishes an optimal ticket word count.** The caps in ISSUE-WRITING.md are engineering judgment calibrated to this evidence — a starting policy to revise, not a finding. The Copilot study is observational (well-scoped may correlate with easy); treat effect sizes as upper bounds.

## Vendor guidance

- [Claude Code best practices](https://code.claude.com/docs/en/best-practices) — "The most useful specs are self-contained: they name the files and interfaces involved, state what is out of scope, and end with an end-to-end verification step." Give the agent a check it can run, or "looks done" is the only signal and you become the verification loop. Per line: "would removing this cause mistakes? If not, cut it."
- [Anthropic, context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) — context is finite with diminishing returns; smallest set of high-signal tokens; prefer just-in-time references (paths) over pre-loaded content.
- [GitHub Copilot agent best practices](https://docs.github.com/copilot/how-tos/agents/copilot-coding-agent/best-practices-for-using-copilot-to-work-on-tasks) — one clear outcome per issue; complete acceptance criteria; which files to change; treat the issue as a prompt. Hand to humans: cross-cutting refactors, security/auth/PII, incidents, ambiguity.
- [Linear agent docs](https://linear.app/docs/agents-in-linear) — agents receive title + description + labels + comments; comments are unreliable context → decisions get edited back into the description. Issues are assigned to humans, delegated to agents.
- [Linear collapsible sections](https://linear.app/changelog/2025-03-19-collapsible-sections) — collapsed content stays in the description string: the asymmetric human-short/agent-complete channel.
- [RFC 2119](https://www.rfc-editor.org/rfc/rfc2119.html) — MUST/SHOULD/MAY semantics apply only in ALL CAPS.

## Practitioner positions (opinion, well-regarded)

- [Linear Method](https://linear.app/method/write-issues-not-user-stories) — user stories are an anti-pattern; short direct titles; descriptions optional; quote feedback verbatim; **everyone writes their own issues** ("it forces you to think through the problem"). Note: challenges our one-lead-writes-most model — consistency bought at the price of engineers' thinking.
- [Shape Up](https://basecamp.com/shapeup/1.5-chapter-06) — pitch = Problem, **Appetite**, Solution, Rabbit Holes, **No-Gos**. Appetite constrains the solution; adopted into our Scope block.
- [Amazon working backwards](https://commoncog.com/working-backwards/) — the lesson is not "write prose", it is "a hard cap is a forcing function". Copy the cap, not the length.
- [Google design docs](https://www.industrialempathy.com/posts/design-docs-at-google/) — value is trade-offs and Goals/Non-Goals; past ~20 pages, split. Scaled down: >500-word issue = issue + design doc not yet separated.
- [Hashimoto / harness engineering](https://zed.dev/blog/agentic-engineering-with-mitchell-hashimoto) — every recurring agent mistake becomes a structural fix (test, lint, rule), not a longer prompt. Origin of the harness rule.
- [Addy Osmani, specs for agents](https://addyosmani.com/blog/good-spec/) — inline critical constraints; link the rest ("index, not full text"); Always/Ask-first/Never beats flat prohibitions.
- Gherkin critiques ([TestQuality](https://testquality.com/how-to-write-effective-gherkin-acceptance-criteria/), [bitbytebit](https://bitbytebit.substack.com/p/given-when-then-for-acceptance-criteria)) — ~3× token cost for zero measured gain outside Cucumber automation.
