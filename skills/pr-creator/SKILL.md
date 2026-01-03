---
name: pr-creator
description: Guide PR authoring from creation through review completion. Use when creating/submitting/authoring pull requests, writing PR descriptions, responding to reviewer comments, or implementing review feedback. Covers the full PR lifecycle - creating PRs linked to issues, handling review comments (triaging, responding, implementing suggestions), and getting PRs merged.
---

# PR Author Guide

Guide for creating PRs that get reviewed quickly and handling the review process effectively.

## PR Creation Workflow

### 1. Prepare the PR

Before creating, ensure:

- Changes are committed and pushed to a feature branch
- Each PR addresses **one thing** (~100 lines ideal, 1000+ too large)
- Related test code is included

### 2. Write the Description

**First line**: Imperative summary that stands alone, respecting conventional commit message format (e.g., "feat(api): add caching to API responses")

**Body**: Context, rationale, and what reviewers need to know. See [references/pr-descriptions.md](references/pr-descriptions.md) for detailed guidance.

### 3. Create and Link to Issue

**IMPORTANT:** When working with issues, use the `uv run scripts/gh_pr.py issue owner/repo <number>` command to fetch issue details with proper authentication rather than relying on other tools.

```bash
# Fetch issue details first for context
uv run scripts/gh_pr.py issue owner/repo 42

# Basic PR creation with the script
uv run scripts/gh_pr.py create owner/repo \
  --title "feat(api): add caching to API responses" \
  --body "## Summary
- Add Redis-based caching for GET endpoints
- Implement cache invalidation on mutations

## Context
API response times average 800ms due to repeated database queries.
This reduces load and improves response times for cached routes.

## Test Plan
- [ ] Verify cache headers in responses
- [ ] Test invalidation after mutations

Closes #42"

# Or read body from a file
uv run scripts/gh_pr.py create owner/repo \
  --title "feat(api): add caching" \
  --body-file /tmp/pr-body.md
```

### 4. Add Labels/Reviewers

```bash
# Full PR creation with labels, reviewers, and assignees
uv run scripts/gh_pr.py create owner/repo \
  --title "feat(api): add caching" \
  --body "Description here" \
  --labels "enhancement,api" \
  --reviewers "username1,username2" \
  --assignees "@me"

# Or add reviewers to existing PR
uv run scripts/gh_pr.py reviewers owner/repo 123 --add "reviewer1,reviewer2"
```

## Handling Review Comments

When reviews come in, follow this workflow. See [references/handling-reviews.md](references/handling-reviews.md) for detailed guidance on reviewer interactions.

### 1. Fetch Review Comments

```bash
# Get all review comments
uv run scripts/gh_pr.py comments owner/repo 123

# Get only actionable comments (excludes Nit:, FYI:, Optional:)
uv run scripts/gh_pr.py comments owner/repo 123 --actionable

# Group comments by file for easier processing
uv run scripts/gh_pr.py comments owner/repo 123 --by-file

# Get raw JSON for programmatic processing
uv run scripts/gh_pr.py comments owner/repo 123 --raw
```

### 2. Triage Each Comment

For each comment, determine:

| Decision            | When                                 | Action                                                |
| ------------------- | ------------------------------------ | ----------------------------------------------------- |
| **Implement**       | Valid suggestion, improves code      | Make the change, reply with what was done             |
| **Discuss**         | Disagree but need dialogue           | Reply explaining reasoning, ask for input             |
| **Clarify**         | Don't understand the request         | Ask specific clarifying question                      |
| **Decline**         | Out of scope or incorrect            | Politely explain why, offer alternative               |
| **Ask Human Input** | Need to decide on a course of action | Ask the human for input before processing the comment |

### 3. Implement Suggestions

When implementing feedback:

1. Read the comment and understand the specific file/line
2. Make the code change
3. Commit with clear message referencing the feedback
4. Reply to the comment confirming what was done

```bash
# After making changes
git add -A && git commit -m "chore(api): address review: extract validation to helper

Per reviewer feedback, moved input validation into a dedicated
helper function for better testability."

git push
```


