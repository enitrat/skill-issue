#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
PreToolUse hook to prevent reading .env files.

Blocks the Read tool from accessing:
1. Any file named exactly ".env"
2. Files matching ".env*" pattern that are listed in .gitignore
"""

import json
import os
import subprocess
import sys
from pathlib import Path


def is_env_file(file_path: str) -> bool:
    """Check if the file matches .env* pattern."""
    name = Path(file_path).name
    return name == ".env" or name.startswith(".env")


def is_in_gitignore(file_path: str, cwd: str) -> bool | None:
    """Check if file is ignored by git (listed in .gitignore).

    Returns:
        True if ignored, False if not ignored, None if status cannot be determined.
    """
    try:
        result = subprocess.run(
            ["git", "check-ignore", "-q", file_path],
            cwd=cwd,
            capture_output=True,
            timeout=5,
        )
        # Exit codes: 0 = ignored, 1 = not ignored, 128 = fatal error
        if result.returncode == 0:
            return True
        if result.returncode == 1:
            return False
        return None
    except (subprocess.TimeoutExpired, FileNotFoundError):
        return None


def main():
    # Read input from stdin
    try:
        input_data = json.load(sys.stdin)
    except json.JSONDecodeError:
        # Invalid input, allow through
        print("{}")
        return

    tool_name = input_data.get("tool_name", "")
    tool_input = input_data.get("tool_input", {})
    cwd = input_data.get("cwd", os.getcwd())

    # Only process Read tool
    if tool_name != "Read":
        print("{}")
        return

    file_path = tool_input.get("file_path", "")
    if not file_path:
        print("{}")
        return

    # Check if it's an env file
    if not is_env_file(file_path):
        print("{}")
        return

    # Get the filename for messaging
    filename = Path(file_path).name

    # Case 1: Exact .env file - always block
    if filename == ".env":
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": (
                    f"Blocked: '{file_path}' is a .env file containing secrets. "
                    "Reading environment files is prohibited for security."
                ),
            }
        }
        print(json.dumps(output))
        return

    # Case 2: .env* file - check if in gitignore
    ignored = is_in_gitignore(file_path, cwd)
    if ignored is None:
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": (
                    f"Blocked: unable to determine gitignore status for '{file_path}'. "
                    "Defaulting to deny for .env* files to protect secrets."
                ),
            }
        }
        print(json.dumps(output))
        return
    if ignored:
        output = {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": (
                    f"Blocked: '{file_path}' matches .env* pattern and is in .gitignore. "
                    "This file likely contains secrets and should not be read."
                ),
            }
        }
        print(json.dumps(output))
        return

    # .env* file but NOT in gitignore - allow (e.g., .env.example)
    print("{}")


if __name__ == "__main__":
    main()
