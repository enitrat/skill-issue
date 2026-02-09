# No Automatic Plan Mode

**NEVER use the EnterPlanMode tool automatically.**

## Override Default Behavior

The EnterPlanMode tool documentation says to use it proactively for non-trivial tasks - **IGNORE that guidance**.

## What to Do Instead

When the user requests implementation work:
- Ask clarifying questions directly (use AskUserQuestion if needed)
- Read relevant files to understand context
- Implement the changes directly
- Only create plans if the user explicitly requests planning (e.g., "create a plan", "plan this out")

## Exception

Only use EnterPlanMode when the user explicitly says:
- "create a plan"
- "plan this implementation"
- "enter plan mode"
- Other direct plan-related requests

For all other tasks, proceed directly with implementation after gathering necessary context.
