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

import checkpoint_session_state as cps  # noqa: E402
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


# ---------------------------------------------------------------------------
# checkpoint_enforcement opt-in modes (unset = tests above, unchanged behavior)
# ---------------------------------------------------------------------------

def _write_project_with_enforcement(tmp_path: Path, mode: str,
                                     current_state: str | None = _PLACEHOLDER_TASK) -> Path:
    (tmp_path / ".project-starter.yml").write_text(
        f"project_type: web-app\ndocs_path: docs/\ncheckpoint_enforcement: {mode}\n",
        encoding="utf-8",
    )
    if current_state is not None:
        docs = tmp_path / "docs"
        docs.mkdir(exist_ok=True)
        (docs / "current-state.md").write_text(current_state, encoding="utf-8")
    return tmp_path


def _payload_with_session(tool_name: str, file_path: str, session_id: str) -> dict:
    return {"tool_name": tool_name, "tool_input": {"file_path": file_path}, "session_id": session_id}


def test_checkpoint_enforcement_off_always_allows_even_when_unscoped(tmp_path):
    project = _write_project_with_enforcement(tmp_path, "off")
    decision, _ = guard.decide(_payload("Edit", "src/login.js"), str(project))
    assert decision == "allow"


def test_session_prompt_unanswered_session_fails_open(tmp_path):
    project = _write_project_with_enforcement(tmp_path, "session-prompt")
    decision, reason = guard.decide(
        _payload_with_session("Edit", "src/login.js", "session-a"), str(project),
    )
    assert decision == "allow"
    assert "has not chosen yet" in reason


def test_session_prompt_opted_out_allows_even_when_unscoped(tmp_path):
    project = _write_project_with_enforcement(tmp_path, "session-prompt")
    cps.write_choice("session-a", False, cwd=str(project))
    decision, reason = guard.decide(
        _payload_with_session("Edit", "src/login.js", "session-a"), str(project),
    )
    assert decision == "allow"
    assert "opted out" in reason


def test_session_prompt_opted_in_denies_when_unscoped(tmp_path):
    project = _write_project_with_enforcement(tmp_path, "session-prompt")
    cps.write_choice("session-a", True, cwd=str(project))
    decision, reason = guard.decide(
        _payload_with_session("Edit", "src/login.js", "session-a"), str(project),
    )
    assert decision == "deny"
    assert "no scoped Current Task" in reason


def test_session_prompt_opted_in_allows_when_scoped(tmp_path):
    project = _write_project_with_enforcement(tmp_path, "session-prompt", current_state=_SCOPED_Y)
    cps.write_choice("session-a", True, cwd=str(project))
    decision, _ = guard.decide(
        _payload_with_session("Edit", "src/login.js", "session-a"), str(project),
    )
    assert decision == "allow"


def test_session_prompt_different_session_id_is_unanswered(tmp_path):
    project = _write_project_with_enforcement(tmp_path, "session-prompt")
    cps.write_choice("session-a", True, cwd=str(project))
    decision, reason = guard.decide(
        _payload_with_session("Edit", "src/login.js", "session-b"), str(project),
    )
    assert decision == "allow"
    assert "has not chosen yet" in reason


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


# --- Approach Confirmed: the proposed breakdown/approach must be shown to the user
# before code is written. Only gates once the field exists in current-state.md. ---

_APPROACH_PLACEHOLDER = _SCOPED_Y + "\n**Approach Confirmed:** [Y / N/A — reason]\n"
_APPROACH_INVALID = _SCOPED_Y + "\n**Approach Confirmed:** N\n"
_APPROACH_Y = _SCOPED_Y + "\n**Approach Confirmed:** Y\n"
_APPROACH_NA = _SCOPED_Y + "\n**Approach Confirmed:** N/A — single obvious change\n"
_APPROACH_Y_REASON = _SCOPED_Y + "\n**Approach Confirmed:** Y — approach A chosen; split DB / BE / FE\n"


def test_approach_field_absent_is_allowed(tmp_path):
    """current-state.md files that predate the field keep working."""
    project = _write_project(tmp_path, current_state=_SCOPED_Y)
    decision, _ = guard.decide(_payload("Write", "src/app.py"), str(project))
    assert decision == "allow"


def test_approach_placeholder_is_denied(tmp_path):
    project = _write_project(tmp_path, current_state=_APPROACH_PLACEHOLDER)
    decision, reason = guard.decide(_payload("Write", "src/app.py"), str(project))
    assert decision == "deny"
    assert "Approach Confirmed" in reason


def test_approach_invalid_value_is_denied(tmp_path):
    project = _write_project(tmp_path, current_state=_APPROACH_INVALID)
    decision, reason = guard.decide(_payload("Write", "src/app.py"), str(project))
    assert decision == "deny"
    assert "Approach Confirmed" in reason


