import importlib.util
from pathlib import Path

_orch_path = Path(__file__).resolve().parent.parent.parent / "orchestrator.py"
_spec = importlib.util.spec_from_file_location("orchestrator", _orch_path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
_render = _mod._render


def _ctx(task_type=None, project_type="web-app", validators=None):
    return {
        "task_type": task_type,
        "project_type": project_type,
        "workflow_key": task_type or "default",
        "validators": validators or [],
    }


# ---------------------------------------------------------------------------
# Task label in heading
# ---------------------------------------------------------------------------

def test_render_heading_contains_task_type():
    out = _render(_ctx(task_type="feature"))
    assert "# Workflow Plan — feature / web-app" in out


def test_render_heading_uses_unset_when_none():
    out = _render(_ctx(task_type=None))
    assert "# Workflow Plan — unset / web-app" in out


def test_render_heading_contains_project_type():
    out = _render(_ctx(task_type="bug-fix", project_type="data-pipeline"))
    assert "data-pipeline" in out


# ---------------------------------------------------------------------------
# Validator commands
# ---------------------------------------------------------------------------

def test_render_includes_validator_command():
    validators = [{"script": "docs/script/verify_docs.py", "args": []}]
    out = _render(_ctx(task_type="feature", validators=validators))
    assert "python3" in out
    assert "verify_docs.py" in out


def test_render_includes_project_type_in_validator_args():
    validators = [{"script": "docs/script/verify_docs.py", "args": []}]
    out = _render(_ctx(task_type="feature", project_type="web-app", validators=validators))
    assert "--project-type web-app" in out


def test_render_numbers_validators_in_order():
    validators = [
        {"script": "docs/script/verify_docs.py", "args": []},
        {"script": "docs/script/verify_content.py", "args": []},
    ]
    out = _render(_ctx(task_type="feature", validators=validators))
    assert "1. " in out
    assert "2. " in out


def test_render_no_validators_shows_message():
    out = _render(_ctx(task_type="feature", validators=[]))
    assert "no validators" in out.lower()


# ---------------------------------------------------------------------------
# Structure
# ---------------------------------------------------------------------------

def test_render_contains_pre_task_section():
    out = _render(_ctx())
    assert "## Pre-task" in out


def test_render_contains_post_task_section():
    out = _render(_ctx())
    assert "## Post-task validators" in out


def test_render_contains_closeout_section():
    out = _render(_ctx())
    assert "## Closeout" in out
