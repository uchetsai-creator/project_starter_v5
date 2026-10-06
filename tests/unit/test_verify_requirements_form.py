"""Unit tests for verify_requirements_form.py: EARS form, scenarios, user journeys, glossary."""
import importlib.util

from tests.conftest import REPO_ROOT

_MOD = REPO_ROOT / "templates/script/validators/verify_requirements_form.py"


def _load():
    spec = importlib.util.spec_from_file_location("verify_requirements_form", _MOD)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


vrf = _load()

GOOD = """# Project Requirements

## Functional Requirements

### SL-1 — Case creation

* **FR-001**: WHEN a user submits a new case, THE SYSTEM SHALL create the case and its first board
* **FR-002**: THE SYSTEM SHALL keep an audit log of every change

Scenario: create a case
- **Given** a logged-in engineer
- **When** they submit the form
- **Then** the case appears in the list

## User Journeys

### Engineer creates a case
Steps and outcome.

## Acceptance Criteria
"""


def _write(tmp_path, body, glossary=True):
    (tmp_path / "project-requirements.md").write_text(body, encoding="utf-8")
    if glossary:
        (tmp_path / "specs").mkdir(exist_ok=True)
        (tmp_path / "specs" / "glossary.md").write_text("# Glossary\n", encoding="utf-8")
    return str(tmp_path)


def test_good_document_passes_every_check(tmp_path):
    result = vrf.run(_write(tmp_path, GOOD))
    assert result["passed"], result["checks"]


def test_fr_without_ears_trigger_is_a_violation(tmp_path):
    body = GOOD.replace("WHEN a user submits a new case, THE SYSTEM SHALL", "a user can create a case; SHALL")
    result = vrf.run(_write(tmp_path, body))
    ids = [v["id"] for v in result["checks"]["ears"]["violations"]]
    assert ids == ["FR-001"]
    assert result["checks"]["ears"]["ok"] is False


def test_template_placeholder_is_unfilled_not_a_violation(tmp_path):
    body = GOOD.replace("WHEN a user submits a new case, THE SYSTEM SHALL create the case and its first board",
                        "WHEN [trigger/event occurs], THE SYSTEM SHALL [expected response]")
    result = vrf.run(_write(tmp_path, body))
    assert result["checks"]["ears"]["violations"] == []
    assert [u["id"] for u in result["checks"]["ears"]["unfilled"]] == ["FR-001"]


def test_group_without_scenario_fails(tmp_path):
    body = GOOD.split("Scenario: create a case")[0] + GOOD.split("- **Then** the case appears in the list")[1]
    result = vrf.run(_write(tmp_path, body))
    assert result["checks"]["scenarios"]["missing"] == ["SL-1 — Case creation"]


def test_plain_groups_without_slices_are_checked_by_heading(tmp_path):
    body = """# T

## 功能需求

### 帳號與權限

- **FR-A01**: WHEN 使用者登入, THE SYSTEM SHALL 驗證帳密

Given 已註冊使用者, When 登入, Then 進入首頁

## 使用者旅程

### 工程師開案
內容
"""
    result = vrf.run(_write(tmp_path, body))
    assert result["checks"]["scenarios"]["groups"] == 1
    assert result["checks"]["scenarios"]["missing"] == []
    assert result["checks"]["journeys"]["ok"] is True


def test_missing_journeys_and_glossary_fail(tmp_path):
    body = GOOD.replace("## User Journeys", "## Notes")
    result = vrf.run(_write(tmp_path, body, glossary=False))
    assert result["checks"]["journeys"]["ok"] is False
    assert result["checks"]["glossary"]["ok"] is False
    assert result["passed"] is False


def test_missing_requirements_file_fails(tmp_path):
    result = vrf.run(str(tmp_path))
    assert result["passed"] is False


def test_template_placeholder_scenario_does_not_count(tmp_path):
    body = GOOD.replace("- **Given** a logged-in engineer", "- **Given** [initial state]")
    body = body.replace("- **When** they submit the form", "- **When** [action]")
    body = body.replace("- **Then** the case appears in the list", "- **Then** [observable outcome]")
    result = vrf.run(_write(tmp_path, body))
    assert result["checks"]["scenarios"]["missing"] == ["SL-1 — Case creation"]
