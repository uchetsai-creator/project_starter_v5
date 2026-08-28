#!/usr/bin/env python3
"""Records the user's per-session answer to the Learning Checkpoint enforcement
prompt (see .project-starter.yml -> checkpoint_enforcement: session-prompt).

This is not a hook -- it's a small CLI the *agent* runs (via its Bash tool) right after
it actually asks the user the question that adapters/claude/session-start-hook.sh
injected as SessionStart additionalContext. That message includes the current
session_id so the agent can pass it back verbatim here; pretooluse_scope_guard.py then
reads the same file to decide whether to mechanically enforce for this session.

Usage:
    python3 adapters/claude/record_checkpoint_choice.py --session-id SID --enabled true|false
"""
from __future__ import annotations

import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import checkpoint_session_state as state  # noqa: E402


def _parse_bool(value: str) -> bool:
    if value.strip().lower() in ("true", "y", "yes", "1"):
        return True
    if value.strip().lower() in ("false", "n", "no", "0"):
        return False
    raise argparse.ArgumentTypeError(f"expected true/false, got {value!r}")


def main() -> None:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--session-id", required=True, dest="session_id")
    p.add_argument("--enabled", required=True, type=_parse_bool)
    p.add_argument("--cwd", default=".")
    args = p.parse_args()

    state.write_choice(args.session_id, args.enabled, cwd=args.cwd)
    mode = "ENABLED (mechanically enforced by pretooluse_scope_guard.py)" if args.enabled \
        else "disabled (conversational Checkpoint A/B only -- see learning-checkpoint Skill)"
    print(f"[OK] Learning Checkpoint enforcement {mode} for session {args.session_id}")


if __name__ == "__main__":
    main()
