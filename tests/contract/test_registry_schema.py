import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT / "templates/script/validators"))

from _registry import VALID_TYPES, load_registry
from verify_registry import _validate_entry, validate


# ---------------------------------------------------------------------------
# Contract 2 — registry schema invariants (legacy field checks)
# ---------------------------------------------------------------------------

def test_registry_all_entries_have_required_fields():
    for key, meta in load_registry().items():
        assert "file" in meta, f"{key} missing 'file'"
        assert "path" in meta, f"{key} missing 'path'"
        assert isinstance(meta.get("required_for", []), list), f"{key} 'required_for' must be list"
        assert isinstance(meta.get("optional_for", []), list), f"{key} 'optional_for' must be list"
        assert meta.get("context_priority") in ("high", "medium", "low"), f"{key} invalid priority"


def test_registry_valid_types_only():
    for key, meta in load_registry().items():
        for pt in meta.get("required_for", []) + meta.get("optional_for", []):
            assert pt in VALID_TYPES, f"{key}: unknown project type '{pt}'"


# ---------------------------------------------------------------------------
# Contract 2b — full schema validation via verify_registry.py
# ---------------------------------------------------------------------------

def test_registry_passes_full_schema_validation():
    registry_path = _REPO_ROOT / "document-registry.yaml"
    errors = validate(registry_path)
    assert not errors, (
        "Registry schema violations:\n"
        + "\n".join(f"  {k}: {e}" for k, errs in errors.items() for e in errs)
    )


def test_registry_all_entries_have_pdf_field():
    for key, meta in load_registry().items():
        assert "pdf" in meta, f"{key} missing 'pdf'"
        assert isinstance(meta["pdf"], bool), f"{key} 'pdf' must be boolean"


def test_registry_all_entries_have_pdf_chapter_field():
    for key, meta in load_registry().items():
        assert "pdf_chapter" in meta, f"{key} missing 'pdf_chapter'"
        if meta["pdf"]:
            assert meta["pdf_chapter"] in ("introduction", "plan", "design", "build", "test", "deployment"), \
                f"{key} 'pdf_chapter' must be a valid chapter when pdf=true"
        else:
            assert meta["pdf_chapter"] is None, \
                f"{key} 'pdf_chapter' must be null when pdf=false"


def test_registry_all_entries_have_audience_field():
    for key, meta in load_registry().items():
        assert "audience" in meta, f"{key} missing 'audience'"
        assert meta["audience"] in ("internal", "external"), \
            f"{key} 'audience' must be internal|external"


def test_registry_all_entries_have_required_sections_field():
    for key, meta in load_registry().items():
        assert "required_sections" in meta, f"{key} missing 'required_sections'"
        assert isinstance(meta["required_sections"], list), \
            f"{key} 'required_sections' must be a list"


def test_registry_all_entries_have_update_trigger_field():
    for key, meta in load_registry().items():
        assert "update_trigger" in meta, f"{key} missing 'update_trigger'"
        assert isinstance(meta["update_trigger"], str), \
            f"{key} 'update_trigger' must be a string"
        assert meta["update_trigger"].strip(), f"{key} 'update_trigger' must not be empty"


# ---------------------------------------------------------------------------
# Contract 2c — verify_registry.py rejects malformed entries
# ---------------------------------------------------------------------------

def test_validate_entry_catches_bad_project_type():
    meta = {
        "file": "test.md",
        "path": "specs/test.md",
        "context_priority": "high",
        "pdf": True,
        "pdf_chapter": "design",
        "audience": "internal",
        "required_sections": [],
        "update_trigger": "when things change",
        "required_for": ["webapp"],  # bad — should be "web-app"
    }
    errors = _validate_entry("test", meta)
    assert any("webapp" in e for e in errors)


def test_validate_entry_catches_missing_required_field():
    meta = {
        "file": "test.md",
        "path": "specs/test.md",
        "context_priority": "high",
        # pdf missing (also pdf_chapter missing — both caught as missing required fields)
        "audience": "internal",
        "required_sections": [],
        "update_trigger": "when things change",
    }
    errors = _validate_entry("test", meta)
    assert any("pdf" in e for e in errors)


