import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))
from _workflow_utils import _read_task_type_from_current_state, _resolve_task_type


# ---------------------------------------------------------------------------
# _read_task_type_from_current_state
# ---------------------------------------------------------------------------

def test_reads_task_type_from_content(tmp_path):
    f = tmp_path / "current-state.md"
    f.write_text("# Task\n\n**Task Type:** pipeline-stage\n\nSome other content.\n")
    assert _read_task_type_from_current_state(f) == "pipeline-stage"


def test_returns_none_when_file_absent(tmp_path):
    assert _read_task_type_from_current_state(tmp_path / "missing.md") is None


def test_returns_none_when_no_task_type_header(tmp_path):
    f = tmp_path / "current-state.md"
    f.write_text("# Task\n\nNo task type field here.\n")
    assert _read_task_type_from_current_state(f) is None


def test_returns_none_for_placeholder_task_type(tmp_path):
    f = tmp_path / "current-state.md"
    f.write_text("**Task Type:** [task-type]\n")
    assert _read_task_type_from_current_state(f) is None


def test_returns_none_for_bare_placeholder(tmp_path):
    f = tmp_path / "current-state.md"
    f.write_text("**Task Type:** task-type\n")
    assert _read_task_type_from_current_state(f) is None


def test_reads_bracketed_real_value(tmp_path):
    """[pipeline-stage] → strips brackets → returns pipeline-stage (not a placeholder)."""
    f = tmp_path / "current-state.md"
    f.write_text("**Task Type:** [pipeline-stage]\n")
    assert _read_task_type_from_current_state(f) == "pipeline-stage"


# ---------------------------------------------------------------------------
# _resolve_task_type
# ---------------------------------------------------------------------------

def test_override_wins_over_everything(tmp_path):
    f = tmp_path / "current-state.md"
    f.write_text("**Task Type:** bug-fix\n")
    cfg = {"task_type": "sprint-end"}
    assert _resolve_task_type(cfg, f, "feature") == "feature"


def test_current_state_wins_over_yml(tmp_path):
    f = tmp_path / "current-state.md"
    f.write_text("**Task Type:** pipeline-stage\n")
    cfg = {"task_type": "sprint-end"}
    assert _resolve_task_type(cfg, f, None) == "pipeline-stage"


def test_yml_fallback_when_no_state(tmp_path):
    f = tmp_path / "current-state.md"  # does not exist
    cfg = {"task_type": "sprint-end"}
    assert _resolve_task_type(cfg, f, None) == "sprint-end"


def test_all_none_returns_none(tmp_path):
    f = tmp_path / "current-state.md"  # does not exist
    cfg = {}
    assert _resolve_task_type(cfg, f, None) is None


def test_empty_string_yml_returns_none(tmp_path):
    f = tmp_path / "current-state.md"  # does not exist
    cfg = {"task_type": ""}
    assert _resolve_task_type(cfg, f, None) is None
