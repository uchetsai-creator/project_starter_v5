"""
typescript.py — TypescriptDetector for project_starter_v5.

Extracts NormalizedFunction objects from a TypeScript library's public API.
Not Python, so there is no `ast` module to lean on — parsing is regex + a
bracket-depth scanner, the same approach as express.py for JS/TS.

Two ways a function becomes "public" in this ecosystem, both handled:
  1. Direct export: `export function name(...)` / `export const name = (...) => ...`
     — the `export` keyword on the declaration itself is the public marker.
  2. Barrel re-export: an internal, undecorated `function name(...)` whose name
     is later named in an `export { name, other as alias };` statement — the
     closest TS equivalent of Python's `__all__` list, and just as common in
     real libraries that keep an index.ts barrel file separate from
     implementation files.
A name in an `export {...}` block is used as the exposed name (its alias, if
any), so a re-exported function is compared under the name callers actually
import, not its internal declaration name.

Params come from the parameter list text between the balanced parens after the
function name — found by scanning bracket depth rather than a single regex,
since a parameter list can itself contain parens/generics (e.g. `cb: (x:
number) => void`, `items: Array<string>`).

Spec: public-api.md — shared library format, parsed by LibraryAdapter, not here.
"""
from __future__ import annotations

import re

from _base import Detector, NormalizedField, NormalizedFunction

_EXTENSIONS = ('.ts', '.tsx')

_EXPORT_FUNC_RE = re.compile(r'\bexport\s+(?:default\s+)?(?:async\s+)?function\s+(\w+)\s*\(')
_EXPORT_CONST_ARROW_RE = re.compile(
    r'\bexport\s+const\s+(\w+)\s*(?::[^=]+)?=\s*(?:async\s*)?\('
)
_PLAIN_FUNC_RE = re.compile(r'(?<!export )\bfunction\s+(\w+)\s*\(')
_PLAIN_CONST_ARROW_RE = re.compile(
    r'(?<!export )\bconst\s+(\w+)\s*(?::[^=]+)?=\s*(?:async\s*)?\('
)
_EXPORT_BLOCK_RE = re.compile(r'\bexport\s*\{([^}]*)\}')


def _find_matching_paren(s: str, open_idx: int) -> int:
    """Index of the ')' matching the '(' at open_idx, respecting nesting."""
    depth = 1
    i = open_idx + 1
    while i < len(s) and depth > 0:
        if s[i] == '(':
            depth += 1
        elif s[i] == ')':
            depth -= 1
        i += 1
    return i - 1


def _bracket_delta(ch: str, prev: str) -> int:
    """Depth change for one character. '>' is only a generic-close when it's not
    the second character of an arrow token '=>' — otherwise a callback-typed
    parameter like `cb: (x: number) => void` miscounts depth and corrupts every
    scan after it."""
    if ch in '([{':
        return 1
    if ch in ')]}':
        return -1
    if ch == '<':
        return 1
    if ch == '>':
        return 0 if prev == '=' else -1
    return 0


def _split_top_level(s: str, sep: str = ',') -> list[str]:
    """Split on `sep` only at bracket depth 0, so nested (), [], {}, <> survive intact."""
    parts, current, depth, prev = [], [], 0, ''
    for ch in s:
        depth += _bracket_delta(ch, prev)
        if ch == sep and depth <= 0:
            parts.append(''.join(current))
            current = []
        else:
            current.append(ch)
        prev = ch
    if current:
        parts.append(''.join(current))
    return parts


def _parse_param(raw: str) -> NormalizedField | None:
    raw = raw.strip().removeprefix('...')
    if not raw:
        return None

    depth, eq_idx, prev = 0, -1, ''
    for i, ch in enumerate(raw):
        depth += _bracket_delta(ch, prev)
        # A top-level '=' is a default-value assignment — unless it's the '='
        # of an arrow '=>', which _bracket_delta already accounts for in depth
        # but which this check must also skip explicitly (it's still a bare
        # top-level '=' character, just not an assignment).
        if ch == '=' and depth == 0 and raw[i + 1:i + 2] != '>':
            eq_idx = i
            break
        prev = ch
    if eq_idx != -1:
        raw = raw[:eq_idx].strip()

    m = re.match(r'^(\w+)\s*\??\s*(?::\s*(.+))?$', raw)
    if not m:
        return None
    return NormalizedField(name=m.group(1), type=(m.group(2) or '').strip())


