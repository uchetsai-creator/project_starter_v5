"""Contract: guidance/decomposition/ has the shared method plus one file per project type, and
every type file gives the nouns common.md expects (observer, entry point, independent test, the
five artifact kinds with a prefix each). web-app must keep the DB / BE / FE prefixes that
run-verify.sh and the Milestone Documentation Sync trigger read."""
import importlib.util
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent.parent
_DIR = _ROOT / "guidance" / "decomposition"

_reg_spec = importlib.util.spec_from_file_location(
    "_registry", _ROOT / "templates" / "script" / "validators" / "_registry.py"
)
assert _reg_spec is not None and _reg_spec.loader is not None
_registry = importlib.util.module_from_spec(_reg_spec)
_reg_spec.loader.exec_module(_registry)
VALID_TYPES = list(_registry.VALID_TYPES)

KINDS = ("Contract", "State", "Logic", "Entry", "Guard")


def test_common_file_defines_all_levels_and_kinds():
    text = (_DIR / "common.md").read_text(encoding="utf-8")
    for heading in ("Level 1", "Level 2", "Level 3"):
        assert heading in text
    for kind in KINDS:
        assert f"**{kind}**" in text


@pytest.mark.parametrize("project_type", VALID_TYPES)
def test_type_file_exists_with_required_nouns(project_type):
    path = _DIR / f"{project_type}.md"
    assert path.exists(), f"guidance/decomposition/{project_type}.md missing"
    text = path.read_text(encoding="utf-8")
    for label in ("**Observer:**", "**Entry point:**", "**Independent Test:**", "## Artifact kinds"):
        assert label in text, f"{project_type}.md lacks {label}"
    for kind in KINDS:
        assert f"| {kind} |" in text, f"{project_type}.md has no row for {kind}"


def test_web_app_keeps_layer_prefixes():
    text = (_DIR / "web-app.md").read_text(encoding="utf-8")
    for prefix in ("`DB`", "`BE`", "`FE`"):
        assert prefix in text


def test_plan_template_points_to_decomposition_guidance():
    text = (_ROOT / "templates" / "project-plan.md").read_text(encoding="utf-8")
    assert "guidance/decomposition/common.md" in text
    assert "**Covers:**" in text
