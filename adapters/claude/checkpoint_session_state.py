"""Shared read/write helpers for the per-session Learning Checkpoint enforcement
choice (see .project-starter.yml -> checkpoint_enforcement: session-prompt).

Used by both session-start-hook.sh (via record_checkpoint_choice.py, invoked by the
agent after it actually asks the user) and pretooluse_scope_guard.py (reads the choice
to decide whether to enforce for the current session). State lives in
logs/telemetry/checkpoint-session-choices.json (gitignored -- see .gitignore's `logs/`
entry) and holds only the single most-recent choice: a session_id mismatch always means
"this session has not answered yet", so there is nothing to gain from retaining history,
and always starting unanswered on a fresh session_id is the point (see checkpoint_enforcement:
session-prompt's doc comment in .project-starter.yml -- every session is asked again).
"""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from typing import Optional

DEFAULT_STATE_PATH = os.path.join("logs", "telemetry", "checkpoint-session-choices.json")


def read_choice(session_id: str, cwd: str, state_path: str = DEFAULT_STATE_PATH) -> Optional[bool]:
    """True/False if this exact session_id already answered this session; None if it
    hasn't (no file yet, a different/older session_id, or a corrupt file -- every
    failure mode here must resolve to "not yet answered", never to a stale answer)."""
    if not session_id:
        return None
    full_path = os.path.join(cwd, state_path)
    try:
        with open(full_path, encoding="utf-8") as f:
            state = json.load(f)
    except (OSError, json.JSONDecodeError):
        return None
    if state.get("session_id") != session_id:
        return None
    enabled = state.get("enabled")
    return enabled if isinstance(enabled, bool) else None


def write_choice(
    session_id: str, enabled: bool, cwd: str,
    state_path: str = DEFAULT_STATE_PATH, ts: Optional[str] = None,
) -> None:
    full_path = os.path.join(cwd, state_path)
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    with open(full_path, "w", encoding="utf-8") as f:
        json.dump({
            "session_id": session_id,
            "enabled": enabled,
            "ts": ts or datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        }, f, indent=2)
