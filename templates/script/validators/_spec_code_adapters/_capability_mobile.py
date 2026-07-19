"""
_capability_mobile.py — MobileAdapter for project_starter_v5 (Phase 52.5).

Capability adapter for mobile app projects.
Orchestrates: ReactNativeDetector, FlutterDetector.

Architecture:
  MobileAdapter (this file)
      │  extract_spec() — parses mobile-contract.md
      │  extract_code() — discovers .tsx/.jsx/.ts/.js + .dart files, delegates to detector(s)
      ├── ReactNativeDetector  (receives .tsx/.jsx/.ts/.js files)
      └── FlutterDetector      (receives .dart files)

Invariants:
  - No framework-specific parsing logic here.
  - Detector selection is the only framework-awareness in this adapter.
  - File discovery lives here, not in detectors.
  - extract_spec() / extract_code() never raise; return [] on any error.
"""
from __future__ import annotations

import os
import re

from _base import FrameworkAdapter, NormalizedField, NormalizedScreen

# Detector name → (module_name, class_name, accepted_extensions)
_DETECTORS: dict[str, tuple[str, str, tuple[str, ...]]] = {
    'react_native': ('react_native', 'ReactNativeDetector', ('.tsx', '.jsx', '.ts', '.js')),
    'flutter':      ('flutter',      'FlutterDetector',     ('.dart',)),
}


def _parse_props_table(section: str) -> list[NormalizedField]:
    h = re.search(r'^#### Props', section, re.MULTILINE)
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
            'name', 'prop', 'property'
        ):
            continue
        fields.append(NormalizedField(name=name, type=type_str))
    return fields


class MobileAdapter(FrameworkAdapter):
    """
    Capability adapter for mobile app projects (Phase 52.5).

    Recognized frameworks: react_native, flutter.

    Args:
        framework: Optional framework hint (e.g. 'react_native'). When supplied,
                   only the matching detector is run. When None, all detectors
                   run and results are unioned.
    """

    def __init__(self, framework: str | None = None) -> None:
        self._framework = framework

    # ------------------------------------------------------------------ spec

    def extract_spec(self, spec_path: str) -> list[NormalizedScreen]:
        """
        Parse a mobile-contract.md spec file.

        Both React Native and Flutter share the same spec format:
          ### HomeScreen
          #### Props
          | Name | Type | Required | Description |
          |---|---|---|---|
          | userId | string | Yes | Current user ID |
          | onLogout | () => void | No | Logout handler |
        """
        try:
            with open(spec_path, encoding='utf-8') as f:
                text = f.read()
        except OSError:
            return []

        screens: list[NormalizedScreen] = []
        section_matches = list(re.finditer(
            r'^### (`?)([A-Z]\w*)\1',
            text, re.MULTILINE,
        ))

        for idx, match in enumerate(section_matches):
            screen_name = match.group(2)
            section_start = match.end()
            section_end = (section_matches[idx + 1].start()
                           if idx + 1 < len(section_matches) else len(text))
            section = text[section_start:section_end]

            screens.append(NormalizedScreen(
                name=screen_name,
                props=_parse_props_table(section),
            ))

        return screens

    # ------------------------------------------------------------------ code

    def extract_code(self, src_path: str) -> list[NormalizedScreen]:
        """
        Discover .tsx/.jsx/.ts/.js and .dart files and delegate to mobile detector(s).

        Deduplicates by screen name across detector results.
        With framework hint: only the matching detector runs.
        Without hint: all detectors run and results are unioned.
        """
        active_detectors = (
            {self._framework: _DETECTORS[self._framework]}
            if self._framework and self._framework in _DETECTORS
            else _DETECTORS
        )

        # Collect the union of all extensions needed by active detectors
        needed_exts: set[str] = set()
        for _, _, exts in active_detectors.values():
            needed_exts.update(exts)

        all_files = (
            [src_path] if os.path.isfile(src_path)
            else [
                os.path.join(root, fname)
                for root, _, fnames in os.walk(src_path)
                for fname in fnames
                if any(fname.endswith(ext) for ext in needed_exts)
            ]
        )

        return self._dispatch_detectors(active_detectors, all_files)
