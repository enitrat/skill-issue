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
- **Stop** - Runs when Claude finishes responding
- **Notification** - Runs when Claude sends notifications
- **SessionStart** - Runs when a session begins

## Installation

These hooks are installed automatically when you install the `base-config` plugin:

```bash
/plugin marketplace add enitrat/skill-issue
/plugin install base-config@eni-skills
```

The hooks are configured in `hooks.json` and use `${CLAUDE_PLUGIN_ROOT}` for paths.

## Creating New Hooks

1. Create a directory: `hooks/<hook-name>/`
2. Write the hook script (Python with uv, or TypeScript with bun)
3. Create a shell wrapper that pipes stdin to the script
4. Register in `hooks/hooks.json`

### Python Pattern (with uv)

```python
#!/usr/bin/env -S uv run --script
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

### Register in hooks.json

```json
{
  "hooks": {
    "Stop": [
      {
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/hooks/<hook-name>/wrapper.sh",
            "timeout": 60
          }
        ]
      }
    ]
  }
}
```
