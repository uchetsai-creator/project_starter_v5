import importlib.util
from pathlib import Path

_orch_path = Path(__file__).resolve().parent.parent.parent / "orchestrator.py"
_spec = importlib.util.spec_from_file_location("orchestrator", _orch_path)
assert _spec is not None and _spec.loader is not None
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
_render = _mod._render
_resolve_spec_code_bindings = _mod._resolve_spec_code_bindings


def _ctx(task_type=None, project_type="web-app", validators=None, spec_code_bindings=None):
    return {
        "task_type": task_type,
        "project_type": project_type,
        "workflow_key": task_type or "default",
        "validators": validators or [],
        "spec_code_bindings": spec_code_bindings or [],
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


# ---------------------------------------------------------------------------
# spec_code_bindings injection
# ---------------------------------------------------------------------------

_SPEC_CODE = {"adapter": "fastapi", "spec": "docs/specs/api-contract.md", "src": "src/"}
_SPEC_CODE_2 = {"adapter": "airflow", "spec": "docs/specs/pipeline-contract.md", "src": "src/stages/"}


def test_render_injects_spec_code_args_when_configured():
    validators = [{"script": "docs/script/validators/verify_spec_code.py", "args": ["--strict"]}]
    out = _render(_ctx(task_type="feature", validators=validators, spec_code_bindings=[_SPEC_CODE]))
    assert "--adapter fastapi --spec docs/specs/api-contract.md --src src/" in out
    assert "--strict" in out


def test_render_omits_spec_code_args_when_not_configured():
    validators = [{"script": "docs/script/validators/verify_spec_code.py", "args": ["--strict"]}]
    out = _render(_ctx(task_type="feature", validators=validators, spec_code_bindings=[]))
    assert "--adapter" not in out


def test_render_does_not_inject_spec_code_args_into_other_validators():
    validators = [{"script": "docs/script/validators/verify_docs.py", "args": ["--content"]}]
    out = _render(_ctx(task_type="feature", validators=validators, spec_code_bindings=[_SPEC_CODE]))
    assert "--adapter" not in out


def test_render_expands_one_line_per_spec_code_binding():
    validators = [{"script": "docs/script/validators/verify_spec_code.py", "args": ["--strict"]}]
    out = _render(_ctx(
        task_type="feature", validators=validators, spec_code_bindings=[_SPEC_CODE, _SPEC_CODE_2],
    ))
    assert "--adapter fastapi --spec docs/specs/api-contract.md --src src/ --strict" in out
    assert "--adapter airflow --spec docs/specs/pipeline-contract.md --src src/stages/ --strict" in out
    assert "1. `python3 docs/script/validators/verify_spec_code.py --project-type web-app --adapter fastapi" in out
    assert "2. `python3 docs/script/validators/verify_spec_code.py --project-type web-app --adapter airflow" in out


def test_render_numbers_continue_correctly_around_expanded_bindings():
    validators = [
        {"script": "docs/script/verify_docs.py", "args": []},
        {"script": "docs/script/validators/verify_spec_code.py", "args": []},
        {"script": "docs/script/verify_content.py", "args": []},
    ]
    out = _render(_ctx(
        task_type="feature", validators=validators, spec_code_bindings=[_SPEC_CODE, _SPEC_CODE_2],
    ))
    # 4 rendered lines total: verify_docs, 2x verify_spec_code (one per binding), verify_content
    assert "1. `python3 docs/script/verify_docs.py" in out
    assert "2. `python3 docs/script/validators/verify_spec_code.py" in out
    assert "3. `python3 docs/script/validators/verify_spec_code.py" in out
    assert "4. `python3 docs/script/verify_content.py" in out
    assert "5. " not in out


# ---------------------------------------------------------------------------
# _resolve_spec_code_bindings — reads .project-starter.yml's config, not ctx
# ---------------------------------------------------------------------------

def test_resolve_bindings_empty_when_unconfigured():
    assert _resolve_spec_code_bindings({}) == []


def test_resolve_bindings_legacy_single_trio():
    cfg = {
        "spec_code_adapter": "fastapi",
        "spec_code_spec": "docs/specs/api-contract.md",
        "spec_code_src": "src/",
    }
    assert _resolve_spec_code_bindings(cfg) == [
        {"adapter": "fastapi", "spec": "docs/specs/api-contract.md", "src": "src/"},
    ]


def test_resolve_bindings_legacy_trio_requires_all_three():
    cfg = {"spec_code_adapter": "fastapi", "spec_code_spec": "docs/specs/api-contract.md"}
    assert _resolve_spec_code_bindings(cfg) == []


def test_resolve_bindings_new_list_form():
    cfg = {
        "spec_code_bindings": [
            {"adapter": "fastapi", "spec": "docs/specs/api-contract.md", "src": "src/"},
            {"adapter": "airflow", "spec": "docs/specs/pipeline-contract.md", "src": "src/stages/"},
        ],
    }
    assert _resolve_spec_code_bindings(cfg) == [
        {"adapter": "fastapi", "spec": "docs/specs/api-contract.md", "src": "src/"},
        {"adapter": "airflow", "spec": "docs/specs/pipeline-contract.md", "src": "src/stages/"},
    ]


def test_resolve_bindings_list_form_drops_incomplete_entries():
    cfg = {
        "spec_code_bindings": [
            {"adapter": "fastapi", "spec": "docs/specs/api-contract.md", "src": "src/"},
            {"adapter": "airflow", "spec": "docs/specs/pipeline-contract.md"},  # missing src
            "not-even-a-mapping",
        ],
    }
    assert _resolve_spec_code_bindings(cfg) == [
        {"adapter": "fastapi", "spec": "docs/specs/api-contract.md", "src": "src/"},
    ]


def test_resolve_bindings_list_form_takes_precedence_over_legacy_trio():
    cfg = {
        "spec_code_adapter": "flask",
        "spec_code_spec": "docs/specs/api-contract.md",
        "spec_code_src": "src/",
        "spec_code_bindings": [
            {"adapter": "fastapi", "spec": "docs/specs/api-contract.md", "src": "src/"},
        ],
    }
    result = _resolve_spec_code_bindings(cfg)
    assert len(result) == 1
    assert result[0]["adapter"] == "fastapi"
