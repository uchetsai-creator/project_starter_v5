"""
javascript_logging.py — JavaScriptLoggingDetector for project_starter_v5.

Covers JavaScript, TypeScript, and React/JSX (.js/.jsx/.ts/.tsx) — the logger-call
convention and function-scoping rules are identical across all four; React function
components and hooks are just functions/arrow functions, so no separate detector is
needed for them (see logging-spec.md → Logger Instantiation, Node.js row).

Extracts NormalizedLogPoint objects from: any `<something>.info(...)` / `.warn(...)` /
`.warning(...)` / `.error(...)` / `.debug(...)` call, attributed to the nearest enclosing
named function — mirrors python_logging.py, but JS/TS has no stdlib AST in Python, so
this is a regex + brace-depth scanner instead of an `ast` walk:

  1. `_scope_boundaries()` walks the source char-by-char, tracking string/template-
     literal state (so braces inside strings don't corrupt the count) and a stack of
     named function scopes (`function foo() {`, `const foo = () => {`, class/object
     method shorthand `foo() {}`). Anonymous blocks (if/for/callbacks passed to hooks
     like useEffect) do not push a new scope — a log call inside one is still
     attributed to the nearest enclosing *named* function, which is what a
     log-<module>.md row is expected to reference.
  2. `_LOG_CALL_RE` finds logger call sites and their message argument (single,
     double, or template-literal string). Template-literal `${...}` interpolation is
     replaced with a placeholder before matching `<operation> — <state>`, the same
     tolerance python_logging.py gives Python f-strings.

This is a heuristic scanner, not a real JS/TS parser (consistent with this framework's
other JS/TS detectors — see express.py, typescript.py) — it can be fooled by unusual
formatting, but false negatives here only mean a task needs a second look, not a wrong
PASS.

No comparison logic here. All comparison lives in verify_spec_code.py.
"""
from __future__ import annotations

import bisect
import re

from _base import Detector, NormalizedLogPoint

_JS_EXTENSIONS = ('.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs')

_LEVEL_METHODS = {
    'info': 'info',
    'warning': 'warn',
    'warn': 'warn',
    'error': 'error',
    'debug': 'debug',
}

_CONTROL_KEYWORDS = frozenset({
    'if', 'for', 'while', 'switch', 'catch', 'else', 'do', 'try', 'finally',
    'function', 'return',
})

_FUNC_DECL_RE = re.compile(
    r'\bfunction\s+(\w+)\s*\([^()]*\)\s*(?::\s*[\w<>\[\].,\s]+?)?\s*\{'
)
_ARROW_ASSIGN_RE = re.compile(
    r'\b(?:const|let|var)\s+(\w+)\s*(?::\s*[\w<>\[\].,\s]+?)?\s*=\s*(?:async\s*)?'
    r'(?:\([^)]*\)|\w+)\s*(?::\s*[\w<>\[\].,\s]+?)?\s*=>\s*\{'
)
_METHOD_RE = re.compile(
    r'(?<![\w.])(?:(?:public|private|protected|static|async)\s+)*'
    r'([A-Za-z_$][\w$]*)\s*\([^()]*\)\s*(?::\s*[\w<>\[\].,\s]+?)?\s*\{'
)
_DECL_PATTERNS = (_FUNC_DECL_RE, _ARROW_ASSIGN_RE, _METHOD_RE)

_LOG_CALL_RE = re.compile(
    r"\b\w+\.(info|warn|warning|error|debug)\s*\(\s*"
    r"(?:'((?:[^'\\]|\\.)*)'"
    r'|"((?:[^"\\]|\\.)*)"'
    r'|`((?:[^`\\]|\\.)*)`)'
)

# '<operation> — <state>' — same convention as python_logging.py; '�' stands in
# for a template-literal ${...} interpolation (see _message_text).
_MESSAGE_RE = re.compile(
    r'^(?P<operation>.+?)\s+—\s+(?P<state>start|end(?::.*)?|failed(?::.*)?|warning(?::.*)?)$',
    re.IGNORECASE,
)

