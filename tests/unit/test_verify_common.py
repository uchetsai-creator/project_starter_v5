import sys
from pathlib import Path

import pytest

sys.path.insert(
    0,
    str(Path(__file__).resolve().parent.parent.parent / "templates/script/validators"),
)
from _verify_common import _is_placeholder, _section_body


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
