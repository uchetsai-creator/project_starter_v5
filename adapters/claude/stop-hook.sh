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
python3 - "$TASK_RUN_FILE" "$ORCH_STATE_FILE" "$TIMESTAMP" "$TASK_NAME" <<'PYEOF'
import json, os, sys

task_run_file, orch_state_file, ts, task_name = sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4]

orchestrator_runs = 0
if os.path.exists(orch_state_file):
    try:
        state = json.loads(open(orch_state_file).read())
        if state.get('task') == task_name:
            orchestrator_runs = state.get('runs', 0)
    except Exception as e:
        print(f"telemetry error: {e}", file=sys.stderr, flush=True)

rows = []
if os.path.exists(task_run_file):
    try:
        rows = json.loads(open(task_run_file).read())
        if not isinstance(rows, list):
            rows = []
    except Exception as e:
        print(f"telemetry error: {e}", file=sys.stderr, flush=True)
        rows = []

rows.append({
    'ts': ts,
    'task': task_name,
    'adapter': 'claude',
    'orchestrator_runs': orchestrator_runs,
    'token_count': None,
})

with open(task_run_file, 'w') as f:
    json.dump(rows, f, indent=2)
PYEOF
