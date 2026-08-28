"""Tests for adapters/claude/checkpoint_session_state.py — the shared per-session
state used by pretooluse_scope_guard.py's `checkpoint_enforcement: session-prompt`
mode and record_checkpoint_choice.py.
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "adapters" / "claude"))

import checkpoint_session_state as s  # noqa: E402


def test_no_state_file_is_unanswered(tmp_path):
    assert s.read_choice("session-a", str(tmp_path)) is None


def test_empty_session_id_is_unanswered(tmp_path):
    s.write_choice("session-a", True, cwd=str(tmp_path))
    assert s.read_choice("", str(tmp_path)) is None


def test_write_then_read_same_session_returns_choice(tmp_path):
    s.write_choice("session-a", True, cwd=str(tmp_path))
    assert s.read_choice("session-a", str(tmp_path)) is True

    s.write_choice("session-b", False, cwd=str(tmp_path))
    assert s.read_choice("session-b", str(tmp_path)) is False


def test_different_session_id_is_unanswered(tmp_path):
    s.write_choice("session-a", True, cwd=str(tmp_path))
    assert s.read_choice("session-b", str(tmp_path)) is None


def test_corrupt_state_file_is_unanswered(tmp_path):
    state_dir = tmp_path / "logs" / "telemetry"
    state_dir.mkdir(parents=True)
    (state_dir / "checkpoint-session-choices.json").write_text("not json", encoding="utf-8")
    assert s.read_choice("session-a", str(tmp_path)) is None


def test_write_choice_creates_parent_dirs(tmp_path):
    s.write_choice("session-a", True, cwd=str(tmp_path))
    expected = tmp_path / "logs" / "telemetry" / "checkpoint-session-choices.json"
    assert expected.exists()
