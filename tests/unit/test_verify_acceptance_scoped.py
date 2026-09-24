"""Tests for AC-XXX traceability and the scoped --only run in verify_acceptance.py.

A whole-project run only starts checking AC-XXX once test-plan.md references at least one (opt-in,
same convention as EC-XXX). A scoped run (--only FR-012,AC-012) always checks the listed ids and
fails on an id the requirements file does not declare. The test-report's Overall status stays
whole-project either way.
"""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

_VA_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "templates" / "script" / "validators" / "verify_acceptance.py"
)
_spec = importlib.util.spec_from_file_location("verify_acceptance", _VA_PATH)
assert _spec is not None and _spec.loader is not None
va = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(va)

_REQUIREMENTS = """# Project Requirements

## Functional Requirements

* **FR-011**: Staff can list orders
* **FR-012**: Staff can export a report

## Acceptance Criteria

* **AC-011**: Given orders exist, When staff open the list, Then orders are shown
* **AC-012**: Given a class teacher, When they export another class, Then the API returns 403

## Assumptions
"""

_REPORT = """# Test Report

**Overall status:** ✅ Pass

## Summary

| Metric | Count |
|---|---|
| Total | 12 |

## Results by Module

| Module | Result |
|---|---|
| Orders | ✅ Pass |
"""


def _plan(scope_rows: str) -> str:
    return f"""# Test Plan

## Test Scope

### In Scope

| Module / Feature | Requirement | Levels | Notes |
|---|---|---|---|
{scope_rows}

## Testing Strategy

| Level | Tool |
|---|---|
| Unit | pytest |
| Integration | pytest |
| E2E | playwright |
"""


def _docs(tmp_path: Path, scope_rows: str, report: str = _REPORT) -> str:
    docs = tmp_path / "docs"
    (docs / "specs").mkdir(parents=True)
    (docs / "project-requirements.md").write_text(_REQUIREMENTS, encoding="utf-8")
    (docs / "specs" / "test-plan.md").write_text(_plan(scope_rows), encoding="utf-8")
    (docs / "specs" / "test-report.md").write_text(report, encoding="utf-8")
    return str(docs)


def _issues(docs: str, only: str | None = None) -> list[str]:
    return va.run_audit(["web-app"], docs, only)["issues"]


_ALL_COVERED = "| Orders | FR-011, AC-011 | Unit | n |\n| Export | FR-012, AC-012 | Unit | n |"
_FR_ONLY = "| Orders | FR-011 | Unit | n |\n| Export | FR-012 | Unit | n |"


def test_whole_run_without_any_ac_reference_is_unaffected(tmp_path):
    """Opt-in: a project that never adopted AC ids in its test plan gets no AC issue."""
    assert _issues(_docs(tmp_path, _FR_ONLY)) == []


def test_whole_run_flags_uncovered_ac_once_convention_is_adopted(tmp_path):
    rows = "| Orders | FR-011, AC-011 | Unit | n |\n| Export | FR-012 | Unit | n |"
    issues = _issues(_docs(tmp_path, rows))
    assert any("AC-012" in i and "no test coverage" in i for i in issues)
    assert not any("AC-011" in i for i in issues)


def test_scoped_run_passes_when_listed_ids_are_covered(tmp_path):
    assert _issues(_docs(tmp_path, _ALL_COVERED), "FR-012,AC-012") == []


def test_scoped_run_always_checks_ac_even_without_opt_in(tmp_path):
    issues = _issues(_docs(tmp_path, _FR_ONLY), "FR-012,AC-012")
    assert any("AC-012" in i and "no test coverage" in i for i in issues)


def test_scoped_run_ignores_other_requirements_gaps(tmp_path):
    """FR-011 / AC-011 are uncovered but belong to another requirement."""
    rows = "| Export | FR-012, AC-012 | Unit | n |"
    assert _issues(_docs(tmp_path, rows), "FR-012,AC-012") == []


def test_scoped_run_fails_on_undeclared_id(tmp_path):
    issues = _issues(_docs(tmp_path, _ALL_COVERED), "FR-099")
    assert any("FR-099" in i and "not declared" in i for i in issues)


def test_scoped_run_rejects_unrecognised_token(tmp_path):
    issues = _issues(_docs(tmp_path, _ALL_COVERED), "FR-012,banana")
    assert any("banana" in i for i in issues)


def test_scoped_run_with_empty_list_fails(tmp_path):
    issues = _issues(_docs(tmp_path, _ALL_COVERED), " ")
    assert any("no requirement ids" in i for i in issues)


def test_scoped_run_is_case_insensitive(tmp_path):
    assert _issues(_docs(tmp_path, _ALL_COVERED), "fr-012, ac-012") == []


def test_test_report_overall_status_is_still_checked_when_scoped(tmp_path):
    failing = _REPORT.replace("✅ Pass", "❌ Fail")
    issues = _issues(_docs(tmp_path, _ALL_COVERED, report=failing), "FR-012,AC-012")
    assert any("Overall status" in i for i in issues)


def test_cli_only_flag_exit_codes(tmp_path):
    docs = _docs(tmp_path, _ALL_COVERED)
    base = [sys.executable, str(_VA_PATH), "--project-type", "web-app", "--docs", docs, "--strict"]
    ok = subprocess.run([*base, "--only", "FR-012,AC-012"], cwd=tmp_path, capture_output=True, text=True, encoding="utf-8")
    assert ok.returncode == 0, ok.stdout + ok.stderr
    bad = subprocess.run([*base, "--only", "FR-099"], cwd=tmp_path, capture_output=True, text=True, encoding="utf-8")
    assert bad.returncode == 1
    js = subprocess.run([*base, "--only", "FR-012", "--json"], cwd=tmp_path, capture_output=True, text=True, encoding="utf-8")
    assert json.loads(js.stdout)["passed"] is True
