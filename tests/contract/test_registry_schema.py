import re
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(_REPO_ROOT / "templates/script/validators"))

from _registry import VALID_TYPES, load_registry


# ---------------------------------------------------------------------------
# Contract 2 — registry schema invariants
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
# Regression guard — Phase 57: orchestrator.py missing `import re`
# ---------------------------------------------------------------------------

def test_orchestrator_imports_re():
    source = (_REPO_ROOT / "orchestrator.py").read_text(encoding="utf-8")
    assert re.search(r"(?m)^import re\b", source), "orchestrator.py is missing top-level `import re`"
