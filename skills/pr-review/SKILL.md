---
name: pr-review
description: Mechanics for leaving a pull request review on GitHub - CLI scripts for fetching PR data, attaching comments to the right file/line, wording/tone/severity conventions, and posting a batched review. Use when the user has feedback to leave on a PR and needs to know how to post it correctly.
---

# PR Review Skill

This skill covers **how to leave a PR review**, not what to look for in the code. It assumes you already know which issues you want to raise and gives you the CLI commands and conventions to attach them to the right place, word them well, and post them as a single batched review.

**Important**: Any text comment you post must be prefixed with:
```
[AUTOMATED]
```
This is important because you are using the Github CLI with the account of your beloved human, and you want to make it clear that the comment is not coming from the human.

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
- Don't block progress over minor issues - use "Nit:" prefix for non-blocking suggestions

---

## Posting the Code Review

### Workflow Overview

Reviews are posted in a single batch to avoid spamming notifications. Accumulate feedback in a transient JSON file, then submit everything at once.

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

### Step 3: Add Comments

Edit the JSON file's `comments` array to attach feedback to the right file and line:

```json
{
  "path": "src/utils/parser.ts",
  "line": 42,
  "side": "RIGHT",
  "body": "[AUTOMATED] Nit: this catch block swallows all exceptions without logging."
}
```

**Field reference:**
- `path`: File path relative to repo root
- `line`: Line number in the new file (for additions/modifications)
- `side`: `RIGHT` for new/modified code, `LEFT` for deleted code
- `body`: The comment text, prefixed with `[AUTOMATED]`

To find valid file/line targets, or to check what's already been discussed, use `files` and `comments` (see Scripts Reference below).

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

If there are no comments to attach, post a summary comment instead:
```bash
gh pr comment 123 --body "[AUTOMATED]

## Code Review

No issues found."
```

### Step 6: Cleanup

```bash
uv run scripts/gh_pr.py cleanup owner/repo 123
```

---

## Replying to and Resolving Existing Comments

```bash
# Reply to a specific review comment
uv run scripts/gh_pr.py reply owner/repo 456 "[AUTOMATED] Response to the discussion"

# Resolve a thread by comment ID
uv run scripts/gh_pr.py resolve owner/repo 123 --comment-id 456

# Unresolve a thread by comment ID
uv run scripts/gh_pr.py resolve owner/repo 123 --comment-id 456 --unresolve
```

---

## Scripts Reference

This skill includes a Python script (`scripts/gh_pr.py`) that wraps GitHub API operations. Run it with `uv`:

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
