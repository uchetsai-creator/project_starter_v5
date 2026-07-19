#!/usr/bin/env python3
"""Write one session-boundary row to .ai/telemetry/task-run.json.

Called by adapters/claude/stop-hook.sh on Claude Code session end.

Usage:
    python3 telemetry_writer.py --task TASK_NAME --adapter ADAPTER \
        --orch-state ORCH_STATE_FILE [--output TASK_RUN_FILE] [--ts TIMESTAMP]
"""
import argparse
import json
import os
import sys
from datetime import datetime, timezone


def _parse_args():
    p = argparse.ArgumentParser(description="Write telemetry row to task-run.json")
    p.add_argument("--task", required=True, help="Task name from current-state.md")
    p.add_argument("--adapter", required=True, help="Adapter name (e.g. claude)")
    p.add_argument("--orch-state", required=True, dest="orch_state",
                   help="Path to .ai/telemetry/.orchestrator_runs.json")
    p.add_argument("--output", default=None,
                   help="Path to task-run.json (default: .ai/telemetry/task-run.json)")
    p.add_argument("--ts", default=None,
                   help="ISO-8601 UTC timestamp (default: now)")
    return p.parse_args()


def _read_orchestrator_runs(orch_state_file: str, task_name: str) -> int:
    if not os.path.exists(orch_state_file):
        return 0
    try:
        state = json.loads(open(orch_state_file).read())
        if state.get("task") == task_name:
            return state.get("runs", 0)
    except Exception as e:
        print(f"telemetry error: {e}", file=sys.stderr, flush=True)
    return 0


def _read_existing_rows(task_run_file: str) -> list:
    if not os.path.exists(task_run_file):
        return []
    try:
        rows = json.loads(open(task_run_file).read())
        if isinstance(rows, list):
            return rows
    except Exception as e:
        print(f"telemetry error: {e}", file=sys.stderr, flush=True)
    return []


def main():
    args = _parse_args()

    ts = args.ts or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    output = args.output or os.path.join(".ai", "telemetry", "task-run.json")

    os.makedirs(os.path.dirname(os.path.abspath(output)), exist_ok=True)

    orchestrator_runs = _read_orchestrator_runs(args.orch_state, args.task)
    rows = _read_existing_rows(output)

    rows.append({
        "ts": ts,
        "task": args.task,
        "adapter": args.adapter,
        "orchestrator_runs": orchestrator_runs,
    })

    with open(output, "w") as f:
        json.dump(rows, f, indent=2)


if __name__ == "__main__":
    main()
