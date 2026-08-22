#!/usr/bin/env python3
"""
mcp_tools.py — PROTOTYPE tool-schema layer for a future MCP server. Not a running server:
no `mcp` package dependency, no transport, no client wiring. This module only proves out
the thin layer a real MCP server would need on top of the validators' already-clean core
functions (verify_docs.run_audit(), verify_content.audit()) — a JSON-Schema tool definition
plus a dict-in/dict-out handler per tool, both directly unit-testable with no protocol
involved. Lives in templates/script/framework/ deliberately — the one subdirectory init.py's
--init already excludes via shutil.ignore_patterns("framework") from what gets copied into a
user project's docs/script/ — same treatment as verify_framework.py, this is framework-repo-only
until a full server is actually built (deliberately deferred — see CHANGELOG.md for why).

Why this exists as a separate, tested-but-inert layer instead of just noting "MCP would be
easy here" in a comment: `run_audit()` and `audit()` already returning plain, JSON-serializable
data was a real (happy) finding, not something assumed going in — wrapping them here and
testing the wrapper is the concrete proof, not just an assertion.

To actually turn this into a live server later: wire TOOLS as the response to MCP's
`tools/list` request, and dispatch(name, arguments) as the handler for `tools/call`, using
the official `mcp` Python SDK's server scaffolding (`pip install mcp`) — this file's contents
would not need to change, only a new thin entry point on top of it.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

_VALIDATORS_DIR = Path(__file__).resolve().parent.parent / "validators"
if str(_VALIDATORS_DIR) not in sys.path:
    sys.path.insert(0, str(_VALIDATORS_DIR))

from _registry import VALID_TYPES  # noqa: E402
from _verify_common import read_doc_profile  # noqa: E402
from verify_content import audit as verify_content_audit  # noqa: E402
from verify_docs import run_audit  # noqa: E402


class ToolError(Exception):
    """Raised for a bad tool call (unknown tool, invalid arguments) — the MCP-layer
    equivalent of the argparse errors verify_docs.py's own main() raises via sys.exit(2)."""


TOOLS: list[dict] = [
    {
        "name": "verify_docs",
        "description": (
            "Audit document completeness for a project_starter_v5 project: which "
            "Required/Optional documents exist, are missing, or are orphaned, and "
            "optionally their fill quality."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_type": {
                    "type": "string",
                    "description": (
                        "Project type, e.g. 'web-app' or a hybrid 'data-pipeline+web-app'."
                    ),
                },
                "docs_dir": {
                    "type": "string",
                    "description": "Path to the docs/ directory.",
                    "default": "docs",
                },
                "check_content": {
                    "type": "boolean",
                    "description": "Also check fill quality (placeholders, required sections).",
                    "default": False,
                },
                "doc_profile": {
                    "type": "string",
                    "enum": ["lite", "full"],
                    "description": (
                        "Which required-doc set to audit against. Omit to auto-detect "
                        "from .project-starter.yml -> doc_profile (defaults to 'full' if "
                        "unset there too) — same default every CLI invocation uses."
                    ),
                },
            },
            "required": ["project_type"],
        },
    },
    {
        "name": "verify_content",
        "description": (
            "Audit content quality of all Required documents and module flow files for a "
            "project_starter_v5 project (deeper than verify_docs's presence-only check)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_type": {"type": "string"},
                "docs_dir": {"type": "string", "default": "docs"},
                "doc_profile": {
                    "type": "string",
                    "enum": ["lite", "full"],
                    "description": "Same auto-detect-if-omitted behavior as verify_docs's doc_profile.",
                },
            },
            "required": ["project_type"],
        },
    },
]


def _parse_types(project_type: str) -> list[str]:
    types = [t.strip() for t in project_type.split("+")]
    invalid = [t for t in types if t not in VALID_TYPES]
    if invalid:
        raise ToolError(
            f"unknown project type(s): {', '.join(invalid)} — valid: {', '.join(VALID_TYPES)}"
        )
    return types


def _resolve_lite(arguments: dict) -> bool:
    """Explicit doc_profile argument wins; otherwise auto-detect from
    .project-starter.yml, same default every CLI invocation of these scripts uses."""
    requested = arguments.get("doc_profile")
    if requested in ("lite", "full"):
        return requested == "lite"
    return read_doc_profile() == "lite"


def _handle_verify_docs(arguments: dict) -> dict:
    project_type = arguments.get("project_type")
    if not project_type:
        raise ToolError("project_type is required")
    docs_dir = arguments.get("docs_dir", "docs")
    if not os.path.isdir(docs_dir):
        raise ToolError(f"docs directory not found: {docs_dir}")

    types = _parse_types(project_type)
    lite = _resolve_lite(arguments)
    results = run_audit(
        types, docs_dir, check_content=bool(arguments.get("check_content", False)), lite=lite,
    )
    return {
        "project_type": project_type,
        "doc_profile": "lite" if lite else "full",
        "results": results,
    }


def _handle_verify_content(arguments: dict) -> dict:
    project_type = arguments.get("project_type")
    if not project_type:
        raise ToolError("project_type is required")
    docs_dir = arguments.get("docs_dir", "docs")
    if not os.path.isdir(docs_dir):
        raise ToolError(f"docs directory not found: {docs_dir}")

    types = _parse_types(project_type)
    lite = _resolve_lite(arguments)
    doc_results, module_results = verify_content_audit(types, docs_dir, str(_VALIDATORS_DIR), lite=lite)
    return {
        "project_type": project_type,
        "doc_profile": "lite" if lite else "full",
        "documents": doc_results,
        "modules": module_results,
    }


_HANDLERS = {
    "verify_docs": _handle_verify_docs,
    "verify_content": _handle_verify_content,
}


def dispatch(name: str, arguments: dict) -> dict:
    """dict-in/dict-out call matching the shape an MCP server's tools/call handler would
    use — arguments and return value are both plain, JSON-serializable dicts, deliberately,
    so this can be unit-tested without any MCP transport."""
    handler = _HANDLERS.get(name)
    if handler is None:
        raise ToolError(f"unknown tool: {name!r} — available: {', '.join(_HANDLERS)}")
    return handler(arguments)
