# env-protection Hook

Prevents Claude Code from reading `.env` files that may contain secrets.

## What It Does

This `PreToolUse` hook blocks the `Read` tool from accessing:

1. **Any file named `.env`** - Always blocked
2. **Files matching `.env*` pattern** - Blocked if listed in `.gitignore`

Files like `.env.example` that are NOT in `.gitignore` are allowed through (they typically contain example values, not secrets).

## Installation

### Option 1: Project-level (recommended)

Add to your project's `.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Read",
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/skill-issue/hooks/env-protection/wrapper.sh"
          }
        ]
      }
    ]
  }
}
```

### Option 2: Global (all projects)

Add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "Read",
        "hooks": [
          {
            "type": "command",
            "command": "/path/to/skill-issue/hooks/env-protection/wrapper.sh"
          }
        ]
      }
    ]
  }
}
```

Replace `/path/to/skill-issue` with the actual path to this repository.

## Requirements

- `uv` - Python package manager (the hook uses inline script dependencies)
- `git` - For checking `.gitignore` status

## Testing

Test the hook manually:

```bash
# Should block - .env file
echo '{"tool_name":"Read","tool_input":{"file_path":"/project/.env"},"cwd":"/project"}' | \
  ./wrapper.sh

# Should block - .env.local in gitignore (if your gitignore has .env*)
echo '{"tool_name":"Read","tool_input":{"file_path":"/project/.env.local"},"cwd":"/project"}' | \
  ./wrapper.sh

# Should allow - .env.example not in gitignore
echo '{"tool_name":"Read","tool_input":{"file_path":"/project/.env.example"},"cwd":"/project"}' | \
  ./wrapper.sh

# Should allow - not an env file
echo '{"tool_name":"Read","tool_input":{"file_path":"/project/config.json"},"cwd":"/project"}' | \
  ./wrapper.sh
```

## How It Works

1. Hook receives JSON with `tool_name`, `tool_input`, and `cwd`
2. Checks if the tool is `Read` and the file matches `.env*` pattern
3. For exact `.env` files: always blocks
4. For `.env*` files: runs `git check-ignore` to see if in gitignore
5. Returns `permissionDecision: "deny"` with reason if blocked
