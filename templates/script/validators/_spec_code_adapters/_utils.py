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


# ── Output/return field resolution (shared by web-api + data-pipeline detectors) ──
#
# A bare return-type annotation (`-> dict`, `-> MyModel`) carries no field names, so
# it cannot be compared field-by-field against a spec's response/output table. These
# helpers make a best effort to resolve the actual field names a function returns:
#   1. the return annotation names a class defined in the same file (Pydantic
#      BaseModel, dataclass, or TypedDict-via-class-syntax) — use its annotated
#      attributes.
#   2. a `return` statement in the function body is a dict literal, a `jsonify(...)`
#      call wrapping one, a `(dict, status_code)` tuple, or a constructor call with
#      keyword arguments (e.g. `MyModel(status="ok")`) — use those keys/kwargs.
#   3. neither applies — return [] rather than a fabricated field, since a bare
#      scalar/opaque return has no named sub-fields to compare.

def _literal_type(node) -> str:
    """Best-effort type name for an AST literal value node. Returns '' if unknown."""
    if isinstance(node, ast.Constant):
        if isinstance(node.value, bool):
            return 'bool'
        if isinstance(node.value, int):
            return 'int'
        if isinstance(node.value, float):
            return 'float'
        if isinstance(node.value, str):
            return 'str'
    return ''


def _resolve_class_fields(tree, class_name: str) -> list[NormalizedField]:
    """Find a module-level class definition named `class_name` and return its
    annotated attributes (covers Pydantic BaseModel, dataclasses, TypedDict-via-class)."""
    if not class_name:
        return []
    for node in ast.walk(tree):
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return [
                NormalizedField(name=item.target.id, type=_annotation_str(item.annotation))
                for item in node.body
                if isinstance(item, ast.AnnAssign) and isinstance(item.target, ast.Name)
            ]
    return []


def _dict_literal_fields(dict_node: ast.Dict) -> list[NormalizedField]:
    return [
        NormalizedField(name=k.value, type=_literal_type(v))
        for k, v in zip(dict_node.keys, dict_node.values)
        if isinstance(k, ast.Constant) and isinstance(k.value, str)
    ]


def _call_kwarg_fields(call_node: ast.Call) -> list[NormalizedField]:
    return [
        NormalizedField(name=kw.arg, type=_literal_type(kw.value))
        for kw in call_node.keywords
        if kw.arg is not None
    ]


def _resolve_return_literal_fields(func_node) -> list[NormalizedField]:
    """Best-effort field names from a function's `return` statement(s): a dict
    literal, a `jsonify(...)`-wrapped dict, a `(dict, status_code)` tuple, or a
    constructor call with keyword arguments. Returns [] if none match."""
    seen: set[str] = set()
    fields: list[NormalizedField] = []

    for node in ast.walk(func_node):
        if not isinstance(node, ast.Return) or node.value is None:
            continue
        value = node.value
        if isinstance(value, ast.Tuple) and value.elts:
            value = value.elts[0]
        # Unwrap a single positional dict argument from any wrapping call —
        # jsonify(...), Response(...), JsonResponse(...), make_response(...), etc.
        # Keyed on argument shape, not the callable's name, so it isn't tied to
        # one framework's wrapper function.
        if (isinstance(value, ast.Call) and len(value.args) == 1
                and isinstance(value.args[0], ast.Dict) and not value.keywords):
            value = value.args[0]

        if isinstance(value, ast.Dict):
            candidates = _dict_literal_fields(value)
        elif isinstance(value, ast.Call):
            candidates = _call_kwarg_fields(value)
        else:
            candidates = []

        for f in candidates:
            if f.name not in seen:
                seen.add(f.name)
                fields.append(f)

    return fields


def _resolve_output_fields(tree, func_node) -> list[NormalizedField]:
    """Resolve a function's output/response field names — see module note above."""
    ret_node = getattr(func_node, 'returns', None)
    if ret_node is not None:
        ret_name = _annotation_str(ret_node)
        base_name = re.sub(r'^\w+\[(.+)\]$', r'\1', ret_name).strip()
        class_fields = _resolve_class_fields(tree, base_name)
        if class_fields:
            return class_fields
    return _resolve_return_literal_fields(func_node)


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
