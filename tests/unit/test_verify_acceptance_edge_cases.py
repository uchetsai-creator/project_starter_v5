"""Tests for check_edge_case_traceability() in verify_acceptance.py.

Reuses the same FR-XXX traceability shape check_test_plan() already applies to
project-requirements.md, for api-contract.md's Edge Cases table instead. Opt-in: the
shipped template's ID column is bracketed ([EC-001]) as a placeholder, so a project that
never adopts the convention gets zero issues — this is deliberately different from
check_requirements()'s FR-XXX handling, which requires FR ids to exist at all.
"""
import importlib.util
from pathlib import Path

_VA_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "templates" / "script" / "validators" / "verify_acceptance.py"
)
_spec = importlib.util.spec_from_file_location("verify_acceptance", _VA_PATH)
assert _spec is not None and _spec.loader is not None
va = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(va)


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


_EDGE_CASES_UNADOPTED = """## Edge Cases

| ID | Scenario | Expected behaviour |
|---|---|---|
| [EC-001] | Required field missing | `400 VALIDATION_FIELD_REQUIRED` |
| [EC-002] | Token expired | `401 AUTH_TOKEN_EXPIRED` |
"""

_EDGE_CASES_ADOPTED = """## Edge Cases

| ID | Scenario | Expected behaviour |
|---|---|---|
| EC-001 | Required field missing | `400 VALIDATION_FIELD_REQUIRED` |
| EC-002 | Token expired | `401 AUTH_TOKEN_EXPIRED` |
"""


def test_no_api_contract_file_returns_no_issues(tmp_path):
    assert va.check_edge_case_traceability(str(tmp_path)) == []


# ---------------------------------------------------------------------------
# Telemetry — regression coverage for the dict/positional schema drift: this validator
# used to call _append_telemetry() with the positional-args convention ('script'/'status'
# keys), diverging from the 'validator'/'level' schema every other validator writes and
# README.md's validation-result.json documents. Fixed to use the dict convention; this
# test guards it from silently reverting.
# ---------------------------------------------------------------------------

def test_telemetry_uses_validator_and_level_keys_not_script_and_status(tmp_path):
    import json
    import subprocess
    import sys

    docs = tmp_path / "docs"
    docs.mkdir()
    result = subprocess.run(
        [sys.executable, str(_VA_PATH), "--project-type", "cli-tool", "--docs", str(docs)],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=str(tmp_path),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    telemetry_file = tmp_path / ".ai" / "telemetry" / "validation-result.json"
    assert telemetry_file.exists()
    rows = json.loads(telemetry_file.read_text(encoding="utf-8"))
    assert len(rows) == 1
    row = rows[0]
    assert row["validator"] == "verify_acceptance.py"
    assert row["level"] in ("pass", "fail")
    assert row["project_type"] == "cli-tool"
    assert "script" not in row
    assert "status" not in row


def test_no_edge_cases_section_returns_no_issues(tmp_path):
    _write(tmp_path / "specs" / "api-contract.md", "# API Contract\n\nNo edge cases here.\n")
    assert va.check_edge_case_traceability(str(tmp_path)) == []


def test_unadopted_bracketed_ids_return_no_issues(tmp_path):
    """The shipped template ships with [EC-001]-style placeholders — must not force work
    on every project that hasn't opted into the convention."""
    _write(tmp_path / "specs" / "api-contract.md", _EDGE_CASES_UNADOPTED)
    assert va.check_edge_case_traceability(str(tmp_path)) == []


def test_adopted_ids_with_no_test_plan_reports_issue(tmp_path):
    _write(tmp_path / "specs" / "api-contract.md", _EDGE_CASES_ADOPTED)
    issues = va.check_edge_case_traceability(str(tmp_path))
    assert len(issues) == 1
    assert "test-plan.md not found" in issues[0]


def test_adopted_ids_uncovered_in_test_plan_are_reported(tmp_path):
    _write(tmp_path / "specs" / "api-contract.md", _EDGE_CASES_ADOPTED)
    _write(
        tmp_path / "specs" / "test-plan.md",
        "## Test Scope\n\n### In Scope\n\n"
        "| Module | Requirement | Levels | Notes |\n|---|---|---|---|\n"
        "| Auth | FR-001 | Unit | - |\n",
    )
    issues = va.check_edge_case_traceability(str(tmp_path))
    assert len(issues) == 2
    assert any("EC-001" in i for i in issues)
    assert any("EC-002" in i for i in issues)


def test_adopted_ids_covered_in_test_plan_pass(tmp_path):
    _write(tmp_path / "specs" / "api-contract.md", _EDGE_CASES_ADOPTED)
    _write(
        tmp_path / "specs" / "test-plan.md",
        "## Test Scope\n\n### In Scope\n\n"
        "| Module | Requirement | Levels | Notes |\n|---|---|---|---|\n"
        "| Auth | FR-001, EC-001 | Unit | - |\n"
        "| Auth | EC-002 | Unit | - |\n",
    )
    assert va.check_edge_case_traceability(str(tmp_path)) == []


def test_partial_coverage_reports_only_the_uncovered_id(tmp_path):
    _write(tmp_path / "specs" / "api-contract.md", _EDGE_CASES_ADOPTED)
    _write(
        tmp_path / "specs" / "test-plan.md",
        "## Test Scope\n\n### In Scope\n\n"
        "| Module | Requirement | Levels | Notes |\n|---|---|---|---|\n"
        "| Auth | EC-001 | Unit | - |\n",
    )
    issues = va.check_edge_case_traceability(str(tmp_path))
    assert len(issues) == 1
    assert "EC-002" in issues[0]


def test_bracketed_reference_in_test_plan_does_not_count_as_coverage(tmp_path):
    """A leftover [EC-XXX] placeholder in test-plan.md's own template row must not
    accidentally satisfy coverage for a real adopted id."""
    _write(tmp_path / "specs" / "api-contract.md", _EDGE_CASES_ADOPTED)
    _write(
        tmp_path / "specs" / "test-plan.md",
        "## Test Scope\n\n### In Scope\n\n"
        "| Module | Requirement | Levels | Notes |\n|---|---|---|---|\n"
        "| [Module] | [FR-XXX, EC-XXX] | [Levels] | [Notes] |\n",
    )
    issues = va.check_edge_case_traceability(str(tmp_path))
    assert len(issues) == 2


def test_instructional_comment_prose_does_not_leak_into_declared_ids(tmp_path):
    """Regression: the shipped template's own <!-- --> comment explains the EC-XXX
    convention using unbracketed example ids in prose (e.g. "EC-002", "EC-XXX id") —
    those must not be picked up as if they were real declared ids in the table."""
    _write(
        tmp_path / "specs" / "api-contract.md",
        "## Edge Cases\n\n"
        "<!-- replace [EC-001] with a real un-bracketed EC-XXX id, e.g. \"FR-001, EC-002\" -->\n\n"
        "| ID | Scenario | Expected behaviour |\n|---|---|---|\n"
        "| [EC-001] | Required field missing | `400` |\n",
    )
    assert va.check_edge_case_traceability(str(tmp_path)) == []


def test_run_audit_gates_check_by_project_type(tmp_path):
    _write(tmp_path / "specs" / "api-contract.md", _EDGE_CASES_ADOPTED)
    # cli-tool doesn't use api-contract.md at all — check must not run for it.
    result = va.run_audit(["cli-tool"], str(tmp_path))
    assert not any("Edge Case" in i for i in result["issues"])
