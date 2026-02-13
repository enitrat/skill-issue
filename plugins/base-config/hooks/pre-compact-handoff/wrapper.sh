#!/bin/bash
set -e
HOOK_DIR="$(cd "$(dirname "$0")" && pwd)"
cat | uv run "$HOOK_DIR/hook.py"