def test_approach_y_is_allowed(tmp_path):
    project = _write_project(tmp_path, current_state=_APPROACH_Y)
    decision, _ = guard.decide(_payload("Write", "src/app.py"), str(project))
    assert decision == "allow"


def test_approach_na_is_denied_because_the_discussion_is_mandatory(tmp_path):
    project = _write_project(tmp_path, current_state=_APPROACH_NA)
    decision, reason = guard.decide(_payload("Write", "src/app.py"), str(project))
    assert decision == "deny"
    assert "no N/A" in reason


def test_approach_y_with_what_was_agreed_is_allowed(tmp_path):
    project = _write_project(tmp_path, current_state=_APPROACH_Y_REASON)
    decision, _ = guard.decide(_payload("Write", "src/app.py"), str(project))
    assert decision == "allow"


def test_approach_unfilled_still_allows_doc_edits(tmp_path):
    """The proposal itself lives in docs/current-state.md, so editing docs must stay possible."""
    project = _write_project(tmp_path, current_state=_APPROACH_PLACEHOLDER)
    decision, _ = guard.decide(_payload("Edit", "docs/current-state.md"), str(project))
    assert decision == "allow"


def test_approach_check_respects_enforcement_off(tmp_path):
    project = _write_project_with_enforcement(tmp_path, "off", current_state=_APPROACH_PLACEHOLDER)
    decision, _ = guard.decide(_payload("Write", "src/app.py"), str(project))
    assert decision == "allow"


# --- Clarifications: the USER answers every category; the agent never decides scope. Only
# gates when current-state.md has a `## Clarifications` section. ---

_CATS = [
    "Goal & scope", "Users & permissions", "Data", "Flow & interaction",
    "Edge cases & failure handling",
    "Non-functional (performance, security, reliability, compliance)",
    "Integrations & external dependencies", "Constraints & trade-offs",
    "Terminology & conventions", "Acceptance criteria (done means)",
]


def _clar_state(overrides: dict | None = None, default: str = "answered by the user") -> str:
    lines = [f"- **{c}:** {(overrides or {}).get(c, default)}" for c in _CATS]
    return _SCOPED_Y + "\n## Clarifications\n\n" + "\n".join(lines) + "\n\n## Approach\n"


def test_clarifications_section_absent_is_allowed(tmp_path):
    """current-state.md files that predate the section keep working."""
    project = _write_project(tmp_path, current_state=_SCOPED_Y)
    decision, _ = guard.decide(_payload("Write", "src/app.py"), str(project))
    assert decision == "allow"


def test_clarifications_all_answered_is_allowed(tmp_path):
    project = _write_project(tmp_path, current_state=_clar_state())
    decision, _ = guard.decide(_payload("Write", "src/app.py"), str(project))
    assert decision == "allow"


def test_clarifications_placeholder_is_denied_and_names_the_category(tmp_path):
    project = _write_project(tmp_path, current_state=_clar_state({"Data": "[ask the user]"}))
    decision, reason = guard.decide(_payload("Write", "src/app.py"), str(project))
    assert decision == "deny"
    assert "Data" in reason
    assert "only the user may skip" in reason


def test_clarifications_empty_answer_is_denied(tmp_path):
    project = _write_project(tmp_path, current_state=_clar_state({"Users & permissions": ""}))
    decision, reason = guard.decide(_payload("Write", "src/app.py"), str(project))
    assert decision == "deny"
    assert "Users & permissions" in reason


def test_clarifications_agent_written_na_is_denied(tmp_path):
    """The agent may not decide a category is out of scope; N/A must say the user did."""
    project = _write_project(tmp_path, current_state=_clar_state({"Data": "N/A — not relevant"}))
    decision, reason = guard.decide(_payload("Write", "src/app.py"), str(project))
    assert decision == "deny"
    assert "N/A — user" in reason


def test_clarifications_user_na_with_reason_is_allowed(tmp_path):
    project = _write_project(
        tmp_path, current_state=_clar_state({"Data": "N/A — user: no data is touched"}),
    )
    decision, _ = guard.decide(_payload("Write", "src/app.py"), str(project))
    assert decision == "allow"


def test_clarifications_user_na_without_reason_is_denied(tmp_path):
    project = _write_project(tmp_path, current_state=_clar_state({"Data": "N/A — user:"}))
    decision, _ = guard.decide(_payload("Write", "src/app.py"), str(project))
    assert decision == "deny"


def test_clarifications_section_with_no_categories_is_denied(tmp_path):
    project = _write_project(
        tmp_path, current_state=_SCOPED_Y + "\n## Clarifications\n\nnothing here\n\n## Approach\n",
    )
    decision, _ = guard.decide(_payload("Write", "src/app.py"), str(project))
    assert decision == "deny"


def test_clarifications_unanswered_still_allows_doc_edits(tmp_path):
    """Answers are recorded in docs/current-state.md itself, so docs must stay editable."""
    project = _write_project(tmp_path, current_state=_clar_state({"Data": "[ask the user]"}))
    decision, _ = guard.decide(_payload("Edit", "docs/current-state.md"), str(project))
    assert decision == "allow"


