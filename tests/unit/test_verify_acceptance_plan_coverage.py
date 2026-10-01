"""Tests for plan traceability in verify_acceptance.py: every declared FR / AC must be named on
a task's **Covers:** line in project-plan.md (guidance/decomposition/common.md).

Opt-in in both whole-project and scoped runs — nothing is checked until the plan has a filled
**Covers:** line, so plans written before the convention keep passing. The shipped templates
(project-requirements.md with ### SL-n sub-headings, project-plan.md with bracketed Covers
placeholders) must not trip the check on their own.
"""
import importlib.util
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent.parent
_VA_PATH = _ROOT / "templates" / "script" / "validators" / "verify_acceptance.py"
_spec = importlib.util.spec_from_file_location("verify_acceptance", _VA_PATH)
assert _spec is not None and _spec.loader is not None
va = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(va)

# Slice-grouped requirements: FR / AC sit under ### SL-n sub-headings inside their ## sections.
_REQUIREMENTS = """# Project Requirements

## Slices

| Slice | Behavior | Observer | Entry point | Priority | Independent Test |
|---|---|---|---|---|---|
| SL-1 | Fault raises an alarm | Line lead | Dashboard | P1 | Trigger fault, alarm shows |
| SL-2 | Lead acknowledges an alarm | Line lead | Dashboard | P2 | Ack one, it leaves the list |

## Functional Requirements

### SL-1 — Fault raises an alarm

* **FR-007**: WHEN equipment faults, THE SYSTEM SHALL raise an alarm

### SL-2 — Lead acknowledges an alarm

* **FR-008**: WHEN a lead acknowledges an alarm, THE SYSTEM SHALL record who and when

## Acceptance Criteria

### SL-1 — Fault raises an alarm

* **AC-004** (FR-007): Given a running machine, When it faults, Then an alarm appears

### SL-2 — Lead acknowledges an alarm

* **AC-005** (FR-008): Given an open alarm, When a lead acknowledges it, Then it leaves the list
* **AC-006** (FR-008): Given an acknowledged alarm, When I acknowledge it, Then the API returns 409

## Assumptions
"""


def _plan(*covers: str) -> str:
    tasks = "\n\n".join(
        f"### Task {i}: BE [SL-2] Task {i}\n\n**Goal:** g\n\n**Covers:** {c}\n"
        for i, c in enumerate(covers, start=1)
    )
    return f"""# Project Plan

<!--
  Filled example (ignored — inside a comment):
  **Covers:** FR-999, AC-999
-->

## Milestone 2: SL-2 — Lead acknowledges an alarm (P2)

{tasks}
"""


def _docs(tmp_path: Path, plan: str | None) -> str:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "project-requirements.md").write_text(_REQUIREMENTS, encoding="utf-8")
    if plan is not None:
        (docs / "project-plan.md").write_text(plan, encoding="utf-8")
    return str(docs)


def _plan_issues(docs: str, only: str | None = None) -> list[str]:
    return [i for i in va.run_audit(["cli-tool"], docs, only)["issues"] if i.startswith("project-plan.md")]


def test_slice_subheadings_keep_all_ids_declared(tmp_path):
    docs = _docs(tmp_path, None)
    issues, fr_ids = va.check_requirements(docs)
    assert issues == []
    assert fr_ids == ["007", "008"]
    assert va.declared_ac_ids(docs) == ["004", "005", "006"]


def test_no_plan_file_is_not_checked(tmp_path):
    assert _plan_issues(_docs(tmp_path, None)) == []


def test_plan_without_covers_lines_is_not_checked(tmp_path):
    plan = "# Project Plan\n\n### Task 1: BE Orders\n\n**Goal:** g\n"
    assert _plan_issues(_docs(tmp_path, plan)) == []


def test_bracketed_placeholder_covers_does_not_opt_in(tmp_path):
    assert _plan_issues(_docs(tmp_path, _plan("[FR and AC ids]", "[FR-001, AC-001]"))) == []


def test_all_ids_covered_passes(tmp_path):
    docs = _docs(tmp_path, _plan("FR-007, AC-004", "FR-008, AC-005", "AC-006"))
    assert _plan_issues(docs) == []


def test_uncovered_ac_and_fr_are_reported(tmp_path):
    issues = _plan_issues(_docs(tmp_path, _plan("FR-008, AC-005")))
    assert any("FR-007" in i and "not covered" in i for i in issues)
    assert any("AC-004" in i and "not covered" in i for i in issues)
    assert any("AC-006" in i and "not covered" in i for i in issues)
    assert not any("AC-005" in i for i in issues)


def test_covers_inside_html_comment_is_ignored(tmp_path):
    issues = _plan_issues(_docs(tmp_path, _plan("FR-007, AC-004", "FR-008, AC-005, AC-006")))
    assert not any("999" in i for i in issues)


def test_undeclared_covers_id_is_reported(tmp_path):
    issues = _plan_issues(_docs(tmp_path, _plan("FR-007, AC-004", "FR-008, AC-005, AC-006, AC-077")))
    assert issues == [
        "project-plan.md: a **Covers:** line names AC-077, which is not declared in project-requirements.md"
    ]


def test_scoped_run_checks_only_listed_ids(tmp_path):
    docs = _docs(tmp_path, _plan("FR-008, AC-005"))
    assert _plan_issues(docs, only="FR-008,AC-005") == []
    issues = _plan_issues(docs, only="FR-008,AC-005,AC-006")
    assert len(issues) == 1 and "AC-006" in issues[0]


def test_scoped_run_without_covers_lines_is_not_checked(tmp_path):
    plan = "# Project Plan\n\n### Task 1: BE Orders\n\n**Goal:** g\n"
    assert _plan_issues(_docs(tmp_path, plan), only="FR-008,AC-005") == []


def test_shipped_templates_do_not_trip_plan_check(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    for name in ("project-requirements.md", "project-plan.md"):
        (docs / name).write_text((_ROOT / "templates" / name).read_text(encoding="utf-8"), encoding="utf-8")
    assert va.plan_covered_ids(str(docs)) == (set(), set())
    assert _plan_issues(str(docs)) == []
