#!/usr/bin/env bash
# run.sh — Launch the Smithers workflow
#
# Usage:
#   ./run.sh               # Run (or resume) the workflow
#   SKIP_PHASES=phase-2-foo,phase-3-bar ./run.sh  # Skip specific phases

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$SCRIPT_DIR"
export SMITHERS_PROJECT="$SCRIPT_DIR/config.ts"

# Allow smithers to spawn Claude Code agents from within a Claude session
unset CLAUDECODE 2>/dev/null || true

echo "Smithers Workflow"
echo "  Dir:    $SCRIPT_DIR"
echo "  Config: $SMITHERS_PROJECT"
echo "  Skip:   ${SKIP_PHASES:-<none>}"
echo ""

# ── Check for runs that need attention (running or cancelled) ─────────────────
PENDING_JSON=$(bunx smithers list workflow.tsx --limit 20 2>/dev/null \
  | jq -c '[.[] | select(.status == "running" or .status == "cancelled")]' 2>/dev/null || echo "[]")

PENDING_COUNT=$(echo "$PENDING_JSON" | jq 'length')

if [[ "$PENDING_COUNT" -gt 0 ]]; then
  echo "Found $PENDING_COUNT run(s) that can be resumed:"
  echo ""

  echo "$PENDING_JSON" | jq -r '.[] | "  [\(.status)] \(.runId)  started \(.createdAtMs / 1000 | todate)"'
  echo ""

  while IFS= read -r run; do
    RUN_ID=$(echo "$run" | jq -r '.runId')
    STATUS=$(echo "$run" | jq -r '.status')
    STARTED=$(echo "$run" | jq -r '.createdAtMs / 1000 | todate')

    # Find the DB (named after workflowName in project config)
    DB_FILE=$(ls "$SCRIPT_DIR"/*.db 2>/dev/null | head -1 || echo "")
    LAST_ATTEMPT=""
    if [[ -n "$DB_FILE" ]]; then
      LAST_ATTEMPT=$(sqlite3 "$DB_FILE" \
        "SELECT node_id, state, attempt FROM _smithers_attempts \
         WHERE run_id = '$RUN_ID' ORDER BY started_at_ms DESC LIMIT 1;" 2>/dev/null || echo "")
    fi

    echo "  [$STATUS] $RUN_ID"
    echo "  Started : $STARTED"
    if [[ -n "$LAST_ATTEMPT" ]]; then
      LAST_NODE=$(echo "$LAST_ATTEMPT" | cut -d'|' -f1)
      LAST_STATE=$(echo "$LAST_ATTEMPT" | cut -d'|' -f2)
      LAST_ATTEMPT_N=$(echo "$LAST_ATTEMPT" | cut -d'|' -f3)
      echo "  Last    : $LAST_NODE  ($LAST_STATE, attempt $LAST_ATTEMPT_N)"
    fi
    echo ""
    read -r -p "  [r]esume  [d]iscard  [s]kip → " choice </dev/tty
    echo ""

    case "$(echo "$choice" | tr '[:upper:]' '[:lower:]')" in
      r)
        echo "Resuming $RUN_ID..."
        exec bunx smithers resume workflow.tsx --run-id "$RUN_ID"
        ;;
      d)
        if [[ "$STATUS" == "running" ]]; then
          bunx smithers cancel workflow.tsx --run-id "$RUN_ID" 2>/dev/null || true
        fi
        if [[ -n "$DB_FILE" ]]; then
          sqlite3 "$DB_FILE" \
            "UPDATE _smithers_runs SET status = 'failed', finished_at_ms = strftime('%s','now') * 1000 \
             WHERE run_id = '$RUN_ID';" 2>/dev/null || true
        fi
        echo "  Discarded."
        ;;
      *)
        echo "  Skipped."
        ;;
    esac
  done < <(echo "$PENDING_JSON" | jq -c '.[]')
fi

# ── Start a new run ───────────────────────────────────────────────────────────
echo "Starting new run..."
bunx smithers run workflow.tsx
