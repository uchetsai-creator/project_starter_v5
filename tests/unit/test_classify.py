import importlib.util
from pathlib import Path

import pytest

_bc_path = Path(__file__).resolve().parent.parent.parent / "build-context.py"
_spec = importlib.util.spec_from_file_location("build_context", _bc_path)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
_classify = _mod._classify


# ---------------------------------------------------------------------------
# Basic classification
# ---------------------------------------------------------------------------

def test_required_when_type_in_required_for():
    meta = {"required_for": ["web-app"], "optional_for": []}
    assert _classify("doc", meta, "web-app", None) == "required"


def test_if_present_when_type_in_optional_for_no_task_type():
    meta = {"required_for": [], "optional_for": ["web-app"]}
    assert _classify("doc", meta, "web-app", None) == "if_present"


def test_skip_when_type_not_in_either():
    meta = {"required_for": ["cli-tool"], "optional_for": ["library"]}
    assert _classify("doc", meta, "web-app", None) == "skip"


# ---------------------------------------------------------------------------
# sprint-end promotes optional → required
# ---------------------------------------------------------------------------

def test_sprint_end_promotes_optional_to_required():
    meta = {"required_for": [], "optional_for": ["data-pipeline"]}
    assert _classify("doc", meta, "data-pipeline", "sprint-end") == "required"


def test_sprint_end_keeps_required_as_required():
    meta = {"required_for": ["data-pipeline"], "optional_for": []}
    assert _classify("doc", meta, "data-pipeline", "sprint-end") == "required"


# ---------------------------------------------------------------------------
# task_types field filtering (Phase 60)
# ---------------------------------------------------------------------------

def test_task_type_in_task_types_returns_if_present():
    meta = {"required_for": [], "optional_for": ["web-app"], "task_types": ["feature", "bug-fix"]}
    assert _classify("doc", meta, "web-app", "feature") == "if_present"


def test_task_type_not_in_task_types_returns_skip():
    meta = {"required_for": [], "optional_for": ["web-app"], "task_types": ["feature"]}
    assert _classify("doc", meta, "web-app", "pipeline-stage") == "skip"


def test_no_task_types_field_returns_if_present():
    meta = {"required_for": [], "optional_for": ["web-app"]}
    assert _classify("doc", meta, "web-app", "feature") == "if_present"


# ---------------------------------------------------------------------------
# Hybrid type (data-pipeline+web-app)
# ---------------------------------------------------------------------------

def test_hybrid_required_if_any_part_matches_required():
    meta = {"required_for": ["web-app"], "optional_for": []}
    assert _classify("doc", meta, "data-pipeline+web-app", None) == "required"


def test_hybrid_required_if_first_part_matches_required():
    meta = {"required_for": ["data-pipeline"], "optional_for": []}
    assert _classify("doc", meta, "data-pipeline+web-app", None) == "required"


def test_hybrid_optional_if_part_matches_optional():
    meta = {"required_for": [], "optional_for": ["web-app"]}
    assert _classify("doc", meta, "data-pipeline+web-app", None) == "if_present"


def test_hybrid_skip_if_no_part_matches():
    meta = {"required_for": ["cli-tool"], "optional_for": ["library"]}
    assert _classify("doc", meta, "data-pipeline+web-app", None) == "skip"


# ---------------------------------------------------------------------------
# All 9 VALID_TYPES pass through required path
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("pt", [
    "web-app", "cli-tool", "library", "data-pipeline",
    "ml-pipeline", "microservices", "llm-app", "iac", "mobile-app",
])
def test_required_for_each_valid_type(pt):
    meta = {"required_for": [pt], "optional_for": []}
    assert _classify("doc", meta, pt, None) == "required"


@pytest.mark.parametrize("pt", [
    "web-app", "cli-tool", "library", "data-pipeline",
    "ml-pipeline", "microservices", "llm-app", "iac", "mobile-app",
])
def test_optional_for_each_valid_type(pt):
    meta = {"required_for": [], "optional_for": [pt]}
    assert _classify("doc", meta, pt, None) == "if_present"