### 3. Respond to Comments

Once you've implemented all the changes you decided to address, you need to respond to the comments, in the comment thread, to let the reviewer know that you have addressed the feedback and what you did.

```bash
# Reply to a specific review comment
uv run scripts/gh_pr.py reply owner/repo 456 \
  "[AUTOMATED] Done - moved the validation into a helper function as suggested."
```

If you have a general comment to address, you can reply in a general PR comment.

```bash
# Add a general PR comment (not tied to specific line)
uv run scripts/gh_pr.py comment owner/repo 123 \
  "[AUTOMATED] Addressed all feedback - ready for re-review."
```

VERY IMPORTANT: because you are using the Github CLI with the account of your human, you MUST start each comment with the following prefix:

```
[AUTOMATED]
```

If you respond to a comment mentioning that you fixed what the reviewer asked for, you should resolve the comment thread.

### 4. Resolve Comment Threads (when appropriate)

```bash
# Resolve a thread by comment ID
uv run scripts/gh_pr.py resolve owner/repo 123 --comment-id 456

# Unresolve a thread by comment ID
uv run scripts/gh_pr.py resolve owner/repo 123 --comment-id 456 --unresolve
```

### 5. Request Re-review

```bash
# After addressing all comments
uv run scripts/gh_pr.py reviewers owner/repo 123 --add "original-reviewer"
```

---

## Scripts Reference

This skill includes Python scripts in `scripts/` that wrap GitHub API operations. Run them with `uv`:

### Quick Reference

| Task             | Command                                                                     |
| ---------------- | --------------------------------------------------------------------------- |
| Fetch issue      | `uv run scripts/gh_pr.py issue owner/repo 42`                               |
| Create PR        | `uv run scripts/gh_pr.py create owner/repo --title "..." --body "..."`      |
| View PR          | `uv run scripts/gh_pr.py view owner/repo 123`                               |
| List PRs         | `uv run scripts/gh_pr.py list owner/repo`                                   |
| Check PR status  | `uv run scripts/gh_pr.py checks owner/repo 123`                             |
| Add reviewers    | `uv run scripts/gh_pr.py reviewers owner/repo 123 --add "user"`             |
| Merge PR         | `uv run scripts/gh_pr.py merge owner/repo 123`                              |
| Get comments     | `uv run scripts/gh_pr.py comments owner/repo 123`                           |
| Reply to comment | `uv run scripts/gh_pr.py reply owner/repo 456 "[AUTOMATED] message"`        |
| Resolve thread   | `uv run scripts/gh_pr.py resolve owner/repo 123 --comment-id 456`           |
| General comment  | `uv run scripts/gh_pr.py comment owner/repo 123 "[AUTOMATED] message"`      |


### Usage Examples

```bash
# Fetch issue details (use this for proper authentication)
uv run scripts/gh_pr.py issue owner/repo 42

# Create a PR
uv run scripts/gh_pr.py create owner/repo --title "feat: add feature" --body "Description"

# Create draft PR
uv run scripts/gh_pr.py create owner/repo --title "wip: new feature" --body "WIP" --draft

# View PR details
uv run scripts/gh_pr.py view owner/repo 123

# List open PRs
uv run scripts/gh_pr.py list owner/repo

# List your PRs
uv run scripts/gh_pr.py list owner/repo --author "myusername"

# Check CI status
uv run scripts/gh_pr.py checks owner/repo 123

# Get actionable review comments
uv run scripts/gh_pr.py comments owner/repo 123 --actionable

# Reply to a comment
uv run scripts/gh_pr.py reply owner/repo 456 "[AUTOMATED] Fixed!"

# Resolve a thread by comment ID
uv run scripts/gh_pr.py resolve owner/repo 123 --comment-id 456

# Merge PR with squash
uv run scripts/gh_pr.py merge owner/repo 123 --method squash

# Add reviewers
uv run scripts/gh_pr.py reviewers owner/repo 123 --add "user1,user2"
```