# --- Approach -> Docs to update: the docs each task updates are agreed with the user when the
# breakdown is proposed. Only gates when the "- **Docs to update:**" line exists; must name
# project-requirements.md (always on the list). ---

def _docs_state(value: str) -> str:
    return _SCOPED_Y + "\n## Approach\n\n- **Breakdown:** 3 tasks\n- **Docs to update:** " + value + "\n"


def test_docs_to_update_line_absent_is_allowed(tmp_path):
    project = _write_project(tmp_path, current_state=_SCOPED_Y + "\n## Approach\n\n- **Breakdown:** 3 tasks\n")
    decision, _ = guard.decide(_payload("Write", "src/app.py"), str(project))
    assert decision == "allow"


def test_docs_to_update_placeholder_is_denied(tmp_path):
    project = _write_project(tmp_path, current_state=_docs_state("[Per task: which spec docs change]"))
    decision, reason = guard.decide(_payload("Write", "src/app.py"), str(project))
    assert decision == "deny"
    assert "Docs to update" in reason


def test_docs_to_update_empty_is_denied(tmp_path):
    project = _write_project(tmp_path, current_state=_docs_state(""))
    decision, _ = guard.decide(_payload("Write", "src/app.py"), str(project))
    assert decision == "deny"


def test_docs_to_update_without_project_requirements_is_denied(tmp_path):
    project = _write_project(tmp_path, current_state=_docs_state("api-contract.md (new endpoint)"))
    decision, reason = guard.decide(_payload("Write", "src/app.py"), str(project))
    assert decision == "deny"
    assert "project-requirements" in reason


def test_docs_to_update_filled_is_allowed(tmp_path):
    project = _write_project(
        tmp_path, current_state=_docs_state("task 1: project-requirements.md, api-contract.md; task 2: none"),
    )
    decision, _ = guard.decide(_payload("Write", "src/app.py"), str(project))
    assert decision == "allow"


def test_docs_to_update_unfilled_still_allows_doc_edits(tmp_path):
    project = _write_project(tmp_path, current_state=_docs_state("[placeholder]"))
    decision, _ = guard.decide(_payload("Edit", "docs/current-state.md"), str(project))
    assert decision == "allow"


# --- The other Approach impact lines: tests, dependencies, config / CI / deploy, per-module docs ---

def _impact_state(extra: str) -> str:
    return _docs_state("project-requirements.md, api-contract.md") + extra


def test_tests_line_placeholder_is_denied(tmp_path):
    project = _write_project(tmp_path, current_state=_impact_state("- **Tests to add/update:** [per task]\n"))
    decision, reason = guard.decide(_payload("Write", "src/app.py"), str(project))
    assert decision == "deny"
    assert "Tests to add/update" in reason


def test_tests_line_without_ids_is_denied(tmp_path):
    project = _write_project(tmp_path, current_state=_impact_state("- **Tests to add/update:** some unit tests\n"))
    decision, reason = guard.decide(_payload("Write", "src/app.py"), str(project))
    assert decision == "deny"
    assert "AC-/FR-" in reason


def test_tests_line_naming_ids_is_allowed(tmp_path):
    project = _write_project(tmp_path, current_state=_impact_state("- **Tests to add/update:** test_export covers AC-012\n"))
    decision, _ = guard.decide(_payload("Write", "src/app.py"), str(project))
    assert decision == "allow"


def _sub(tmp_path, name):
    d = tmp_path / name
    d.mkdir()
    return d


def test_tests_line_user_na_is_allowed_but_agent_na_is_denied(tmp_path):
    ok = _write_project(_sub(tmp_path, "a"), current_state=_impact_state("- **Tests to add/update:** N/A — user: docs only\n"))
    assert guard.decide(_payload("Write", "src/app.py"), str(ok))[0] == "allow"
    bad = _write_project(_sub(tmp_path, "b"), current_state=_impact_state("- **Tests to add/update:** N/A — not needed\n"))
    assert guard.decide(_payload("Write", "src/app.py"), str(bad))[0] == "deny"


def test_other_impact_lines_placeholder_is_denied_and_none_is_allowed(tmp_path):
    for i, field in enumerate(("Dependencies", "Config / CI / deploy", "Per-module docs")):
        bad = _write_project(_sub(tmp_path, f"bad{i}"), current_state=_impact_state(f"- **{field}:** [x]\n"))
        decision, reason = guard.decide(_payload("Write", "src/app.py"), str(bad))
        assert decision == "deny" and field in reason
        ok = _write_project(_sub(tmp_path, f"ok{i}"), current_state=_impact_state(f"- **{field}:** none\n"))
        assert guard.decide(_payload("Write", "src/app.py"), str(ok))[0] == "allow"
