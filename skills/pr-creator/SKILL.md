---
name: pr-creator
description: Guide PR authoring from creation through review completion. Use when creating pull requests, writing PR descriptions, responding to reviewer comments, or implementing review feedback. Covers the full PR lifecycle - creating PRs linked to issues, handling review comments (triaging, responding, implementing suggestions), and getting PRs merged.
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

```bash
# Basic PR creation
gh pr create \
  --title "feat(api): add caching to API responses" \
  --body "$(cat <<'EOF'
## Summary
- Add Redis-based caching for GET endpoints
- Implement cache invalidation on mutations

## Context
API response times average 800ms due to repeated database queries.
This reduces load and improves response times for cached routes.

## Test Plan
- [ ] Verify cache headers in responses
- [ ] Test invalidation after mutations

Closes #42
EOF
)"

# Link to issue via keywords in body: Closes #N, Fixes #N, Resolves #N
```

### 4. Add Labels/Reviewers

```bash
gh pr create \
  --title "Title" \
  --body "..." \
  --label "enhancement" \
  --reviewer "username" \
  --assignee "@me"
```

## Handling Review Comments

When reviews come in, follow this workflow. See [references/handling-reviews.md](references/handling-reviews.md) for detailed guidance on reviewer interactions.

### 1. Fetch Review Comments

```bash
# Get PR number first
PR_NUMBER=$(gh pr view --json number --jq '.number')

# Fetch all review comments
gh api repos/{owner}/{repo}/pulls/$PR_NUMBER/comments

# Fetch review summaries (approve/request changes/comment)
gh api repos/{owner}/{repo}/pulls/$PR_NUMBER/reviews

# Pretty-print pending comments for triage
gh api repos/{owner}/{repo}/pulls/$PR_NUMBER/comments \
  --jq '.[] | {id: .id, path: .path, line: .line, body: .body, user: .user.login}'
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

### 3. Respond to Comments

VERY IMPORTANT: because you are using the Github CLI with the account of your human, you MUST start each comment with the following prefix:

```
[AUTOMATED]
```

```bash
# Reply to a specific review comment. Prefer this if you're addressing a specific comment.
gh api repos/{owner}/{repo}/pulls/$PR_NUMBER/comments/$COMMENT_ID/replies \
  -f body="[AUTOMATED] Done - moved the validation into a helper function as suggested."

# Add a general PR comment (not tied to specific line)
gh pr comment $PR_NUMBER --body "[AUTOMATED] Addressed all feedback - ready for re-review."
```

### 4. Implement Suggestions

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

### 5. Request Re-review

```bash
# After addressing all comments
gh pr edit $PR_NUMBER --add-reviewer "original-reviewer"
```

## GH CLI Quick Reference

| Task             | Command                                                                     |
| ---------------- | --------------------------------------------------------------------------- |
| Create PR        | `gh pr create --title "..." --body "..."`                                   |
| View PR          | `gh pr view [number]`                                                       |
| List PRs         | `gh pr list`                                                                |
| Check PR status  | `gh pr checks`                                                              |
| Add reviewers    | `gh pr edit --add-reviewer "user"`                                          |
| Merge PR         | `gh pr merge [number]`                                                      |
| Get comments     | `gh api repos/{owner}/{repo}/pulls/{n}/comments`                            |
| Reply to comment | `gh api repos/{owner}/{repo}/pulls/{n}/comments/{id}/replies -f body="..."` |
