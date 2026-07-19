"""
flutter.py — FlutterDetector (+ legacy FlutterAdapter) for project_starter_v5.

Phase 52.5: FlutterDetector is the primary class — it receives pre-discovered
files from MobileAdapter and returns NormalizedScreen objects.
FlutterAdapter is kept as a backward-compatible shim.

Extracts NormalizedScreen objects from:
  - Spec: mobile-contract.md (### ScreenName sections with #### Props tables)
  - Code: .dart files — Widget classes (StatelessWidget / StatefulWidget) with final fields

No comparison logic here. All comparison lives in verify_spec_code.py.
"""
from __future__ import annotations

import os
import re

from _base import Detector, FrameworkAdapter, NormalizedField, NormalizedScreen

_DART_EXTENSIONS = ('.dart',)
_WIDGET_BASES = frozenset({'StatelessWidget', 'StatefulWidget', 'ConsumerWidget', 'HookWidget'})


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
        if not name or re.match(r'^[-:]+$', name) or name.lower() in ('name', 'prop', 'property'):
            continue
        fields.append(NormalizedField(name=name, type=type_str))
    return fields


class FlutterDetector(Detector):
    """
    Framework detector for Flutter / Dart (Phase 52.5).

    Receives pre-discovered .dart files from MobileAdapter.
    Returns NormalizedScreen for each Widget class.
    Must not perform file discovery.
    """

    def extract(self, files: list[str]) -> list[NormalizedScreen]:
        screens: list[NormalizedScreen] = []
        seen: set[str] = set()
        for fpath in files:
            if any(fpath.endswith(ext) for ext in _DART_EXTENSIONS):
                for screen in self._parse_file(fpath):
                    if screen.name not in seen:
                        seen.add(screen.name)
                        screens.append(screen)
        return screens

    def _parse_file(self, fpath: str) -> list[NormalizedScreen]:
        try:
            with open(fpath, encoding='utf-8') as f:
                source = f.read()
        except OSError:
            return []

        screens: list[NormalizedScreen] = []
        class_pattern = re.compile(
            r'\bclass\s+([A-Z]\w*)\s+extends\s+(\w+)\s*\{([^{}]*(?:\{[^{}]*\}[^{}]*)*)\}',
            re.DOTALL,
        )
        for m in class_pattern.finditer(source):
            class_name = m.group(1)
            base = m.group(2)
            if base not in _WIDGET_BASES:
                continue
            body = m.group(3)
            field_pattern = re.compile(r'\bfinal\s+(\w[\w<>, ?]*?)\s+(\w+)\s*;')
            props = [
                NormalizedField(name=fm.group(2), type=fm.group(1).strip())
                for fm in field_pattern.finditer(body)
                if fm.group(2) not in ('key',)
            ]
            screens.append(NormalizedScreen(name=class_name, props=props))

        return screens


class FlutterAdapter(FrameworkAdapter):
    """Deprecated: use the corresponding capability adapter in _capability_*.py. This shim exists for backward compatibility with --adapter <name> CLI usage. Do not extend.

    Adapter for Flutter / Dart Mobile App projects.

    Spec format (mobile-contract.md):
      ### HomeScreen
      #### Props
      | Name | Type | Required | Description |
      |---|---|---|---|
      | userId | String | Yes | Current user ID |
      | onLogout | VoidCallback | No | Logout handler |

    Code format (.dart):
      class HomeScreen extends StatelessWidget {
        final String userId;
        final VoidCallback onLogout;

        const HomeScreen({required this.userId, this.onLogout});
      }
    """

    def extract_spec(self, spec_path: str) -> list[NormalizedScreen]:
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

    def extract_code(self, src_path: str) -> list[NormalizedScreen]:
        files = (
            [src_path] if os.path.isfile(src_path)
            else [
                os.path.join(root, fname)
                for root, _, fnames in os.walk(src_path)
                for fname in fnames
                if any(fname.endswith(ext) for ext in _DART_EXTENSIONS)
            ]
        )
        screens: list[NormalizedScreen] = []
        seen: set[str] = set()
        for fpath in files:
            for screen in self._parse_file(fpath):
                if screen.name not in seen:
                    seen.add(screen.name)
                    screens.append(screen)
        return screens

    def _parse_file(self, fpath: str) -> list[NormalizedScreen]:
        return FlutterDetector()._parse_file(fpath)
