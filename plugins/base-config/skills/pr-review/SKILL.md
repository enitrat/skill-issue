---
name: pr-review
description: Perform thorough, constructive pull request reviews using parallel specialized agents. Use when user wants to review a PR, provide code review feedback, or assess code changes. Features confidence-scored issues, validation filtering, and batched GitHub comments.
---

# PR Review Skill

This skill provides a structured approach to reviewing pull requests using **parallel specialized agents** for thorough coverage, with confidence scoring to minimize false positives.

**Important**: Any text comment you post must be prefixed with:
```
[AUTOMATED]
```
This is important because you are using the Github CLI with the account of your beloved human, and you want to make it clear that the comment is not coming from the human.

---

## Review Workflow

### Step 1: Pre-Review Validation

Before starting, launch a **haiku agent** to check if review should proceed:

```
Check if any of the following are true for the PR:
- The PR is closed
- The PR is a draft
- The PR is trivial (automated, obviously correct single-line change)

If any condition is true, stop and explain why.
```

If validation fails, do not proceed with the review.

### Step 2: Gather Context

Launch **two haiku agents in parallel**:

**Agent A - PR Summary**:
```
Fetch PR details using: uv run scripts/gh_pr.py files owner/repo <number>
If there's a linked issue, fetch it: uv run scripts/gh_pr.py issue owner/repo <issue>
Return a brief summary of:
- What the PR does
- Files changed
- Author's stated intent — based on code and eventual linked issue
```

**Agent B - Guidelines Discovery**:
```
Find all relevant guideline files:
- Root CLAUDE.md (if exists)
- CLAUDE.md files in directories containing modified files
- Any project-specific style guides

Return the file paths and key rules that apply to changed files.
```

### Step 3: Parallel Review Agents

Launch **4 specialized agents in parallel** to review the changes. Each agent should receive:
- PR title and description
- Relevant guideline summaries (from Step 2)
- The diff (via `uv run scripts/gh_pr.py files owner/repo <number> --raw`)

**Agent 1: Bug Hunter (opus)**
See `agents/bug-hunter.md`. Focus on actual bugs and security issues.

**Agent 2: Bug Hunter (opus)**
Same as Agent 1, run twice for coverage. Different agents may catch different issues.

**Agent 3: Guideline Compliance (sonnet)**
See `agents/guideline-compliance.md`. Check CLAUDE.md and project convention adherence.

**Agent 4: Error Handling Auditor (sonnet)**
See `agents/error-handling-auditor.md`. Hunt for silent failures and poor error handling.

**CRITICAL**: We only want **HIGH SIGNAL** issues:
- Objective bugs that will cause incorrect behavior at runtime
- Clear, unambiguous guideline violations with quoted rules
- Silent failures that hide errors from users

We do NOT want:
- Subjective concerns or suggestions
- Style preferences not explicitly required
- Potential issues that "might" be problems
- Anything requiring interpretation or judgment

### Step 4: Issue Validation

For each issue found with confidence >= 80, launch a **validation subagent**:

See `agents/issue-validator.md`. The validator independently verifies:
- Bug reports are real (trace code, check for defensive handling)
- Guideline violations actually apply (rule exists, no exceptions)
- The severity assessment is accurate

Use **opus** subagents for bug validation, **sonnet** for guideline validation.

### Step 5: Filter Results

Only keep issues that:
1. Had original confidence >= 80
2. Were validated in Step 4
3. Are not duplicates

This gives us our final list of high-signal issues.

### Step 6: Post Review

#### If NO issues found:

Post a summary comment (if requested):
```bash
gh pr comment <number> --body "[AUTOMATED]

## Code Review

No issues found. Checked for bugs, guideline compliance, and error handling."
```

#### If issues found:

Use the batched review workflow to post all comments at once.

---

## The Core Standard

**Approve changes that improve code health, even if imperfect.**

- The goal is continuous improvement, not perfection
- Don't block progress over minor issues - use "Nit:" prefix for non-blocking suggestions
- Reject only when the change worsens overall code health or is fundamentally unwanted

### Decision Hierarchy

When opinions conflict:
1. Technical facts and data override opinions
2. Style guides are authoritative
3. Design decisions require principle-based reasoning, not preference
4. Consistency with existing code (when it maintains health)

---

## What to Look For

### Design
- Is the overall architecture sound?
- Do code interactions make sense?
- Does this belong here, or in a library/different module?
- Does it integrate well with existing systems?

