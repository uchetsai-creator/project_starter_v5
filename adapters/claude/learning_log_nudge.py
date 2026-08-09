#!/usr/bin/env python3
"""SessionStart nudge: reminds about learning-log.md when a task was recently closed
out (docs/task-log.md committed) with no corresponding learning-log.md entry since.

Deliberately NOT a gate. learning-log.md's own header says it is "never checked by
any validator" -- turning a personal teach-back gap log into something graded creates
an incentive to write hollow entries just to pass, which defeats the point of the log
(Goodhart's law). This hook never blocks, never inspects entry content, and stays
silent whenever git history is unavailable or the signal is ambiguous -- it only makes
the absence of a reminder less likely, the same non-blocking role session-start-hook.sh
already plays for scoping.

Install: add to .claude/settings.json's SessionStart hooks array, alongside the
existing session-start-hook.sh entry:
  { "type": "command", "command": "python3 adapters/claude/learning_log_nudge.py" }
"""
from __future__ import annotations

import json
import os
import subprocess


def _last_commit_epoch(cwd: str, rel_path: str) -> int | None:
    try:
        result = subprocess.run(
            ["git", "log", "-1", "--format=%ct", "--", rel_path],
            cwd=cwd, capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=5,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    out = result.stdout.strip()
    return int(out) if out.isdigit() else None


def decide(cwd: str) -> str | None:
    """Pure-ish decision function: returns a reminder string, or None to stay silent."""
    if not os.path.isfile(os.path.join(cwd, "learning-log.md")):
        return None  # not part of this project's setup

    task_log_ts = _last_commit_epoch(cwd, "docs/task-log.md")
    if task_log_ts is None:
        return None  # no closed-out task committed yet -- nothing to check against

    learning_log_ts = _last_commit_epoch(cwd, "learning-log.md")
    if learning_log_ts is not None and learning_log_ts >= task_log_ts:
        return None  # learning-log.md already caught up with (or ahead of) the last closeout

    return (
        "The last committed docs/task-log.md entry has no learning-log.md entry since. "
        "If Checkpoint C.4's teach-back revealed a gap or named a pattern last task, log "
        "it now -- skip if teach-back went cleanly (see learning-log.md's own header)."
    )


def main() -> None:
    try:
        msg = decide(os.getcwd())
    except Exception:
        msg = None  # fail silent: this is a reminder, never a reason to break a session
    if msg:
        print(json.dumps({
            "hookSpecificOutput": {
                "hookEventName": "SessionStart",
                "additionalContext": msg,
            },
        }))


if __name__ == "__main__":
    main()