_INTERPOLATION_RE = re.compile(r'\$\{[^{}]*\}')


class JavaScriptLoggingDetector(Detector):
    """
    Language detector for JS/TS/React logger calls (Phase: logging capability).

    Receives pre-discovered .js/.jsx/.ts/.tsx files from LoggingAdapter.
    Returns NormalizedLogPoint for each call matching the message convention.
    Must not perform file discovery.
    """

    def extract(self, files: list[str]) -> list[NormalizedLogPoint]:
        points: list[NormalizedLogPoint] = []
        for fpath in files:
            if not any(fpath.endswith(ext) for ext in _JS_EXTENSIONS):
                continue
            points.extend(self._parse_file(fpath))
        return points

    def _parse_file(self, fpath: str) -> list[NormalizedLogPoint]:
        try:
            with open(fpath, encoding='utf-8') as f:
                source = f.read()
        except OSError:
            return []

        positions, names = _scope_boundaries(source)

        points: list[NormalizedLogPoint] = []
        for m in _LOG_CALL_RE.finditer(source):
            level = _LEVEL_METHODS.get(m.group(1).lower())
            if level is None:
                continue
            raw_text = next((g for g in m.groups()[1:] if g is not None), None)
            if raw_text is None:
                continue

            idx = bisect.bisect_right(positions, m.start()) - 1
            function = names[idx] if idx >= 0 else None
            if not function:
                continue  # module-level call — nothing to key it to

            text = _INTERPOLATION_RE.sub('�', raw_text)
            match = _MESSAGE_RE.match(text.strip())
            if not match:
                continue

            points.append(NormalizedLogPoint(
                function=function,
                operation=match.group('operation').strip(),
                state=match.group('state').strip(),
                level=level,
            ))
        return points


def _scope_boundaries(source: str) -> tuple[list[int], list[str | None]]:
    """
    Walk `source` tracking brace depth and named-function scope, ignoring braces
    inside string/template literals. Returns parallel lists (positions, names) —
    `names[i]` is the enclosing function name active from `positions[i]` onward,
    suitable for `bisect.bisect_right(positions, char_index) - 1` lookups.
    """
    # Precompute every declaration match once (O(n) total) rather than re-scanning
    # from position 0 for every '{' encountered in the char walk below (O(n^2)).
    decl_by_end: dict[int, str] = {}
    for regex in _DECL_PATTERNS:
        for m in regex.finditer(source):
            name = m.group(1)
            if name not in _CONTROL_KEYWORDS:
                decl_by_end[m.end()] = name

    positions: list[int] = [0]
    names: list[str | None] = [None]

    stack: list[tuple[str | None, int]] = []  # (name, entry_depth)
    depth = 0
    i = 0
    n = len(source)
    quote: str | None = None  # None | "'" | '"' | '`'

    def _record(name: str | None) -> None:
        if names[-1] != name:
            positions.append(i)
            names.append(name)

    while i < n:
        ch = source[i]

        if quote:
            if ch == '\\':
                i += 2
                continue
            if ch == quote:
                quote = None
            i += 1
            continue

        if ch in ('"', "'", '`'):
            quote = ch
            i += 1
            continue

        if ch == '/' and i + 1 < n and source[i + 1] == '/':
            nl = source.find('\n', i)
            i = nl if nl != -1 else n
            continue
        if ch == '/' and i + 1 < n and source[i + 1] == '*':
            end = source.find('*/', i + 2)
            i = end + 2 if end != -1 else n
            continue

        if ch == '{':
            depth += 1
            name = decl_by_end.get(i + 1)
            if name:
                stack.append((name, depth))
                _record(name)
            i += 1
            continue

        if ch == '}':
            depth -= 1
            if stack and stack[-1][1] - 1 == depth:
                stack.pop()
                _record(stack[-1][0] if stack else None)
            i += 1
            continue

        i += 1

    return positions, names
