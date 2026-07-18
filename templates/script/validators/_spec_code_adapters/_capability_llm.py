"""
_capability_llm.py — LLMAdapter for project_starter_v5 (Phase 52.5).

Capability adapter for AI / LLM app projects.
Orchestrates: ToolSchemaDetector.

Architecture:
  LLMAdapter (this file)
      │  extract_spec() — parses llm-contract.md
      │  extract_code() — discovers .py + .json files, delegates to detector(s)
      └── ToolSchemaDetector

Invariants:
  - No framework-specific parsing logic here.
  - Detector selection is the only framework-awareness in this adapter.
  - File discovery lives here, not in detectors.
  - extract_spec() / extract_code() never raise; return [] on any error.
"""
from __future__ import annotations

import os
import re

from _base import FrameworkAdapter, NormalizedField, NormalizedTool

_DETECTORS: dict[str, tuple[str, str]] = {
    'tool_schema': ('tool_schema', 'ToolSchemaDetector'),
}


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
        if not name or re.match(r'^[-:]+$', name) or name.lower() in (
            'name', 'parameter', 'param'
        ):
            continue
        fields.append(NormalizedField(name=name, type=type_str))
    return fields


class LLMAdapter(FrameworkAdapter):
    """
    Capability adapter for AI / LLM app projects (Phase 52.5).

    Recognized frameworks: tool_schema.

    Args:
        framework: Optional framework hint (e.g. 'tool_schema'). When supplied,
                   only the matching detector is run. When None, all detectors
                   run and results are unioned.
    """

    def __init__(self, framework: str | None = None) -> None:
        self._framework = framework

    # ------------------------------------------------------------------ spec

    def extract_spec(self, spec_path: str) -> list[NormalizedTool]:
        """
        Parse an llm-contract.md spec file.

        Spec format:
          ### get_weather
          #### Parameters
          | Name | Type | Required | Description |
          |---|---|---|---|
          | location | string | Yes | City name |
          | units | string | No | celsius or fahrenheit |
        """
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

    # ------------------------------------------------------------------ code

    def extract_code(self, src_path: str) -> list[NormalizedTool]:
        """
        Discover .py and .json files and delegate to LLM detector(s).

        With framework hint: only the matching detector runs.
        Without hint: all detectors run and results are unioned.
        """
        files = (
            [src_path] if os.path.isfile(src_path)
            else [
                os.path.join(root, fname)
                for root, _, fnames in os.walk(src_path)
                for fname in fnames
                if fname.endswith(('.py', '.json'))
            ]
        )

        active_detectors = (
            {self._framework: _DETECTORS[self._framework]}
            if self._framework and self._framework in _DETECTORS
            else _DETECTORS
        )

        results: list[NormalizedTool] = []
        for detector_key, (module_name, class_name) in active_detectors.items():
            try:
                import importlib
                mod = importlib.import_module(module_name)
                cls = getattr(mod, class_name)
                results.extend(cls().extract(files))
            except Exception:  # noqa: BLE001
                pass

        return results