### Architectural Consistency
- **Identify existing abstractions** - What patterns does this codebase already have?
- **Check for pattern reuse** - Is new code following established patterns or reinventing them?
- **Look for duplicated abstractions** - Is the PR reimplementing existing helpers?
- **Look for useless abstractions** - Is complexity being added unnecessarily?

**Key question**: *"How do similar features in this codebase solve this problem?"*

### Functionality
- Does the code do what the author intended?
- Watch for: edge cases, race conditions, concurrency bugs

### Complexity
- Can you understand the code quickly?
- Is it over-engineered for hypothetical future needs?
- **Principle**: Solve the problem that exists now

### Tests
- Are there appropriate tests?
- Will tests actually fail when the code breaks?
- Are test cases meaningful, not just coverage padding?

---

## Writing Effective Comments

### Severity Labels
- **Nit:** Minor issue, should fix but won't block approval
- **Optional/Consider:** Suggestion worth considering, not required
- **FYI:** Information only, no action expected

### Tone
- Be kind - critique code, never the person
- Explain the reasoning behind suggestions
- Acknowledge when the author knows more than you

---

## Specialized Agents Reference

Additional agents available for targeted analysis:

### Test Analyzer
See `agents/test-analyzer.md`. Use when:
- PR adds significant new functionality
- You want to verify test coverage quality
- User asks about test thoroughness

### Full Agent List

| Agent | Focus | Model | When to Use |
|-------|-------|-------|-------------|
| bug-hunter | Bugs & security | opus | Default parallel review |
| guideline-compliance | CLAUDE.md adherence | sonnet | Default parallel review |
| error-handling-auditor | Silent failures | sonnet | Default parallel review |
| test-analyzer | Test coverage | sonnet | On request or for new features |
| issue-validator | Verify findings | inherit | Validation step |

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
# Fetch issue details
uv run scripts/gh_pr.py issue owner/repo 42

# Get PR files and diff
uv run scripts/gh_pr.py files owner/repo 123

# Get raw JSON for agent processing
uv run scripts/gh_pr.py files owner/repo 123 --raw

# Get unresolved review comments
uv run scripts/gh_pr.py comments owner/repo 123 --unresolved

# Initialize review file
uv run scripts/gh_pr.py init-review owner/repo 123

# Post batched review
uv run scripts/gh_pr.py post owner/repo 123 /tmp/pr-review-owner-repo-123.json
```

---

## Posting the Code Review

### Workflow Overview

Reviews are posted in a single batch to avoid spamming notifications. During the review process, accumulate feedback in a transient JSON file, then submit everything at once.

If you are inside the same repository as the PR, checkout the PR branch into a temporary worktree for full codebase context.

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

Edit the JSON file to add comments from validated issues:

```json
{
  "path": "src/utils/parser.ts",
  "line": 42,
  "side": "RIGHT",
  "body": "[AUTOMATED] This catch block swallows all exceptions without logging. Unexpected errors will be silently ignored.\n\nConfidence: 92/100"
}
```

**Field reference:**
- `path`: File path relative to repo root
- `line`: Line number in the new file (for additions/modifications)
- `side`: `RIGHT` for new/modified code, `LEFT` for deleted code
- `body`: The comment text (include confidence score)

### Step 4: Set the Review Verdict

| Verdict | `event` value | When to use |
|---------|---------------|-------------|
| Approve | `APPROVE` | Code is good to merge |
| Request Changes | `REQUEST_CHANGES` | Blocking issues must be addressed |
| Comment | `COMMENT` | Feedback only, not blocking |

### Step 5: Post the Review

```bash
uv run scripts/gh_pr.py post owner/repo 123 /tmp/pr-review-owner-repo-123.json
```

### Step 6: Cleanup

```bash
uv run scripts/gh_pr.py cleanup owner/repo 123
```

---

## Review Checklist (Quick Reference)

- [ ] PR description is clear and links to relevant issue
- [ ] Design is sound and appropriate for the codebase
- [ ] New code extends existing abstractions rather than duplicating them
- [ ] Follows patterns established by similar code in the codebase
- [ ] Code does what it claims to do
- [ ] Edge cases and error conditions handled
- [ ] No over-engineering or unnecessary complexity
- [ ] Tests are present and meaningful
- [ ] Naming is clear and consistent
- [ ] Comments explain *why* where needed
- [ ] Style guide followed
- [ ] Documentation updated if user-facing
- [ ] No security vulnerabilities introduced
- [ ] No silent failures in error handling

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
