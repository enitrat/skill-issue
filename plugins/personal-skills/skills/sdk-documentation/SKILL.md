---
name: sdk-documentation
description: >-
  Rules and patterns for writing comprehensive, high-quality SDK documentation for public libraries.
  Covers documentation architecture, narrative tone, user guides, and API references.
  Use when: (1) Writing or reviewing documentation for a public SDK/library,
  (2) Creating API reference pages for hooks/functions/classes,
  (3) Writing getting-started guides or tutorials,
  (4) Structuring a documentation site from scratch,
  (5) Reviewing documentation quality and consistency,
  (6) Setting up a VitePress documentation site for an SDK.
---

# SDK Documentation Best Practices

Rules for writing clear, scannable, code-forward documentation for public SDKs.
Derived from analysis of best-in-class SDK documentation (wagmi, viem, TanStack).

## Core Philosophy

| Principle | Meaning |
|-----------|---------|
| Code is the star | Prose exists to introduce, contextualize, and connect code examples |
| Scannable over narrative | Readers skim for answers; structure for rapid lookup |
| Show, don't tell | Diff annotations and working examples beat explanations |
| One concept per step | Never introduce multiple ideas simultaneously |
| Full files, not snippets | Every code block should be runnable in isolation |
| Template rigidly | Predictable structure is a feature, not a limitation |

## Quick Reference: Critical Rules

| Category | DO | DON'T |
|----------|-----|-------|
| Voice | "you" for concepts, "we" for tutorials | Passive voice |
| Tone | Professional-casual, confident | Humorous, condescending, or stiff |
| Sentences | 10-25 words, active voice | 35+ word run-on sentences |
| Code examples | Complete runnable files with focus annotations | Partial snippets missing context |
| Parameters | One `###` heading per param with full example | Tables or lists of parameters |
| Optional params | Indicate via `\| undefined` in type | "Optional" badges or markers |
| Jargon | SDK-specific terms explained; ecosystem terms assumed | Over-explaining industry basics |
| Sections | Rigid ordering: Import → Usage → Parameters → Return Type | Freeform section ordering |
| Cross-refs | Link to related APIs inline and in dedicated sections | "See also" dump at bottom |
| Warnings | Use admonitions (`::: warning`) for critical info | Inline bold warnings in prose |

## Detailed Guidance by Topic

- **Documentation structure**: See [references/structure.md](references/structure.md) for site architecture, page templates, navigation, shared content systems
- **Narrative tone**: See [references/tone.md](references/tone.md) for voice, style, sentence patterns, jargon handling
- **User guides**: See [references/guides.md](references/guides.md) for tutorial structure, progressive disclosure, framework variants
- **API references**: See [references/api-reference.md](references/api-reference.md) for parameter docs, return types, TypeScript presentation, cross-referencing
- **VitePress setup**: See [references/vitepress.md](references/vitepress.md) for project init, config, markdown extensions, twoslash, code groups, shared includes