def test_validate_entry_catches_bad_priority():
    meta = {
        "file": "test.md",
        "path": "specs/test.md",
        "context_priority": "critical",  # invalid
        "pdf": False,
        "pdf_chapter": None,
        "audience": "internal",
        "required_sections": [],
        "update_trigger": "when things change",
    }
    errors = _validate_entry("test", meta)
    assert any("context_priority" in e for e in errors)


def test_validate_entry_catches_bad_audience():
    meta = {
        "file": "test.md",
        "path": "specs/test.md",
        "context_priority": "low",
        "pdf": False,
        "pdf_chapter": None,
        "audience": "public",  # invalid
        "required_sections": [],
        "update_trigger": "when things change",
    }
    errors = _validate_entry("test", meta)
    assert any("audience" in e for e in errors)


def test_validate_entry_catches_pdf_not_boolean():
    meta = {
        "file": "test.md",
        "path": "specs/test.md",
        "context_priority": "low",
        "pdf": "yes",  # string instead of bool
        "pdf_chapter": "design",
        "audience": "internal",
        "required_sections": [],
        "update_trigger": "when things change",
    }
    errors = _validate_entry("test", meta)
    assert any("pdf" in e for e in errors)


def test_validate_entry_catches_file_without_md():
    meta = {
        "file": "test",  # missing .md
        "path": "specs/test.md",
        "context_priority": "low",
        "pdf": False,
        "pdf_chapter": None,
        "audience": "internal",
        "required_sections": [],
        "update_trigger": "when things change",
    }
    errors = _validate_entry("test", meta)
    assert any("file" in e for e in errors)


def test_validate_entry_catches_empty_update_trigger():
    meta = {
        "file": "test.md",
        "path": "specs/test.md",
        "context_priority": "low",
        "pdf": False,
        "pdf_chapter": None,
        "audience": "internal",
        "required_sections": [],
        "update_trigger": "   ",  # whitespace only
    }
    errors = _validate_entry("test", meta)
    assert any("update_trigger" in e for e in errors)


def test_validate_entry_passes_valid_entry():
    meta = {
        "file": "test.md",
        "path": "specs/test.md",
        "required_for": ["web-app", "cli-tool"],
        "optional_for": ["library"],
        "context_priority": "high",
        "purpose": "Test document",
        "used_by": ["validator"],
        "related": ["other-doc"],
        "pdf": True,
        "pdf_chapter": "design",
        "audience": "external",
        "required_sections": ["Overview", "Usage"],
        "update_trigger": "when the test changes",
    }
    errors = _validate_entry("test", meta)
    assert not errors


def test_validate_entry_catches_bad_pdf_chapter():
    meta = {
        "file": "test.md",
        "path": "specs/test.md",
        "context_priority": "low",
        "pdf": True,
        "pdf_chapter": "summary",  # invalid chapter name
        "audience": "internal",
        "required_sections": [],
        "update_trigger": "when things change",
    }
    errors = _validate_entry("test", meta)
    assert any("pdf_chapter" in e for e in errors)


def test_validate_entry_catches_pdf_chapter_not_null_when_pdf_false():
    meta = {
        "file": "test.md",
        "path": "specs/test.md",
        "context_priority": "low",
        "pdf": False,
        "pdf_chapter": "design",  # must be null when pdf=false
        "audience": "internal",
        "required_sections": [],
        "update_trigger": "when things change",
    }
    errors = _validate_entry("test", meta)
    assert any("pdf_chapter" in e for e in errors)


def test_validate_entry_passes_pdf_false_with_null_chapter():
    meta = {
        "file": "test.md",
        "path": "specs/test.md",
        "context_priority": "low",
        "pdf": False,
        "pdf_chapter": None,
        "audience": "internal",
        "required_sections": [],
        "update_trigger": "when things change",
    }
    errors = _validate_entry("test", meta)
    assert not errors
