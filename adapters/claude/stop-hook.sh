#!/usr/bin/env bash
# Called by Claude Code Stop hook on session end.
# Appends one row to docs/task-log.md recording the session boundary.
#
# Install: add to .claude/settings.json:
#   { "hooks": { "Stop": [{ "matcher": "", "hooks": [{ "type": "command", "command": "bash adapters/claude/stop-hook.sh" }] }] } }
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
TASK_LOG="$PROJECT_ROOT/docs/task-log.md"
CURRENT_STATE="$PROJECT_ROOT/docs/current-state.md"

TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")

TASK_NAME="(unknown)"
if [[ -f "$CURRENT_STATE" ]]; then
    TASK_NAME=$(grep -m1 '^\*\*Task:\*\*' "$CURRENT_STATE" 2>/dev/null \
        | sed 's/\*\*Task:\*\* *//' | tr -d '\r' || true)
    [[ -z "$TASK_NAME" ]] && TASK_NAME="(unknown)"
fi

if [[ -f "$TASK_LOG" ]]; then
    printf "| %s | %s | session-end | — |\n" "$TIMESTAMP" "$TASK_NAME" >> "$TASK_LOG"
fi
