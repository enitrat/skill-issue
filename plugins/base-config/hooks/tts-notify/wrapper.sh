#!/bin/bash
# Shell wrapper for tts-notify hook
# Pipes stdin JSON to the Python hook script

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cat | uv run "$SCRIPT_DIR/hook.py"
