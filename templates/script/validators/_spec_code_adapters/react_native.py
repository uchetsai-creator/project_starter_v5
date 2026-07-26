"""
react_native.py — ReactNativeDetector (+ legacy ReactNativeAdapter) for project_starter_v5.

Phase 52.5: ReactNativeDetector is the primary class — it receives pre-discovered
files from MobileAdapter and returns NormalizedScreen objects.
ReactNativeAdapter is kept as a backward-compatible shim.

Extracts NormalizedScreen objects from:
  - Spec: mobile-contract.md (### ScreenName sections with #### Props tables)
  - Code: .tsx / .jsx files — React function components or class components

No comparison logic here. All comparison lives in verify_spec_code.py.
"""
from __future__ import annotations

import os
import re

from _base import Detector, FrameworkAdapter, NormalizedField, NormalizedScreen

_RN_EXTENSIONS = ('.tsx', '.jsx', '.ts', '.js')

# Boundary used to bound how far a "component body" search extends when a component's
# props aren't destructured in its parameter list (see _component_body below) — the
# next top-level function/const-arrow/class declaration, or end of file.
_NEXT_COMPONENT_RE = re.compile(
    r'\n\s*(?:export\s+)?(?:default\s+)?'
    r'(?:function\s+[A-Z]\w*|const\s+[A-Z]\w*\s*(?::[^=]+)?=|class\s+[A-Z]\w*\s+extends)',
)

# Non-destructured single `props` parameter, e.g. `function Name(props: Type)` or
# `const Name = (props: Type) => ...` — as common in real TypeScript React code as the
# destructured-parameter style, but the original regexes here only matched the latter.
_FN_PROPS_PARAM_RE = re.compile(
    r'\bfunction\s+([A-Z]\w*)\s*\(\s*(\w+)\s*(?::\s*[^),]+)?\s*\)',
)
_CONST_PROPS_PARAM_RE = re.compile(
    r'\bconst\s+([A-Z]\w*)\s*(?::\s*\S+)?\s*=\s*\(\s*(\w+)\s*(?::\s*[^),]+)?\s*\)\s*(?::\s*\S+)?\s*=>',
)

# Class components — still common, fully valid React; the original detector had no
# pattern for them at all.
_CLASS_COMPONENT_RE = re.compile(
    r'\bclass\s+([A-Z]\w*)\s+extends\s+(?:React\.)?(?:Component|PureComponent)\b',
)


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


class ReactNativeDetector(Detector):
    """
    Framework detector for React Native (Phase 52.5).

    Receives pre-discovered .tsx/.jsx/.ts/.js files from MobileAdapter.
    Returns NormalizedScreen for each React function/const component.
    Must not perform file discovery.
    """

    def extract(self, files: list[str]) -> list[NormalizedScreen]:
        screens: list[NormalizedScreen] = []
        seen: set[str] = set()
        for fpath in files:
            if any(fpath.endswith(ext) for ext in _RN_EXTENSIONS):
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

        fn_pattern = re.compile(
            r'\bfunction\s+([A-Z]\w*)\s*\(\s*\{([^}]*)\}',
        )
        for m in fn_pattern.finditer(source):
            name = m.group(1)
            props = self._extract_destructured_props(m.group(2))
            screens.append(NormalizedScreen(name=name, props=props))

        const_pattern = re.compile(
            r'\bconst\s+([A-Z]\w*)\s*(?::\s*\S+)?\s*=\s*\(\s*\{([^}]*)\}',
        )
        for m in const_pattern.finditer(source):
            name = m.group(1)
            props = self._extract_destructured_props(m.group(2))
            if not any(s.name == name for s in screens):
                screens.append(NormalizedScreen(name=name, props=props))

        # Non-destructured single `props` parameter — resolve prop names from how
        # `props` is used in the function body instead (destructured there, or
        # accessed as props.x).
        for pattern in (_FN_PROPS_PARAM_RE, _CONST_PROPS_PARAM_RE):
            for m in pattern.finditer(source):
                name, props_var = m.group(1), m.group(2)
                if any(s.name == name for s in screens):
                    continue
                body = self._component_body(source, m.end())
                screens.append(NormalizedScreen(
                    name=name, props=self._extract_props_usage(body, props_var),
                ))

        # Class components (`class Name extends React.Component`) — not recognized
        # by any pattern above at all.
        for m in _CLASS_COMPONENT_RE.finditer(source):
            name = m.group(1)
            if any(s.name == name for s in screens):
                continue
            body = self._component_body(source, m.end())
            screens.append(NormalizedScreen(
                name=name, props=self._extract_this_props_usage(body),
            ))

        return screens

    def _extract_destructured_props(self, destructure_body: str) -> list[NormalizedField]:
        fields: list[NormalizedField] = []
        for part in re.split(r',', destructure_body):
            part = part.strip()
            m = re.match(r'^(\w+)', part)
            if m and m.group(1) not in ('', 'children'):
                fields.append(NormalizedField(name=m.group(1), type=''))
        return fields

    def _component_body(self, source: str, start: int) -> str:
        """Return the text from `start` up to the next top-level component
        declaration (or end of file) — a bounded window to search for how a
        non-destructured `props` parameter is actually used."""
        m = _NEXT_COMPONENT_RE.search(source, start)
        end = m.start() if m else len(source)
        return source[start:end]

    def _extract_props_usage(self, body: str, props_var: str) -> list[NormalizedField]:
        fields: list[NormalizedField] = []
        seen: set[str] = set()
        destructure_m = re.search(
            r'\b(?:const|let|var)\s*\{([^}]*)\}\s*=\s*' + re.escape(props_var) + r'\b', body,
        )
        if destructure_m:
            for f in self._extract_destructured_props(destructure_m.group(1)):
                if f.name not in seen:
                    seen.add(f.name)
                    fields.append(f)
        for m in re.finditer(re.escape(props_var) + r'\.(\w+)', body):
            if m.group(1) not in seen and m.group(1) != 'children':
                seen.add(m.group(1))
                fields.append(NormalizedField(name=m.group(1), type=''))
        return fields

    def _extract_this_props_usage(self, body: str) -> list[NormalizedField]:
        fields: list[NormalizedField] = []
        seen: set[str] = set()
        for m in re.finditer(r'this\.props\.(\w+)', body):
            if m.group(1) not in seen and m.group(1) != 'children':
                seen.add(m.group(1))
                fields.append(NormalizedField(name=m.group(1), type=''))
        return fields


class ReactNativeAdapter(FrameworkAdapter):
    """Deprecated: use the corresponding capability adapter in _capability_*.py. This shim exists for backward compatibility with --adapter <name> CLI usage. Do not extend.

    Adapter for React Native (TypeScript / JavaScript) Mobile App projects.

    Spec format (mobile-contract.md):
      ### HomeScreen
      #### Props
      | Name | Type | Required | Description |
      |---|---|---|---|
      | userId | string | Yes | Current user ID |
      | onLogout | () => void | No | Logout handler |

    Code format (.tsx/.jsx):
      function HomeScreen({ userId, onLogout }: HomeScreenProps) {
        return <View>...</View>;
      }
      // or
      const HomeScreen: React.FC<HomeScreenProps> = ({ userId, onLogout }) => { ... };
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
                if any(fname.endswith(ext) for ext in _RN_EXTENSIONS)
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
        return ReactNativeDetector()._parse_file(fpath)
