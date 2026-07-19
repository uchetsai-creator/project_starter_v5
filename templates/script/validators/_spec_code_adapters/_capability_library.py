"""
_capability_library.py — LibraryAdapter for project_starter_v5 (Phase 52.5).

Capability adapter for library / SDK projects.
Orchestrates: PythonLibraryDetector.

Architecture:
  LibraryAdapter (this file)
      │  extract_spec() — parses public-api.md
      │  extract_code() — discovers .py files, delegates to detector(s)
      └── PythonLibraryDetector

Invariants:
  - No framework-specific parsing logic here.
  - Detector selection is the only framework-awareness in this adapter.
  - File discovery lives here, not in detectors.
  - extract_spec() / extract_code() never raise; return [] on any error.
"""
from __future__ import annotations

import os
import re

from _base import FrameworkAdapter, NormalizedField, NormalizedFunction
from _utils import _parse_params_table

_DETECTORS: dict[str, tuple[str, str]] = {
    'python_library': ('python_library', 'PythonLibraryDetector'),
}


class LibraryAdapter(FrameworkAdapter):
    """
    Capability adapter for library / SDK projects (Phase 52.5).

    Recognized frameworks: python_library.

    Args:
        framework: Optional framework hint (e.g. 'python_library'). When supplied,
                   only the matching detector is run. When None, all detectors
                   run and results are unioned.
    """

    def __init__(self, framework: str | None = None) -> None:
        self._framework = framework

    # ------------------------------------------------------------------ spec

    def extract_spec(self, spec_path: str) -> list[NormalizedFunction]:
        """
        Parse a public-api.md spec file.

        Spec format:
          ### function_name
          #### Parameters
          | Name | Type | Description |
          |---|---|---|
          | param1 | str | ... |
          #### Returns
          | Type | Description |
          |---|---|
          | dict | ... |
        """
        try:
            with open(spec_path, encoding='utf-8') as f:
                text = f.read()
        except OSError:
            return []

        functions: list[NormalizedFunction] = []
        section_matches = list(re.finditer(r'^### (`?)(\w+)\1', text, re.MULTILINE))

        for idx, match in enumerate(section_matches):
            func_name = match.group(2)
            section_start = match.end()
            section_end = (section_matches[idx + 1].start()
                           if idx + 1 < len(section_matches) else len(text))
            section = text[section_start:section_end]

            functions.append(NormalizedFunction(
                name=func_name,
                params=_parse_params_table(section),
                return_type=self._parse_return_type(section),
            ))

        return functions

    def _parse_return_type(self, section: str) -> str:
        h = re.search(r'^#### Returns', section, re.MULTILINE)
        if not h:
            return ''
        table_text = section[h.end():]
        next_h = re.search(r'^#{3,4} ', table_text, re.MULTILINE)
        if next_h:
            table_text = table_text[:next_h.start()]
        for row in re.finditer(r'(?m)^\|(.+)\|$', table_text):
            cols = [c.strip().strip('`') for c in row.group(1).split('|')]
            if cols and not re.match(r'^[-:]+$', cols[0]) and cols[0].lower() not in (
                'type', 'return type'
            ):
                return cols[0]
        return ''

    # ------------------------------------------------------------------ code

    def extract_code(self, src_path: str) -> list[NormalizedFunction]:
        """
        Discover .py files and delegate to library detector(s).

        With framework hint: only the matching detector runs.
        Without hint: all detectors run and results are unioned.
        """
        files = (
            [src_path] if os.path.isfile(src_path)
            else [
                os.path.join(root, fname)
                for root, _, fnames in os.walk(src_path)
                for fname in fnames
                if fname.endswith('.py')
            ]
        )

        active_detectors = (
            {self._framework: _DETECTORS[self._framework]}
            if self._framework and self._framework in _DETECTORS
            else _DETECTORS
        )

        results: list[NormalizedFunction] = []
        for detector_key, (module_name, class_name) in active_detectors.items():
            try:
                import importlib
                mod = importlib.import_module(module_name)
                cls = getattr(mod, class_name)
                results.extend(cls().extract(files))
            except Exception:  # noqa: BLE001
                pass

        return results
