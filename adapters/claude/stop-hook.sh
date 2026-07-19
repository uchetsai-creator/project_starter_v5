#!/usr/bin/env bash
# Called by Claude Code Stop hook on session end.
# Writes .ai/telemetry/task-run.json row (session boundary tracking).
# Does NOT write to task-log.md — that file records completed-task verification
# results only and is written during task closeout, not on every session end.
#
# Install: add to .claude/settings.json:
#   { "hooks": { "Stop": [{ "matcher": "", "hooks": [{ "type": "command", "command": "bash adapters/claude/stop-hook.sh" }] }] } }
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
CURRENT_STATE="$PROJECT_ROOT/docs/current-state.md"
TELEMETRY_DIR="$PROJECT_ROOT/.ai/telemetry"
TASK_RUN_FILE="$TELEMETRY_DIR/task-run.json"
ORCH_STATE_FILE="$TELEMETRY_DIR/.orchestrator_runs.json"

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

TASK_NAME="(unknown)"
if [[ -f "$CURRENT_STATE" ]]; then
    TASK_NAME=$(grep -m1 '^\*\*Task:\*\*' "$CURRENT_STATE" 2>/dev/null \
        | sed 's/\*\*Task:\*\* *//' | tr -d '\r' || true)
    [[ -z "$TASK_NAME" ]] && TASK_NAME="(unknown)"
fi

# Write telemetry row
mkdir -p "$TELEMETRY_DIR"
python3 "$(dirname "$0")/telemetry_writer.py" \
    --task "$TASK_NAME" \
    --adapter claude \
    --orch-state "$ORCH_STATE_FILE" \
    --output "$TASK_RUN_FILE" \
    --ts "$TIMESTAMP"