def _extract_return_type(tail: str) -> str:
    """`tail` is the text right after a function's closing ')'. Returns the
    `: ReturnType` annotation if present, stopping at whichever of '{' or '=>'
    comes first (arrow functions can omit braces for a direct-expression body)."""
    m = re.match(r'\s*:\s*(.+)', tail)
    if not m:
        return ''
    type_text = m.group(1)
    for delim in ('=>', '{'):
        idx = type_text.find(delim)
        if idx != -1:
            type_text = type_text[:idx]
    return type_text.strip()


class TypescriptDetector(Detector):
    """
    Framework detector for TypeScript (library).
    Receives pre-discovered .ts/.tsx/.js/.jsx files from LibraryAdapter. Must not perform file discovery.
    """

    def extract(self, files: list[str]) -> list[NormalizedFunction]:
        ts_files = [f for f in files if f.endswith(_EXTENSIONS)]

        sources: dict[str, str] = {}
        for fpath in ts_files:
            try:
                with open(fpath, encoding='utf-8') as f:
                    sources[fpath] = f.read()
            except OSError:
                continue

        barrel_names: dict[str, str] = {}
        for source in sources.values():
            barrel_names.update(self._barrel_exports(source))

        functions: list[NormalizedFunction] = []
        seen: set[str] = set()
        for source in sources.values():
            for fn in self._parse_source(source, barrel_names):
                if fn.name not in seen:
                    seen.add(fn.name)
                    functions.append(fn)
        return functions

    @staticmethod
    def _barrel_exports(source: str) -> dict[str, str]:
        """Map internal name -> exposed name from every `export { a, b as c }`."""
        names: dict[str, str] = {}
        for block in _EXPORT_BLOCK_RE.finditer(source):
            for entry in block.group(1).split(','):
                entry = entry.strip()
                if not entry:
                    continue
                if ' as ' in entry:
                    internal, exposed = (p.strip() for p in entry.split(' as ', 1))
                else:
                    internal = exposed = entry
                names[internal] = exposed
        return names

    def _parse_source(self, source: str, barrel_names: dict[str, str]) -> list[NormalizedFunction]:
        functions: list[NormalizedFunction] = []

        for pattern, exposed_directly in (
            (_EXPORT_FUNC_RE, True), (_EXPORT_CONST_ARROW_RE, True),
            (_PLAIN_FUNC_RE, False), (_PLAIN_CONST_ARROW_RE, False),
        ):
            for m in pattern.finditer(source):
                internal_name = m.group(1)
                if exposed_directly:
                    exposed_name = internal_name
                elif internal_name in barrel_names:
                    exposed_name = barrel_names[internal_name]
                else:
                    continue  # not exported directly, and not named in a barrel export

                open_idx = source.index('(', m.end() - 1)
                close_idx = _find_matching_paren(source, open_idx)
                params_text = source[open_idx + 1:close_idx]
                params = [
                    p for raw in _split_top_level(params_text)
                    if (p := _parse_param(raw)) is not None
                ]
                return_type = _extract_return_type(source[close_idx + 1:close_idx + 200])

                functions.append(NormalizedFunction(
                    name=exposed_name, params=params, return_type=return_type,
                ))

        return functions


if __name__ == '__main__':
    import tempfile
    from pathlib import Path

    index_ts = '''
export function add(a: number, b: number): number {
  return a + b;
}

export const greet = (name: string, loud?: boolean): string => {
  return loud ? name.toUpperCase() : name;
};

function internalMultiply(a: number, b: number): number {
  return a * b;
}

export { internalMultiply as multiply };

function trulyPrivate(x: number): number {
  return x;
}
'''

    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "index.ts"
        path.write_text(index_ts, encoding="utf-8")

        detector = TypescriptDetector()
        assert detector.extract([]) == [], "extract([]) must return an empty list"

        functions = detector.extract([str(path)])
        by_name = {f.name: f for f in functions}

        assert "add" in by_name, functions
        assert "greet" in by_name, functions
        assert "multiply" in by_name, functions            # barrel-exported under an alias
        assert "internalMultiply" not in by_name, functions  # only the alias is public
        assert "trulyPrivate" not in by_name, functions

        add_params = {f.name: f.type for f in by_name["add"].params}
        assert add_params == {"a": "number", "b": "number"}
        assert by_name["add"].return_type == "number"

        greet_params = {f.name: f.type for f in by_name["greet"].params}
        assert greet_params == {"name": "string", "loud": "boolean"}
        assert by_name["greet"].return_type == "string"

        multiply_params = {f.name: f.type for f in by_name["multiply"].params}
        assert multiply_params == {"a": "number", "b": "number"}

        assert len(functions) == 3

    print("[OK] typescript.py self-test passed")
