"""
tool_schema.py — ToolSchemaDetector (+ legacy ToolSchemaAdapter) for project_starter_v5.

Phase 52.5: ToolSchemaDetector is the primary class — it receives pre-discovered
files from LLMAdapter and returns NormalizedTool objects.
ToolSchemaAdapter is kept as a backward-compatible shim.

Extracts NormalizedTool objects from:
  - Spec: llm-contract.md (### tool_name sections with #### Parameters tables)
  - Code: Python files — type-annotated functions with docstring Args: sections
          OR JSON files — OpenAI-compatible tool schema ({"name": ..., "parameters": {"properties": {...}}})

No comparison logic here. All comparison lives in verify_spec_code.py.
"""
from __future__ import annotations

import ast
import json
import os
import re

from _base import Detector, FrameworkAdapter, NormalizedField, NormalizedTool
from _utils import _annotation_str

_SKIP_PARAMS = frozenset({'self', 'cls', 'kwargs', 'args'})


def _parse_params_table(section: str) -> list[NormalizedField]:
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
        if not name or re.match(r'^[-:]+$', name) or name.lower() in ('name', 'parameter', 'param'):
            continue
        fields.append(NormalizedField(name=name, type=type_str))
    return fields


def _parse_docstring_args(docstring: str) -> list[NormalizedField]:
    """Extract parameter names from a Google-style or NumPy-style docstring."""
    fields: list[NormalizedField] = []
    args_m = re.search(r'Args:\s*\n(.*?)(?:\n\s*\n|\n\s*[A-Z][a-z]+:|\Z)',
                       docstring, re.DOTALL)
    if not args_m:
        return fields
    for line in args_m.group(1).splitlines():
        m = re.match(r'\s+(\w+)\s*(?:\(([^)]+)\))?:', line)
        if m:
            fields.append(NormalizedField(name=m.group(1), type=m.group(2) or ''))
    return fields


class ToolSchemaDetector(Detector):
    """
    Framework detector for AI / LLM App tool schemas (Phase 52.5).

    Receives pre-discovered .py and .json files from LLMAdapter.
    Returns NormalizedTool for each tool function or JSON schema entry.
    Must not perform file discovery.
    """

    def extract(self, files: list[str]) -> list[NormalizedTool]:
        tools: list[NormalizedTool] = []
        for fpath in files:
            if fpath.endswith('.json'):
                tools.extend(self._parse_json(fpath))
            elif fpath.endswith('.py'):
                tools.extend(self._parse_python(fpath))
        return tools

    def _parse_json(self, fpath: str) -> list[NormalizedTool]:
        try:
            with open(fpath, encoding='utf-8') as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            return []

        tools: list[NormalizedTool] = []
        entries = data if isinstance(data, list) else [data]
        for entry in entries:
            if not isinstance(entry, dict) or 'name' not in entry:
                continue
            props = (entry.get('parameters') or {}).get('properties') or {}
            params = [
                NormalizedField(name=k, type=(v.get('type') or '') if isinstance(v, dict) else '')
                for k, v in props.items()
            ]
            tools.append(NormalizedTool(name=entry['name'], parameters=params))
        return tools

    def _parse_python(self, fpath: str) -> list[NormalizedTool]:
        try:
            with open(fpath, encoding='utf-8') as f:
                source = f.read()
            tree = ast.parse(source, filename=fpath)
        except (OSError, SyntaxError):
            return []

        tools: list[NormalizedTool] = []
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if node.name.startswith('_'):
                continue

            params = [
                NormalizedField(name=a.arg, type=_annotation_str(a.annotation))
                for a in node.args.args
                if a.arg not in _SKIP_PARAMS
            ]

            if not any(p.type for p in params):
                docstring = ast.get_docstring(node) or ''
                if docstring:
                    params = _parse_docstring_args(docstring) or params

            if params:
                tools.append(NormalizedTool(name=node.name, parameters=params))

        return tools


class ToolSchemaAdapter(FrameworkAdapter):
    """
    Adapter for AI / LLM App projects.

    Spec format (llm-contract.md):
      ### get_weather
      #### Parameters
      | Name | Type | Required | Description |
      |---|---|---|---|
      | location | string | Yes | City name |
      | units | string | No | celsius or fahrenheit |

    Code format (Python — type annotations):
      def get_weather(location: str, units: str = 'celsius') -> dict:
          ...

    Code format (JSON — OpenAI tool schema):
      [{"name": "get_weather", "parameters": {"properties": {"location": {"type": "string"}}}}]
    """

    def extract_spec(self, spec_path: str) -> list[NormalizedTool]:
        try:
            with open(spec_path, encoding='utf-8') as f:
                text = f.read()
        except OSError:
            return []

        tools: list[NormalizedTool] = []
        section_matches = list(re.finditer(r'^### (`?)(\w+)\1', text, re.MULTILINE))

        for idx, match in enumerate(section_matches):
            tool_name = match.group(2)
            section_start = match.end()
            section_end = (section_matches[idx + 1].start()
                           if idx + 1 < len(section_matches) else len(text))
            section = text[section_start:section_end]
            tools.append(NormalizedTool(
                name=tool_name,
                parameters=_parse_params_table(section),
            ))

        return tools

    def extract_code(self, src_path: str) -> list[NormalizedTool]:
        all_files = (
            [src_path] if os.path.isfile(src_path)
            else [
                os.path.join(root, fname)
                for root, _, fnames in os.walk(src_path)
                for fname in fnames
                if fname.endswith(('.py', '.json'))
            ]
        )
        tools: list[NormalizedTool] = []
        for fpath in all_files:
            if fpath.endswith('.json'):
                tools.extend(self._parse_json(fpath))
            else:
                tools.extend(self._parse_python(fpath))
        return tools

    def _parse_json(self, fpath: str) -> list[NormalizedTool]:
        try:
            with open(fpath, encoding='utf-8') as f:
                data = json.load(f)
        except (OSError, json.JSONDecodeError):
            return []

        tools: list[NormalizedTool] = []
        entries = data if isinstance(data, list) else [data]
        for entry in entries:
            if not isinstance(entry, dict) or 'name' not in entry:
                continue
            props = (entry.get('parameters') or {}).get('properties') or {}
            params = [
                NormalizedField(name=k, type=(v.get('type') or '') if isinstance(v, dict) else '')
                for k, v in props.items()
            ]
            tools.append(NormalizedTool(name=entry['name'], parameters=params))
        return tools

    def _parse_python(self, fpath: str) -> list[NormalizedTool]:
        try:
            with open(fpath, encoding='utf-8') as f:
                source = f.read()
            tree = ast.parse(source, filename=fpath)
        except (OSError, SyntaxError):
            return []

        tools: list[NormalizedTool] = []
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            if node.name.startswith('_'):
                continue

            params = [
                NormalizedField(name=a.arg, type=_annotation_str(a.annotation))
                for a in node.args.args
                if a.arg not in _SKIP_PARAMS
            ]

            # Fall back to docstring Args: if no type annotations
            if not any(p.type for p in params):
                docstring = ast.get_docstring(node) or ''
                if docstring:
                    params = _parse_docstring_args(docstring) or params

            if params:
                tools.append(NormalizedTool(name=node.name, parameters=params))

        return tools
