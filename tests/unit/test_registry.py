"""Tests for _registry.py's lite/full doc profile support (build_matrix/build_type_docs
lite= parameter) — a small synthetic registry, not the real 40-document one, so these stay
fast and focused on the downgrade rule itself rather than any specific document's real
classification.
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "templates" / "script" / "validators"))

from _registry import VALID_TYPES, build_matrix, build_type_docs, get_universal_docs  # noqa: E402

_T1, _T2 = VALID_TYPES[0], VALID_TYPES[1]

_REGISTRY = {
    "always-required": {
        "required_for": [_T1, _T2],
        "optional_for": [],
    },
    "downgradable": {
        "required_for": [_T1, _T2],
        "optional_for": [],
        "lite_downgrade": "optional",
    },
    "already-optional-elsewhere": {
        "required_for": [_T1],
        "optional_for": [_T2],
        "lite_downgrade": "optional",
    },
    "never-applies-to-t1": {
        "required_for": [_T2],
        "optional_for": [],
        "lite_downgrade": "optional",
    },
}

_UNIVERSAL_REGISTRY = {
    "universal-plain": {"required_for": list(VALID_TYPES)},
    "universal-downgradable": {"required_for": list(VALID_TYPES), "lite_downgrade": "optional"},
    "not-universal": {"required_for": [_T1]},
}


def test_get_universal_docs_full_includes_downgradable():
    result = get_universal_docs(_UNIVERSAL_REGISTRY, lite=False)
    assert "universal-plain.md" in result
    assert "universal-downgradable.md" in result
    assert "not-universal.md" not in result


def test_get_universal_docs_lite_excludes_downgradable():
    result = get_universal_docs(_UNIVERSAL_REGISTRY, lite=True)
    assert "universal-plain.md" in result
    assert "universal-downgradable.md" not in result


def test_full_matrix_ignores_lite_downgrade():
    matrix = build_matrix(_REGISTRY, lite=False)
    assert matrix["downgradable.md"][VALID_TYPES.index(_T1)] == "R"
    assert matrix["downgradable.md"][VALID_TYPES.index(_T2)] == "R"


def test_lite_matrix_downgrades_required_to_optional():
    matrix = build_matrix(_REGISTRY, lite=True)
    assert matrix["downgradable.md"][VALID_TYPES.index(_T1)] == "O"
    assert matrix["downgradable.md"][VALID_TYPES.index(_T2)] == "O"


def test_lite_matrix_does_not_touch_docs_without_lite_downgrade():
    matrix = build_matrix(_REGISTRY, lite=True)
    assert matrix["always-required.md"][VALID_TYPES.index(_T1)] == "R"
    assert matrix["always-required.md"][VALID_TYPES.index(_T2)] == "R"


def test_lite_matrix_does_not_touch_types_already_optional_or_na():
    """lite_downgrade only affects types where the doc would be Required -- a type where
    it's already Optional (or N/A) must stay exactly as it was."""
    matrix = build_matrix(_REGISTRY, lite=True)
    # T1: required -> downgraded to O; T2: was already optional -> stays O either way
    row = matrix["already-optional-elsewhere.md"]
    assert row[VALID_TYPES.index(_T1)] == "O"
    assert row[VALID_TYPES.index(_T2)] == "O"

    # a type never in required_for/optional_for at all must remain N regardless of lite
    matrix_full = build_matrix(_REGISTRY, lite=False)
    for t in VALID_TYPES[2:]:
        idx = VALID_TYPES.index(t)
        assert matrix["already-optional-elsewhere.md"][idx] == "N"
        assert matrix_full["already-optional-elsewhere.md"][idx] == "N"


def test_build_type_docs_full_includes_downgradable_docs():
    type_docs = build_type_docs(_REGISTRY, lite=False)
    assert "downgradable.md" in type_docs[_T1]


def test_build_type_docs_lite_excludes_downgradable_docs():
    type_docs = build_type_docs(_REGISTRY, lite=True)
    assert "downgradable.md" not in type_docs[_T1]
    assert "downgradable.md" not in type_docs[_T2]
    assert "always-required.md" in type_docs[_T1]  # unaffected doc still required
