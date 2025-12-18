# Handling Reviewer Comments

Code review comments critique the code, not the author. Approach reviews as collaborative problem-solving.

## Core Principles

### Fix the Code, Not Just Explain

When reviewers don't understand something, clarify the code itself first - not the review thread. Future readers face the same confusion.

**Instead of**: Long explanation in review comment
**Do**: Add code comment, rename for clarity, or refactor

### Don't Take It Personally

Reviews maintain codebase quality. Interpret constructive intent even when tone is terse. Never respond in anger - step away if needed.

### Think Collaboratively

Before disagreeing:
1. Ensure you understand what's being requested
2. Ask for clarification if uncertain
3. Discuss trade-offs with technical reasoning

## Response Patterns

### Implementing Feedback

When the suggestion is valid:

```
Done - moved the validation into a helper function as suggested.
```

```
Good catch! Fixed the null check and added a test case for this edge case.
```

### Seeking Clarification

When you don't understand:

```
Could you clarify what you mean by "more defensive"? Are you concerned
about null inputs, or about the external API changing its response format?
```

```
I want to make sure I address this correctly - are you suggesting we
change the algorithm, or just add documentation about the current behavior?
```

### Respectful Disagreement

When you disagree:

```
I considered that approach but chose X because [technical reasoning].
The trade-off is [downside], but I think [benefit] outweighs it here.
Happy to discuss further or try your approach if you feel strongly.
```

```
This is intentional - [explanation]. I added a comment explaining the
reasoning. Let me know if you think there's a better way to handle this.
```

### Declining (Out of Scope)

When the request is out of scope:

```
Agreed this could be improved, but I'd prefer to keep this PR focused
on [current scope]. I've created #123 to track this separately.
```

```
That's a good suggestion for a broader refactor. For this bug fix,
I'd like to keep changes minimal. Want me to open a follow-up issue?
```

## Workflow

1. **Read all comments** before responding - some may be related
2. **Batch related changes** into logical commits
3. **Reply to each comment** with action taken or reasoning
4. **Push changes** before marking conversations resolved
5. **Request re-review** when all feedback is addressed

## Resolving Conflicts

If consensus isn't reached:
1. Re-read the reviewer's concern - are you missing something?
2. Propose a concrete compromise
3. Involve a third party if needed
4. Defer to team standards or style guides

Courtesy and respect matter throughout disagreements.
