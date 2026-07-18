"""
_utils.py — Shared utilities for spec_code adapters.

Import from here instead of defining locally:

    from _utils import _annotation_str
"""
from __future__ import annotations

import ast


def _annotation_str(node) -> str:
    """Convert an AST annotation node to a type string. Returns '' on failure."""
    if node is None:
        return ''
    try:
        return ast.unparse(node)
    except AttributeError:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Constant):
            return str(node.value)
        if isinstance(node, ast.Attribute):
            return f"{_annotation_str(node.value)}.{node.attr}"
        return ''
