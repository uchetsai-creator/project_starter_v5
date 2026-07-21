import json
import sys
from pathlib import Path

import pytest

sys.path.insert(
    0,
    str(Path(__file__).resolve().parent.parent.parent / "templates/script/validators"),
)
from _verify_common import _append_telemetry, _is_placeholder, _section_body


# ---------------------------------------------------------------------------
# _is_placeholder — positive cases
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("text", [
    "<!-- TODO: fill this in -->",
    "<!-- todo: missing -->",
    "<!-- TBD -->",
    "_TBD_",
    "[placeholder]",
    "[PLACEHOLDER]",
    "[your company name]",
    "[your project description]",
    "[insert description here]",
    "[describe the system]",
    "[add more detail]",
    "[fill in the blanks]",
    "[e.g. some example]",
    "[Component]",
    "[Method]",
    "[/path]",
    "[FunctionName]",
    "[MODEL]",
    "[Stage Name here]",
    "[Flow Name here]",
    "[module name]",
    "actualFunctionName",
    "path/to/file",
    "   _   ",
    "   ...   ",
])
def test_is_placeholder_detects_pattern(text):
    assert _is_placeholder(text) is True


# ---------------------------------------------------------------------------
# _is_placeholder — negative cases (real content)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("text", [
    "The pipeline ingests data from S3 every hour.",
    "## Architecture\n\nThis service exposes a REST API.",
    "Handles authentication via OAuth2.",
    "See `docs/api-contract.md` for schema.",
    "Version 2.3.1 released on 2025-01-15.",
])
def test_is_placeholder_passes_real_content(text):
    assert _is_placeholder(text) is False


# ---------------------------------------------------------------------------
# _section_body
# ---------------------------------------------------------------------------

_DOC = """\
# Title

Intro text.

## Section A

Body of A.
More A content.

## Section B

Body of B.

### Sub-section B1

Sub content.

## Section C

Body of C.
"""


def test_section_body_returns_body():
    body = _section_body(_DOC, r"^## Section A")
    assert body is not None
    assert "Body of A." in body
    assert "More A content." in body


def test_section_body_stops_at_same_level_heading():
    body = _section_body(_DOC, r"^## Section A")
    assert "Section B" not in body


def test_section_body_includes_sub_headings():
    body = _section_body(_DOC, r"^## Section B")
    assert "Sub-section B1" in body
    assert "Sub content." in body


def test_section_body_returns_none_when_absent():
    body = _section_body(_DOC, r"^## Nonexistent Section")
    assert body is None


def test_section_body_returns_rest_when_last_section():
    body = _section_body(_DOC, r"^## Section C")
    assert body is not None
    assert "Body of C." in body


def test_section_body_case_insensitive():
    body = _section_body(_DOC, r"^## section a")
    assert body is not None
    assert "Body of A." in body


# ---------------------------------------------------------------------------
# _section_body — list[str] input
# ---------------------------------------------------------------------------

_DOC_LINES = _DOC.splitlines()


def test_section_body_list_returns_list():
    result = _section_body(_DOC_LINES, r"^## Section A")
    assert isinstance(result, list), "expected list[str] when input is list[str]"


def test_section_body_list_returns_none_when_absent():
    result = _section_body(_DOC_LINES, r"^## Nonexistent")
    assert result is None


def test_section_body_list_contains_body_lines():
    result = _section_body(_DOC_LINES, r"^## Section A")
    assert result is not None
    joined = "\n".join(result)
    assert "Body of A." in joined
    assert "More A content." in joined


def test_section_body_list_stops_at_same_level():
    result = _section_body(_DOC_LINES, r"^## Section A")
    assert result is not None
    joined = "\n".join(result)
    assert "Section B" not in joined


def test_section_body_list_includes_sub_headings():
    result = _section_body(_DOC_LINES, r"^## Section B")
    assert result is not None
    joined = "\n".join(result)
    assert "Sub-section B1" in joined
    assert "Sub content." in joined


# ---------------------------------------------------------------------------
# _append_telemetry — dict style and positional-args style
# ---------------------------------------------------------------------------

def test_append_telemetry_dict_style(tmp_path, monkeypatch):
    """dict argument creates telemetry entry verbatim."""
    monkeypatch.chdir(tmp_path)
    entry = {'script': 'verify_docs', 'project_type': 'web-app', 'status': 'pass', 'ts': '2026-01-01T00:00:00Z'}
    _append_telemetry(entry)
    telemetry_file = tmp_path / '.ai' / 'telemetry' / 'validation-result.json'
    assert telemetry_file.exists()
    rows = json.loads(telemetry_file.read_text())
    assert isinstance(rows, list)
    assert len(rows) == 1
    assert rows[0] == entry


def test_append_telemetry_positional_style(tmp_path, monkeypatch):
    """Positional-args call (script, project_type, status, ts) creates correct entry."""
    monkeypatch.chdir(tmp_path)
    _append_telemetry('verify_acceptance', 'cli-tool', 'fail', '2026-06-01T12:00:00Z')
    telemetry_file = tmp_path / '.ai' / 'telemetry' / 'validation-result.json'
    assert telemetry_file.exists()
    rows = json.loads(telemetry_file.read_text())
    assert isinstance(rows, list)
    assert len(rows) == 1
    assert rows[0] == {
        'script': 'verify_acceptance',
        'project_type': 'cli-tool',
        'status': 'fail',
        'ts': '2026-06-01T12:00:00Z',
    }


def test_append_telemetry_accumulates_entries(tmp_path, monkeypatch):
    """Multiple calls append rows; dict and positional styles coexist."""
    monkeypatch.chdir(tmp_path)
    _append_telemetry({'script': 'verify_docs', 'status': 'pass'})
    _append_telemetry('verify_acceptance', 'web-app', 'pass', '2026-01-01T00:00:00Z')
    telemetry_file = tmp_path / '.ai' / 'telemetry' / 'validation-result.json'
    rows = json.loads(telemetry_file.read_text())
    assert len(rows) == 2
    assert rows[0]['script'] == 'verify_docs'
    assert rows[1]['script'] == 'verify_acceptance'
