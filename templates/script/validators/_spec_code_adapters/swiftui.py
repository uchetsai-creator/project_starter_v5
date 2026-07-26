"""
swiftui.py — SwiftuiDetector for project_starter_v5.

Extracts NormalizedScreen objects from native iOS SwiftUI code — Swift, not
JSX/Dart, so React Native's/Flutter's parsing has nothing to reuse.

  struct HomeScreen: View {
      let title: String
      @Binding var isFavorite: Bool
      @State private var isExpanded: Bool = false

      var body: some View {
          Text(title)
      }
  }

A screen is `struct <Name>: <ConformanceList incl. View> { ... }`. Its props
are the struct's *stored* properties (`let`/`var` declarations, optionally
carrying a property-wrapper attribute like `@Binding`/`@ObservedObject`) that
are not `private` — `private` is the idiomatic marker for a view's own
internal state (`@State private var ...`), never for a value the parent
passes in, so it's the signal used here to exclude internal state without
needing special-case handling for every property wrapper that happens to be
used privately. `var body: some View { ... }` and similar computed
properties are excluded — they have a `{ ... }` body immediately after the
type, where a stored property has either `= defaultValue` or nothing before
the line ends.

Spec: mobile-contract.md — shared mobile format, parsed by MobileAdapter, not here.
"""
from __future__ import annotations

import re

from _base import Detector, NormalizedField, NormalizedScreen

_VIEW_STRUCT_RE = re.compile(r'\bstruct\s+([A-Z]\w*)\s*:\s*([^{]+)\{')

_PROPERTY_RE = re.compile(
    r'^[ \t]*((?:@\w+(?:\([^)]*\))?\s*)*)(private\s+)?(?:let|var)\s+(\w+)\s*:\s*([^={\n]+?)\s*(=|\{|$)',
    re.MULTILINE,
)


def _find_matching_brace(s: str, open_idx: int) -> int:
    depth = 1
    i = open_idx + 1
    while i < len(s) and depth > 0:
        if s[i] == '{':
            depth += 1
        elif s[i] == '}':
            depth -= 1
        i += 1
    return i - 1


class SwiftuiDetector(Detector):
    """
    Framework detector for SwiftUI (mobile).
    Receives pre-discovered .swift files from MobileAdapter. Must not perform file discovery.
    """

    def extract(self, files: list[str]) -> list[NormalizedScreen]:
        screens: list[NormalizedScreen] = []
        for fpath in files:
            if fpath.endswith('.swift'):
                screens.extend(self._parse_file(fpath))
        return screens

    def _parse_file(self, fpath: str) -> list[NormalizedScreen]:
        try:
            with open(fpath, encoding='utf-8') as f:
                source = f.read()
        except OSError:
            return []

        screens: list[NormalizedScreen] = []
        for m in _VIEW_STRUCT_RE.finditer(source):
            name = m.group(1)
            conformances = [c.strip() for c in m.group(2).split(',')]
            if 'View' not in conformances:
                continue

            open_idx = m.end() - 1
            close_idx = _find_matching_brace(source, open_idx)
            body = source[open_idx + 1:close_idx]

            props = [
                NormalizedField(name=prop_m.group(3), type=prop_m.group(4).strip())
                for prop_m in _PROPERTY_RE.finditer(body)
                if prop_m.group(5) != '{' and not prop_m.group(2)
            ]

            screens.append(NormalizedScreen(name=name, props=props))

        return screens


if __name__ == '__main__':
    import tempfile
    from pathlib import Path

    src = '''
import SwiftUI

struct HomeScreen: View {
    let title: String
    @Binding var isFavorite: Bool
    @State private var isExpanded: Bool = false

    var body: some View {
        Text(title)
    }

    private func helper() -> Int {
        return 0
    }
}

struct SettingsScreen: View, Identifiable {
    let userId: Int

    var body: some View {
        Text("Settings")
    }
}

class NotAScreen {
    let value: Int = 0
}
'''

    with tempfile.NamedTemporaryFile(suffix=".swift", mode="w", delete=False, encoding="utf-8") as f:
        f.write(src)
        path = f.name

    try:
        detector = SwiftuiDetector()
        assert detector.extract([]) == [], "extract([]) must return an empty list"

        screens = detector.extract([path])
        by_name = {s.name: s for s in screens}

        assert "HomeScreen" in by_name, screens
        assert "SettingsScreen" in by_name, screens        # multi-protocol conformance list
        assert "NotAScreen" not in by_name, screens          # class, not a View struct

        home_props = {f.name: f.type for f in by_name["HomeScreen"].props}
        assert home_props == {"title": "String", "isFavorite": "Bool"}, home_props
        assert "isExpanded" not in home_props, "private @State must not be a prop"

        settings_props = {f.name: f.type for f in by_name["SettingsScreen"].props}
        assert settings_props == {"userId": "Int"}
        assert len(screens) == 2
    finally:
        Path(path).unlink()

    print("[OK] swiftui.py self-test passed")
