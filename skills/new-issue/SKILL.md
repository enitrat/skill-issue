---
name: new-issue
description: Guide structured GitHub issue creation using Why/What/How format. Use when creating bug reports, feature requests, or task issues that clearly communicate context, scope, and implementation direction.
---

# Issue Creation Skill

This skill provides a structured approach to writing GitHub issues that communicate context, scope, and direction clearly.

## The Why/What/How Framework

Every issue should answer three questions for the reader:
- **Why** does this matter?
- **What** exactly needs to happen?
- **How** should it be approached?

This framework ensures issues are actionable and provide enough context for anyone picking them up.

---

## Issue Template

### Why

Explain the background and motivation:

- **Current state**: What exists today? How does it work?
- **Bottleneck/Problem**: What specific issue or limitation was identified?
- **Value**: Why is solving this valuable? What insights, metrics, or improvements does it unlock?

```markdown
## Why

Currently, [describe current state/behavior].

This causes [specific problem or bottleneck], which [impact on users/system/workflow].

Addressing this will [concrete benefit - improved metrics, unlocked capabilities, better UX].
```

### What

Define the scope concretely:

- **Specific deliverable**: What exactly needs to be built, fixed, or changed?
- **Boundaries**: What is explicitly out of scope?
- **Success criteria**: How do we know when this is done?

```markdown
## What

[Verb] [specific thing] to [achieve outcome].

Scope:
- [In scope item 1]
- [In scope item 2]

Out of scope:
- [Explicitly excluded item]
```

### How

Provide implementation direction:

- **Approach**: High-level strategy or pattern to follow
- **Key files/components**: Where changes will likely occur
- **Architecture sketch**: Skeleton of the solution structure (not implementation details)

```markdown
## How

Approach: [brief strategy - e.g., "Extend existing X pattern", "Add new Y component"]

Key areas:
1. [Component/file] - [what changes here]
2. [Component/file] - [what changes here]

Skeleton:
- [High-level step 1]
- [High-level step 2]
- [Integration point]
```

---

## Acceptance Criteria

Keep acceptance criteria focused on integration and observable behavior:

```markdown
## Acceptance Criteria

- [ ] [Observable behavior or state that confirms completion]
- [ ] [Integration with existing system works as expected]
- [ ] [Edge case or error condition handled]
```

Tips:
- Write criteria that can be verified by running the system
- Focus on "what" not "how" - avoid implementation details
- Include integration points with existing functionality

---

## Testing Plan

Keep testing plans succinct and focused on verification:

```markdown
## Testing Plan

- [ ] [How to manually verify the change]
- [ ] [Key integration scenario to test]
- [ ] [Regression check if applicable]
```

Tips:
- Tests added should integrate within existing test architeture
- Prioritize integration testing over isolated unit tests
- Include the command or steps to run verification
- Note any existing tests that should continue passing

---

## Creating the Issue (gh CLI)

### Basic Creation

```bash
gh issue create \
  --title "Brief, descriptive title" \
  --body "$(cat <<'EOF'
## Why

[Background and motivation]

## What

[Specific scope and deliverable]

## How

[Implementation direction]

## Acceptance Criteria

- [ ] [Criterion 1]
- [ ] [Criterion 2]

## Testing Plan

- [ ] [Verification step]
EOF
)"
```

### With Labels and Assignment

```bash
gh issue create \
  --title "Add caching layer to API responses" \
  --body "$(cat <<'EOF'
## Why

API response times average 800ms due to repeated database queries.

## What

Add response caching for GET endpoints with configurable TTL.

## How

1. Add Redis client configuration
2. Create caching middleware
3. Apply to read-only endpoints

## Acceptance Criteria

- [ ] GET /users returns cached response on subsequent calls
- [ ] Cache invalidates on relevant mutations
- [ ] TTL configurable via environment variable

## Testing Plan

- [ ] Verify cache hit/miss headers in response
- [ ] Test invalidation after POST/PUT/DELETE
EOF
)" \
  --label "enhancement" \
  --label "performance" \
  --assignee "@me"
```

### From a File

For longer issues, write to a file first:

```bash
# Write issue content to file
cat > /tmp/issue-body.md <<'EOF'
## Why
...
EOF

# Create issue from file
gh issue create \
  --title "Issue title" \
  --body-file /tmp/issue-body.md

# Clean up
rm /tmp/issue-body.md
```

### Adding to a Project

```bash
gh issue create \
  --title "Issue title" \
  --body "..." \
  --project "Project Name"
```

### Linking to Milestone

```bash
gh issue create \
  --title "Issue title" \
  --body "..." \
  --milestone "v2.0"
```

---

## Linking Issues

### Link to Parent Issue (Sub-issues)

GitHub supports sub-issues for creating parent/child relationships. Add a sub-issue to an existing parent:

```bash
# Add issue #42 as a sub-issue of parent issue #10
gh issue develop 42 --issue 10

# Or use the API directly
gh api repos/{owner}/{repo}/issues/10/sub_issues \
  -f sub_issue_id={sub_issue_node_id}
```

### Reference Parent in Body

Include a reference to the parent issue in the issue body:

```bash
gh issue create \
  --title "Implement caching middleware" \
  --body "$(cat <<'EOF'
Parent: #10

## Why
...
EOF
)"
```

### Link Issues After Creation

Link two existing issues:

```bash
# Get the node IDs for both issues
PARENT_ID=$(gh issue view 10 --json id --jq '.id')
CHILD_ID=$(gh issue view 42 --json id --jq '.id')

# Create the sub-issue relationship via GraphQL
gh api graphql -f query='
  mutation($parentId: ID!, $childId: ID!) {
    addSubIssue(input: {issueId: $parentId, subIssueId: $childId}) {
      issue {
        number
      }
    }
  }
' -f parentId="$PARENT_ID" -f childId="$CHILD_ID"
```

### Close Issue via Commit

Reference the issue number in a commit message to auto-close:

```bash
git commit -m "Add caching middleware

Fixes #42"
```

Keywords that close issues: `fixes`, `closes`, `resolves` (followed by `#issue_number`)

### View Issue Relationships

```bash
# View issue details including linked issues
gh issue view 42

# View sub-issues of a parent
gh api repos/{owner}/{repo}/issues/10/sub_issues
```

