"""
_utils.py — Shared utilities for spec_code adapters.

Import from here instead of defining locally:

    from _utils import _annotation_str
    from _utils import _HTTP_METHODS, _parse_field_table
    from _utils import _PLACEHOLDER_NAMES, _parse_schema_value
    from _utils import _PLACEHOLDER_CMD_NAMES, _clean_flag_name
    from _utils import _parse_config_table, _parse_params_table
"""
from __future__ import annotations

import ast
import re

from _base import NormalizedField


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


# ── HTTP / Web API ────────────────────────────────────────────────────────────

_HTTP_METHODS = frozenset({'GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'})


def _parse_field_table(section: str, header: str) -> list[NormalizedField]:
    """Parse a Markdown table under `#### {header}` into NormalizedField list."""
    h = re.search(rf'^#### {re.escape(header)}', section, re.MULTILINE)
    if not h:
        return []
    table_text = section[h.end():]
    next_h = re.search(r'^#{3,4} ', table_text, re.MULTILINE)
    if next_h:
        table_text = table_text[:next_h.start()]

    fields: list[NormalizedField] = []
    for row in re.finditer(r'(?m)^\|(.+)\|$', table_text):
        cols = [c.strip().strip('`') for c in row.group(1).split('|')]
        if len(cols) < 2:
            continue
        name = cols[0]
        type_str = cols[1] if len(cols) > 1 else ''
        if not name or re.match(r'^[-:]+$', name) or name.lower() in (
            'field', 'name', 'parameter', 'property'
        ):
            continue
        fields.append(NormalizedField(name=name, type=type_str))
    return fields


# ── Pipeline ──────────────────────────────────────────────────────────────────

_PLACEHOLDER_NAMES = frozenset({'stage name', '[stage name]', 'stage', ''})


def _parse_schema_value(value: str) -> list[NormalizedField]:
    """Parse 'field: type, field2: type2' or 'field (type)' patterns."""
    fields = []
    for part in re.split(r'[,\n;]', value):
        part = part.strip().strip('`')
        m = re.match(r'([a-zA-Z_]\w*)\s*[:(]\s*(\w[\w\[\], ]*)', part)
        if m:
            fields.append(NormalizedField(name=m.group(1).strip(), type=m.group(2).strip()))
    return fields


# ── CLI ───────────────────────────────────────────────────────────────────────

_PLACEHOLDER_CMD_NAMES = frozenset({'subcommand', '[subcommand]', 'tool-name', ''})


def _clean_flag_name(raw: str) -> str:
    """Strip backticks, leading dashes, and angle brackets."""
    return re.sub(r'[`<>]', '', raw).strip().lstrip('-').replace('-', '_')


# ── IaC ───────────────────────────────────────────────────────────────────────

def _parse_config_table(section: str) -> list[str]:
    """Return config key names from a '#### Configuration' Markdown table."""
    h = re.search(r'^#### Configuration', section, re.MULTILINE)
    if not h:
        return []
    table_text = section[h.end():]
    next_h = re.search(r'^#{3,4} ', table_text, re.MULTILINE)
    if next_h:
        table_text = table_text[:next_h.start()]

    keys: list[str] = []
    for row in re.finditer(r'(?m)^\|(.+)\|$', table_text):
        cols = [c.strip().strip('`') for c in row.group(1).split('|')]
        key = cols[0] if cols else ''
        if not key or re.match(r'^[-:]+$', key) or key.lower() in (
            'key', 'name', 'attribute', 'property'
        ):
            continue
        keys.append(key)
    return keys


# ── Library / LLM ─────────────────────────────────────────────────────────────

def _parse_params_table(section: str) -> list[NormalizedField]:
    """Parse a '#### Parameters' Markdown table into NormalizedField list."""
    h = re.search(r'^#### Parameters', section, re.MULTILINE)
    if not h:
        return []
    table_text = section[h.end():]
    next_h = re.search(r'^#{3,4} ', table_text, re.MULTILINE)
    if next_h:
        table_text = table_text[:next_h.start()]

    fields: list[NormalizedField] = []
    for row in re.finditer(r'(?m)^\|(.+)\|$', table_text):
        cols = [c.strip().strip('`') for c in row.group(1).split('|')]
        if len(cols) < 2:
            continue
        name, type_str = cols[0], cols[1] if len(cols) > 1 else ''
        if not name or re.match(r'^[-:]+$', name) or name.lower() in (
            'name', 'parameter', 'param'
        ):
            continue
        fields.append(NormalizedField(name=name, type=type_str))
    return fields
