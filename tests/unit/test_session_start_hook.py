"""Tests for adapters/claude/session-start-hook.sh — the SessionStart nudge.

This is the mechanical follow-through on AGENTS.md -> Constitution -> "Unscoped New
Requirement": the rule only helps if the agent actually has it in front of mind each
session, not just somewhere in a file it may or may not have read closely. The hook
re-surfaces the current-state.md scoping state as SessionStart hookSpecificOutput.
additionalContext every session, instead of relying on CLAUDE.md's `@AGENTS.md` load
having put that specific section in attention.

Never blocks (always exits 0) — it's a reminder, not a gate; the actual gate is the
Clarifying Questions Asked check in .githooks/pre-commit (see
test_pre_commit_clarifying_questions.py).

Runs the real script via subprocess, matching the pre-commit test suite's approach.
"""
import json
import subprocess
from pathlib import Path

import pytest

from tests.conftest import find_posix_bash

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
HOOK = REPO_ROOT / "adapters" / "claude" / "session-start-hook.sh"

_BASH = find_posix_bash()
pytestmark = pytest.mark.skipif(_BASH is None, reason="bash not found on PATH")


def _run(cwd: Path) -> subprocess.CompletedProcess:
    assert _BASH is not None  # module-level skipif guarantees this by the time we get here
    return subprocess.run(
        [_BASH, str(HOOK)], cwd=cwd, capture_output=True, text=True,
        encoding="utf-8", errors="replace", input="{}",
    )


def test_missing_current_state_produces_no_output(tmp_path):
    result = _run(tmp_path)
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_placeholder_task_produces_reminder(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "current-state.md").write_text(
        "**Task:** [Task name, e.g., BE Order API]\n", encoding="utf-8",
    )
    result = _run(tmp_path)
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    ctx = payload["hookSpecificOutput"]["additionalContext"]
    assert payload["hookSpecificOutput"]["hookEventName"] == "SessionStart"
    assert "no scoped Current Task" in ctx


def test_real_task_missing_cqa_produces_reminder(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "current-state.md").write_text(
        "**Task:** Build the order API\n", encoding="utf-8",
    )
    result = _run(tmp_path)
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    ctx = payload["hookSpecificOutput"]["additionalContext"]
    assert "Clarifying Questions Asked is unfilled" in ctx


def test_real_task_with_cqa_filled_is_silent(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "current-state.md").write_text(
        "**Task:** Build the order API\n\n**Clarifying Questions Asked:** Y\n",
        encoding="utf-8",
    )
    result = _run(tmp_path)
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_real_task_with_na_cqa_is_silent(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "current-state.md").write_text(
        "**Task:** Build the order API\n\n"
        "**Clarifying Questions Asked:** N/A -- pre-scoped in project-plan.md\n",
        encoding="utf-8",
    )
    result = _run(tmp_path)
    assert result.returncode == 0
    assert result.stdout.strip() == ""
