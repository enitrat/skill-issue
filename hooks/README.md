# Claude Code Hooks

Custom hooks for Claude Code that extend or restrict its behavior.

## Available Hooks

| Hook | Type | Description |
|------|------|-------------|
| [env-protection](./env-protection/) | PreToolUse | Prevents reading `.env` files with secrets |

## Hook Types

- **PreToolUse** - Runs before a tool executes, can block/modify
- **PostToolUse** - Runs after a tool completes, can provide feedback
- **UserPromptSubmit** - Runs when user sends a prompt, can inject context
- **SessionStart** - Runs when a session begins

## Installation

Hooks can be installed automatically using `tools/skills-sync`, or manually registered in Claude Code's `settings.json`:

- **Automatic**: Run `tools/skills-sync` - copies hooks to `~/.claude/hooks/synced/` and registers them in `~/.claude/settings.json`
- **Manual (project-level)**: `.claude/settings.json` in your project
- **Manual (global)**: `~/.claude/settings.json`

### Automatic Sync with skills-sync

Each hook directory must contain a `hook.json` config file:

```json
{
  "event": "PreToolUse",
  "matcher": "Read",
  "timeout": 10
}
```

| Field | Required | Description |
|-------|----------|-------------|
| `event` | Yes | Hook event: `PreToolUse`, `PostToolUse`, `UserPromptSubmit`, `SessionStart`, etc. |
| `matcher` | No | Tool pattern to match (regex supported): `Read`, `Edit\|Write`, `Bash`, etc. |
| `timeout` | No | Timeout in seconds (default: 60) |

Run the sync:
```bash
tools/skills-sync           # Sync skills and hooks
tools/skills-sync --dry-run # Preview changes
```

The sync will:
- Copy hook files to `~/.claude/hooks/synced/<hook-name>/`
- Register the hook in `~/.claude/settings.json` without duplicating or removing existing hooks
- Skip hooks that are already up-to-date

See each hook's README for manual installation instructions.

## Creating New Hooks

1. Create a directory: `hooks/<hook-name>/`
2. Write the hook script (Python with uv, or TypeScript with bun)
3. Create a shell wrapper that pipes stdin to the script
4. Add a README with installation instructions

### Python Pattern (with uv)

```python
#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///

import json
import sys

def main():
    input_data = json.load(sys.stdin)
    # Process and decide
    output = {}  # or {"decision": "block", "reason": "..."}
    print(json.dumps(output))

if __name__ == "__main__":
    main()
```

### Shell Wrapper

```bash
#!/bin/bash
set -e
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cat | uv run "$SCRIPT_DIR/hook.py"
```
