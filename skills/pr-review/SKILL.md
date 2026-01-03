---
name: pr-review
description: Perform thorough, constructive pull request reviews. Use when user wants to review a PR, provide code review feedback, or assess code changes. This skill provides a structured approach to evaluating code quality, design, and implementation while maintaining constructive communication, and how to perform the review through the Github CLI.
---

# PR Review Skill

This skill provides a structured approach to reviewing pull requests, distilled from Google's engineering practices.
Keep this in mind: any text comment that you make must be prefixed with the following prefix:
```
[AUTOMATED]
```
This is important because you are using the Github CLI with the account of your beloved human, and you want to make it clear that the comment is not coming from the human.

## The Core Standard

**Approve changes that improve code health, even if imperfect.**

- The goal is continuous improvement, not perfection
- Don't block progress over minor issues—use "Nit:" prefix for non-blocking suggestions
- Reject only when the change worsens overall code health or is fundamentally unwanted

### Decision Hierarchy

When opinions conflict:
1. Technical facts and data override opinions
2. Style guides are authoritative
3. Design decisions require principle-based reasoning, not preference
4. Consistency with existing code (when it maintains health)

## Review Approach: Three Steps

### Step 1: Assess the Overall Change

Before diving into code:
- Read the PR description and linked issue (use `uv run scripts/gh_pr.py issue owner/repo <number>` to fetch issue details with proper authentication)
- Does this change make sense? Should it exist?
- If fundamentally problematic, respond immediately with explanation

### Step 2: Examine Critical Components First

