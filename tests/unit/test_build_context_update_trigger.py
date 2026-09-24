"""build-context.py prints each candidate document's update_trigger.

The breakdown discussion (guidance/approach-proposal.md) compares the chosen approach with each
document's update_trigger. If the candidate list does not show it, the comparison depends on
someone opening document-registry.yaml separately and is easily skipped -- so the trigger is
printed right under each document, in both the Required and If Present sections.
"""
import importlib.util
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_bc_path = REPO_ROOT / "build-context.py"
_spec = importlib.util.spec_from_file_location("build_context", _bc_path)
assert _spec is not None and _spec.loader is not None
bc = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(bc)


def _ctx(required=(), if_present=()):
    def entry(key, trigger):
        return {"key": key, "path": f"docs/{key}.md", "purpose": f"{key} purpose", "trigger": trigger, "priority": "high"}
    return {
        "project_type": "web-app", "task_type": "feature", "skipped": [],
        "required": [entry(k, t) for k, t in required],
        "if_present": [entry(k, t) for k, t in if_present],
    }


def test_required_documents_show_their_update_trigger():
    out = bc._render(_ctx(required=[("architecture", "system components or data-flow changes")]))
    assert "- docs/architecture.md   # architecture purpose\n    update when: system components or data-flow changes" in out


def test_if_present_documents_show_their_update_trigger():
    out = bc._render(_ctx(if_present=[("dependencies", "library or service added")]))
    assert "## Read (If Present)" in out
    assert "    update when: library or service added" in out


def test_document_without_a_trigger_prints_no_update_line():
    out = bc._render(_ctx(required=[("current-state", "")]))
    assert "update when" not in out


def _registry_triggers():
    import sys
    sys.path.insert(0, str(REPO_ROOT))
    from orchestrator import _load_yaml
    return {k: m.get("update_trigger", "") for k, m in _load_yaml(REPO_ROOT / "document-registry.yaml")["documents"].items()}


def test_every_registered_document_has_an_update_trigger():
    missing = [k for k, v in _registry_triggers().items() if not v.strip()]
    assert missing == []


@pytest.mark.parametrize("doc, phrase", [
    ("project-requirements", "scope, roles"),
    ("test-plan", "test scope"),
    ("dependencies", "external service"),
    ("api-contract", "error codes"),
    ("logging-spec", "new module"),
])
def test_triggers_cover_what_the_template_actually_holds(doc, phrase):
    """These triggers used to name only part of the document's scope (e.g. test-plan said 'strategy,
    tool, or CI gate' although it holds the Test Scope every new AC-XXX goes into), so a plain
    trigger-vs-approach comparison would miss a real update."""
    assert phrase in _registry_triggers()[doc].lower()


def test_triggers_are_single_line_strings():
    for key, trig in _registry_triggers().items():
        assert re.fullmatch(r"[^\n]+", trig), key
