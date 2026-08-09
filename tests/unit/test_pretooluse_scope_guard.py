"""Tests for adapters/claude/pretooluse_scope_guard.py.

This is the generation-time counterpart to .githooks/pre-commit's "Unscoped
source-change guard" (tests/unit/test_pre_commit_unscoped_source_guard.py) -- same
rule, enforced before the agent writes anything instead of at commit time. Tests call
the pure `decide()` function directly (fast, no subprocess) plus one end-to-end
subprocess test to confirm the stdin/stdout JSON contract actually works.
"""
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "adapters" / "claude"))

import pretooluse_scope_guard as guard  # noqa: E402


def _write_project(tmp_path: Path, project_type: str = "web-app",
                    current_state: str | None = None) -> Path:
    (tmp_path / ".project-starter.yml").write_text(
        f"project_type: {project_type}\ndocs_path: docs/\n", encoding="utf-8",
    )
    if current_state is not None:
        docs = tmp_path / "docs"
        docs.mkdir(exist_ok=True)
        (docs / "current-state.md").write_text(current_state, encoding="utf-8")
    return tmp_path


_SCOPED_Y = "## Current Task\n\n**Task:** Build the order API\n\n**Clarifying Questions Asked:** Y\n"
_SCOPED_NA = "## Current Task\n\n**Task:** Build the order API\n\n**Clarifying Questions Asked:** N/A — pre-scoped\n"
_PLACEHOLDER_TASK = "## Current Task\n\n**Task:** [Task name, e.g., BE Order API]\n"
_TASK_NO_CQA = "## Current Task\n\n**Task:** Build the order API\n"
_TASK_INVALID_CQA = "## Current Task\n\n**Task:** Build the order API\n\n**Clarifying Questions Asked:** N\n"


def _payload(tool_name: str, file_path: str) -> dict:
    return {"tool_name": tool_name, "tool_input": {"file_path": file_path}}


def test_non_gated_tool_is_allowed(tmp_path):
    project = _write_project(tmp_path)
    decision, _ = guard.decide(_payload("Read", "src/app.py"), str(project))
    assert decision == "allow"


def test_unset_project_type_is_allowed(tmp_path):
    (tmp_path / ".project-starter.yml").write_text(
        "project_type: [your-project-type]\ndocs_path: docs/\n", encoding="utf-8",
    )
    decision, _ = guard.decide(_payload("Write", "src/app.py"), str(tmp_path))
    assert decision == "allow"


def test_missing_config_is_allowed(tmp_path):
    decision, _ = guard.decide(_payload("Write", "src/app.py"), str(tmp_path))
    assert decision == "allow"


def test_doc_path_edit_is_allowed_even_without_current_state(tmp_path):
    project = _write_project(tmp_path)
    decision, _ = guard.decide(_payload("Write", "docs/current-state.md"), str(project))
    assert decision == "allow"


def test_source_write_with_no_current_state_file_is_denied(tmp_path):
    project = _write_project(tmp_path)
    decision, reason = guard.decide(_payload("Write", "src/login.js"), str(project))
    assert decision == "deny"
    assert "does not exist yet" in reason


def test_source_write_with_placeholder_task_is_denied(tmp_path):
    project = _write_project(tmp_path, current_state=_PLACEHOLDER_TASK)
    decision, reason = guard.decide(_payload("Edit", "src/login.js"), str(project))
    assert decision == "deny"
    assert "no scoped Current Task" in reason


def test_source_write_with_task_but_no_cqa_is_denied(tmp_path):
    project = _write_project(tmp_path, current_state=_TASK_NO_CQA)
    decision, reason = guard.decide(_payload("Edit", "src/login.js"), str(project))
    assert decision == "deny"
    assert "Clarifying" in reason


def test_source_write_with_invalid_cqa_value_is_denied(tmp_path):
    project = _write_project(tmp_path, current_state=_TASK_INVALID_CQA)
    decision, reason = guard.decide(_payload("Edit", "src/login.js"), str(project))
    assert decision == "deny"


def test_source_write_with_scoped_task_y_is_allowed(tmp_path):
    project = _write_project(tmp_path, current_state=_SCOPED_Y)
    decision, _ = guard.decide(_payload("Edit", "src/login.js"), str(project))
    assert decision == "allow"


def test_source_write_with_scoped_task_na_is_allowed(tmp_path):
    project = _write_project(tmp_path, current_state=_SCOPED_NA)
    decision, _ = guard.decide(_payload("Write", "src/login.js"), str(project))
    assert decision == "allow"


def test_notebook_edit_uses_notebook_path(tmp_path):
    project = _write_project(tmp_path)
    decision, reason = guard.decide(
        {"tool_name": "NotebookEdit", "tool_input": {"notebook_path": "analysis.ipynb"}},
        str(project),
    )
    assert decision == "deny"


def test_malformed_payload_fails_open_end_to_end(tmp_path):
    """Full subprocess test of the stdin/stdout contract with garbage input."""
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "adapters" / "claude" / "pretooluse_scope_guard.py")],
        input="not json", capture_output=True, text=True, cwd=tmp_path,
    )
    assert result.returncode == 0
    out = json.loads(result.stdout)
    assert out["hookSpecificOutput"]["permissionDecision"] == "allow"


def test_end_to_end_denies_unscoped_source_write(tmp_path):
    project = _write_project(tmp_path)
    payload = _payload("Write", str(project / "src" / "app.py"))
    result = subprocess.run(
        [sys.executable, str(REPO_ROOT / "adapters" / "claude" / "pretooluse_scope_guard.py")],
        input=json.dumps(payload), capture_output=True, text=True, cwd=project,
    )
    assert result.returncode == 0
    out = json.loads(result.stdout)
    assert out["hookSpecificOutput"]["permissionDecision"] == "deny"