- Identify files with the most substantial logic changes
- Review these first—they provide context for everything else
- Flag major design issues immediately (don't wait until the end)
- If design is wrong, communicate early so author can course-correct

### Step 3: Review Remaining Files

- Go through remaining files methodically
- Consider reading tests before implementation to understand intent
- Review every line within the broader context

## What to Look For

### Design
- Is the overall architecture sound?
- Do code interactions make sense?
- Does this belong here, or in a library/different module?
- Does it integrate well with existing systems?

### Architectural Consistency

**Before reviewing individual files, understand the codebase's existing patterns:**

1. **Identify existing abstractions** - What helpers, utilities, or patterns does this codebase already have for similar problems?

2. **Check for pattern reuse** - Is the new code following established patterns, or reinventing them? If similar code exists elsewhere, how was it structured?

3. **Ask the extensibility question** - "If someone adds a similar feature tomorrow, would they copy-paste this code or reuse it?" Copy-paste is a design smell.

4. **Look for duplicated abstractions** - Is the PR reimplementing logic that already exists in a helper? New code should extend existing abstractions, not duplicate them.

5. **Look for useless abstractions** - Is the PR introducing a new abstraction that is not needed? Will we likely need to do a similar thing in the future? If not, it's probably not worth the complexity. You can ask the author what they think about it.

**Key question to always ask:** *"How do similar features in this codebase solve this problem?"*

This is often more important than catching bugs—architectural inconsistency compounds over time and makes codebases harder to maintain.

### Functionality
- Does the code do what the author intended?
- Does it serve end-users and future developers well?
- Watch for: edge cases, race conditions, concurrency bugs
- UI changes warrant extra scrutiny for user impact

### Complexity
- Can you understand the code quickly?
- Is it over-engineered for hypothetical future needs?
- **Key principle**: Solve the problem that exists now, not speculative future problems

### Tests
- Are there appropriate tests (unit, integration, e2e)?
- Will tests actually fail when the code breaks?
- Are test cases meaningful, not just coverage padding?

### Naming
- Do names clearly communicate purpose?
- Are they descriptive yet readable?

### Comments
- Do comments explain *why*, not *what*?
- Are they necessary, or does the code speak for itself?
- If code needs explanation in review comments, request code comments instead

### Style & Consistency
- Does it follow the project's style guide?
- Is it consistent with surrounding code?

### Documentation
- Are user-facing changes documented?
- READMEs, API docs, and references updated?

## Writing Effective Comments

### Tone
- Be kind—critique code, never the person
- Explain the reasoning behind suggestions
- Acknowledge when the author knows more than you

### Severity Labels
Use prefixes to clarify intent:
- **Nit:** Minor issue, should fix but won't block approval
- **Optional/Consider:** Suggestion worth considering, not required
- **FYI:** Information only, no action expected

### Balance Direction and Learning
- Sometimes point out issues and let the author solve them
- Sometimes provide explicit solutions
- Use judgment based on complexity and author experience

### Positive Feedback
- Call out things done well: clean algorithms, thorough tests, clever approaches
- Reinforcing good practices encourages their continuation

## Handling Disagreements

### When Author Pushes Back

1. **Consider their perspective**—they may have deeper context
2. **If they're right**, acknowledge it and move on
3. **If you still disagree**, explain *why* it matters with additional context
4. Maintain courtesy even through multiple rounds of discussion

### "We'll Fix It Later"

- This almost never happens—competing priorities take over
- Insist on cleanup before merge unless truly an emergency
- If unavoidable: require a filed issue and TODO comment

### Escalation

If consensus fails after good-faith discussion:
- Consult technical leads or maintainers
- Reference established project standards
- Don't let reviews stall indefinitely

## Speed Matters

### Response Time
- Respond at natural break points (not mid-task)
- Maximum: one business day
- Goal: multiple review rounds within a single day when needed

### Why Speed Matters
Slow reviews cause:
- Blocked features and fixes
- Developer frustration
- Pressure to approve substandard work

### Large PRs
- Request authors split into smaller, sequential changes
- Large PRs are harder to review well and slower to merge

---

## Review Checklist (Quick Reference)

- [ ] PR description is clear and links to relevant issue
- [ ] Design is sound and appropriate for the codebase
- [ ] **New code extends existing abstractions rather than duplicating them**
- [ ] **Follows patterns established by similar code in the codebase**
- [ ] Code does what it claims to do
- [ ] Edge cases and error conditions handled
- [ ] No over-engineering or unnecessary complexity
- [ ] Tests are present and meaningful
- [ ] Naming is clear and consistent
- [ ] Comments explain *why* where needed
- [ ] Style guide followed
- [ ] Documentation updated if user-facing
- [ ] No security vulnerabilities introduced
- [ ] No obvious performance regressions

---

## Scripts Reference

This skill includes Python scripts in `scripts/` that wrap GitHub API operations. Run them with `uv`:

### Available Commands

| Command | Description |
|---------|-------------|
| `files` | Get PR files with status and patch info |
| `comments` | Get review comments (supports `--unresolved`, `--pending` filters) |
| `reviews` | List all reviews on a PR |
| `post` | Post a batched review from JSON file |
| `reply` | Reply to a specific review comment |
| `resolve` | Resolve or unresolve a review thread |
| `head` | Get the head commit SHA for a PR |
| `checkout` | Create a worktree to review PR locally |
| `cleanup` | Remove a PR worktree |
| `init-review` | Initialize a review JSON file |
| `issue` | Fetch issue details (title, description, labels, assignees) |

### Usage Examples

```bash
# Fetch issue details (use this for proper authentication)
uv run scripts/gh_pr.py issue owner/repo 42

# Get PR files and diff
uv run scripts/gh_pr.py files owner/repo 123

# Get unresolved review comments
uv run scripts/gh_pr.py comments owner/repo 123 --unresolved

# Get raw JSON output
uv run scripts/gh_pr.py comments owner/repo 123 --raw

# List all reviews
uv run scripts/gh_pr.py reviews owner/repo 123

# Get head commit SHA (for review submission)
uv run scripts/gh_pr.py head owner/repo 123

# Reply to a comment
uv run scripts/gh_pr.py reply owner/repo 456 "[AUTOMATED] Good catch, fixed!"

# Resolve a thread by comment ID
uv run scripts/gh_pr.py resolve owner/repo 123 --comment-id 456

# Unresolve a thread by comment ID
uv run scripts/gh_pr.py resolve owner/repo 123 --comment-id 456 --unresolve
```

---

## Posting the Code Review

### Workflow Overview

Reviews are posted in a single batch to avoid spamming notifications. During the review process, accumulate feedback in a transient JSON file, then submit everything at once.

If you are inside the same repository as the PR, you MUST checkout the PR branch, inside a new worktree that will be temporary and deleted after the review, and use local tools to review the code, so as to get full context of the codebase on top of the code diff.

### Step 1: Checkout the PR (if in same repo)

```bash
# Create a temporary worktree for the PR
WORKTREE_PATH=$(uv run scripts/gh_pr.py checkout owner/repo 123)
cd "$WORKTREE_PATH"
```

### Step 2: Initialize Review File

```bash
# Creates /tmp/pr-review-{owner}-{repo}-{pr}.json with commit SHA
uv run scripts/gh_pr.py init-review owner/repo 123
```

This creates a JSON file with the structure:
```json
{
  "owner": "anthropics",
  "repo": "claude-code",
  "pr_number": 123,
  "commit_id": "abc123def456",
  "body": "",
  "event": "COMMENT",
  "comments": []
}
```

### Step 3: Add Comments During Review

Edit the JSON file to add comments to the `comments` array as you review each file. Make sure to use the correct line number!

```json
{
  "path": "src/utils/parser.ts",
  "line": 42,
  "side": "RIGHT",
  "body": "[AUTOMATED] Nit: consider extracting this logic into a helper function for readability."
}
```

**Field reference:**
- `path`: File path relative to repo root
- `line`: Line number in the new file (for additions/modifications)
- `side`: `RIGHT` for new/modified code, `LEFT` for deleted code being commented on
- `body`: The comment text (use severity prefixes: `Nit:`, `Optional:`, `FYI:`)

### Step 4: Set the Review Verdict

Before posting, update the `event` and `body` fields in the JSON:

| Verdict | `event` value | When to use |
|---------|---------------|-------------|
| Approve | `APPROVE` | Code is good to merge |
| Request Changes | `REQUEST_CHANGES` | Blocking issues must be addressed |
| Comment | `COMMENT` | Feedback only, not blocking |

Set `body` to a summary of the review (required for `REQUEST_CHANGES` and `COMMENT`).

### Step 5: Post the Review

```bash
# Submit the batched review (auto-cleans up JSON file on success)
uv run scripts/gh_pr.py post owner/repo 123 /tmp/pr-review-owner-repo-123.json
```

### Step 6: Cleanup

```bash
# Remove the worktree after review
uv run scripts/gh_pr.py cleanup owner/repo 123
```

### Replying to Existing Comments

```bash
# Reply to a specific review comment
uv run scripts/gh_pr.py reply owner/repo 456 "[AUTOMATED] Response to the discussion"
```

### Resolving Comment Threads

```bash
# Resolve a thread by comment ID
uv run scripts/gh_pr.py resolve owner/repo 123 --comment-id 456

# Unresolve a thread by comment ID
uv run scripts/gh_pr.py resolve owner/repo 123 --comment-id 456 --unresolve
```

### Quick Reference: Script Commands

| Action | Command |
|--------|---------|
| Fetch issue details | `uv run scripts/gh_pr.py issue owner/repo 42` |
| Get PR files & diff | `uv run scripts/gh_pr.py files owner/repo 123` |
| Get existing review comments | `uv run scripts/gh_pr.py comments owner/repo 123` |
| Get unresolved comments only | `uv run scripts/gh_pr.py comments owner/repo 123 --unresolved` |
| Get PR reviews | `uv run scripts/gh_pr.py reviews owner/repo 123` |
| Initialize review file | `uv run scripts/gh_pr.py init-review owner/repo 123` |
| Post batched review | `uv run scripts/gh_pr.py post owner/repo 123 /path/to/review.json` |
| Reply to comment | `uv run scripts/gh_pr.py reply owner/repo 456 "message"` |
| Resolve thread | `uv run scripts/gh_pr.py resolve owner/repo 123 --comment-id 456` |
| Get commit SHA | `uv run scripts/gh_pr.py head owner/repo 123` |
| Create worktree | `uv run scripts/gh_pr.py checkout owner/repo 123` |
| Remove worktree | `uv run scripts/gh_pr.py cleanup owner/repo 123` |
