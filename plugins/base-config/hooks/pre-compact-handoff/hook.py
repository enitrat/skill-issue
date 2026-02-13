#!/usr/bin/env -S uv run
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""PreCompact hook that invokes /create_handoff instead of default compaction summary.

Reads PreCompact input from stdin and outputs a systemMessage instructing Claude
to run the /create_handoff workflow before context is lost to compaction.
"""

import json
import sys
from datetime import datetime, timezone


def main() -> None:
    raw = sys.stdin.read()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        data = {}

    trigger = data.get("trigger", "unknown")
    session_id = data.get("session_id", "unknown")

    now = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    system_message = (
        f"[PreCompact:{trigger}] Context compaction triggered at {now} (session: {session_id}).\n\n"
        "**IMPORTANT:** Before compaction proceeds, you MUST create a handoff document "
        "to preserve session context. Invoke the /create_handoff skill NOW.\n\n"
        "This replaces the default compaction summary. The handoff document will capture:\n"
        "- What was accomplished this session\n"
        "- Current state and blockers\n"
        "- Decisions made and rationale\n"
        "- Next steps for the resuming session\n\n"
        "After creating the handoff, compaction can proceed safely."
    )

    output = {
        "continue": True,
        "systemMessage": system_message,
    }
    print(json.dumps(output))


if __name__ == "__main__":
    main()
