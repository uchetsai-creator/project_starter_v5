"""Tests for the mcp_tools.py prototype — proves the tool-schema layer is real and
correct (dispatch() delegates to the actual verify_docs.run_audit() / verify_content.audit()
core functions and returns JSON-serializable data), without needing the `mcp` package, a
server process, or a client. Run against examples/web-app/docs — a real, filled fixture —
rather than an empty directory, so the results reflect actual audit behavior.
"""
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "templates" / "script" / "framework"))

import mcp_tools  # noqa: E402

_WEB_APP_DOCS = str(REPO_ROOT / "examples" / "web-app" / "docs")


def test_tools_list_has_expected_schemas():
    names = {t["name"] for t in mcp_tools.TOOLS}
    assert names == {"verify_docs", "verify_content"}
    for tool in mcp_tools.TOOLS:
        assert "description" in tool and tool["description"]
        schema = tool["inputSchema"]
        assert schema["type"] == "object"
        assert "project_type" in schema["properties"]
        assert "project_type" in schema["required"]


def test_dispatch_verify_docs_against_real_fixture():
    result = mcp_tools.dispatch(
        "verify_docs", {"project_type": "web-app", "docs_dir": _WEB_APP_DOCS},
    )
    assert result["project_type"] == "web-app"
    assert isinstance(result["results"], list) and result["results"]
    # every entry must be plain JSON-serializable data — proves this is a real
    # dict-in/dict-out boundary, not something that happens to work by accident
    json.dumps(result)
    statuses = {r["status"] for r in result["results"]}
    assert "present" in statuses  # the fixture has real filled docs


def test_dispatch_verify_content_against_real_fixture():
    result = mcp_tools.dispatch(
        "verify_content", {"project_type": "web-app", "docs_dir": _WEB_APP_DOCS},
    )
    assert result["project_type"] == "web-app"
    assert isinstance(result["documents"], list) and result["documents"]
    json.dumps(result)


def test_dispatch_unknown_tool_raises_tool_error():
    with pytest.raises(mcp_tools.ToolError, match="unknown tool"):
        mcp_tools.dispatch("not_a_real_tool", {})


def test_dispatch_missing_project_type_raises_tool_error():
    with pytest.raises(mcp_tools.ToolError, match="project_type is required"):
        mcp_tools.dispatch("verify_docs", {"docs_dir": _WEB_APP_DOCS})


def test_dispatch_invalid_project_type_raises_tool_error():
    with pytest.raises(mcp_tools.ToolError, match="unknown project type"):
        mcp_tools.dispatch(
            "verify_docs", {"project_type": "not-a-real-type", "docs_dir": _WEB_APP_DOCS},
        )


def test_dispatch_missing_docs_dir_raises_tool_error():
    with pytest.raises(mcp_tools.ToolError, match="docs directory not found"):
        mcp_tools.dispatch(
            "verify_docs", {"project_type": "web-app", "docs_dir": "/no/such/path"},
        )


def test_dispatch_check_content_flag_adds_content_field():
    result = mcp_tools.dispatch(
        "verify_docs",
        {"project_type": "web-app", "docs_dir": _WEB_APP_DOCS, "check_content": True},
    )
    present_required = [
        r for r in result["results"] if r["status"] == "present" and "content" in r
    ]
    assert present_required, "check_content=True should attach a content quality field"


# ---------------------------------------------------------------------------
# doc_profile (lite/full) -- explicit argument, since in-process dispatch() calls don't
# change cwd the way a subprocess-based CLI test would to exercise auto-detection
# ---------------------------------------------------------------------------

def test_dispatch_verify_docs_explicit_lite_profile():
    result = mcp_tools.dispatch(
        "verify_docs",
        {"project_type": "web-app", "docs_dir": _WEB_APP_DOCS, "doc_profile": "lite"},
    )
    assert result["doc_profile"] == "lite"
    json.dumps(result)


def test_dispatch_verify_docs_explicit_full_profile():
    result = mcp_tools.dispatch(
        "verify_docs",
        {"project_type": "web-app", "docs_dir": _WEB_APP_DOCS, "doc_profile": "full"},
    )
    assert result["doc_profile"] == "full"


def test_dispatch_verify_content_explicit_lite_profile_excludes_downgraded_docs():
    result = mcp_tools.dispatch(
        "verify_content",
        {"project_type": "web-app", "docs_dir": _WEB_APP_DOCS, "doc_profile": "lite"},
    )
    assert result["doc_profile"] == "lite"
    audited_names = {d["name"] for d in result["documents"]}
    assert "permissions.md" not in audited_names
