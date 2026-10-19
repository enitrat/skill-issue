---
name: github-issue
description: Write and manage GitHub issues. Use when creating, viewing, editing, commenting on, labelling or closing a GitHub issue, writing an issue body, creating or linking sub-issues, or dumping an issue tree to markdown and pushing it back.
---

# GitHub issues

The reader is a teammate who was not in the conversation. The issue gives them a
model of the problem and the system it lives in, then hands them the work. **They
own the solution.** The issue points; it does not prescribe.

**Only what matters is written.** A line earns its place when the reader would get
the problem wrong without it. When unsure, cut.

## Title

Conventional commit format, validated by the script (`--skip-validation` for repos
with another convention): `<type>(<scope>): <description>`, e.g.
`fix(api): resolve race condition in request handler`.

## Body

| Shape | When | Sections |
| --- | --- | --- |
| **Task** | We know what to do | What · Why · How |
| **Open question** | The fix is a decision | Question · What we found · Options |
| **Bug** | Behaviour differs from expected | What happens · Expected · How to reproduce |

- **What**: the change in product terms. What a user or caller can do afterwards.
- **Why**: the concrete problem, then the system explained so the reader gets it in
  one read: terms defined once, what happens when, one real example link.
- **How**: "Guidance only." and 2–5 pointers (prior art, a link, a constraint that
  rules out an obvious approach). Open points stay listed as open.
- **Options**: numbered, one line each with its cost, ending in "Something else?".

Cut implementation plans, edge-case lists, acceptance-criteria and testing-plan
checklists, facts the reader can't check, and history. Prune each line: would the
reader get the problem wrong without it? Then tighten with `/unslop`.

## Script

`scripts/gh_issue.py`, run with `uv run`. Create and push show a preview and ask
first; `--yes` skips it.

| Task | Command |
| --- | --- |
| Start a body | `init --template task\|question\|bug -o /tmp/issue.md` |
| Create | `create owner/repo --title "…" --body-file /tmp/issue.md [--labels a,b] [--assignees @me] [--milestone M] [--project P]` |
| Create a sub-issue | `create-sub owner/repo --parent 10 --title "…" --body-file …` |
| Link existing | `link owner/repo --parent 10 --child 42` |
| Edit | `edit owner/repo 123 [--title "…"] [--body-file …]` |
| View / list | `view owner/repo 123` · `list owner/repo [--labels bug]` |
| Sub-issues, incl. cross-repo | `list-subissues owner/repo 123 [--json]` |
| Comment / label / close | `comment owner/repo 123 "…"` · `labels owner/repo 123 --add a,b` · `close owner/repo 123 --reason completed` |

**Round trip.** `dump-tree owner/repo 123 ./issues/` writes the issue and its
sub-issues as markdown with YAML frontmatter (`title`, `repo`, `number`, `labels`,
`assignees`, `milestone`, `parent`). Edit locally, then `push ./issues/<file>.md`:
it updates the issue when `number` is set and creates one otherwise.
