"""
python_logging.py — PythonLoggingDetector for project_starter_v5.

Extracts NormalizedLogPoint objects from Python source: any `<something>.info(...)` /
`.warning(...)` / `.warn(...)` / `.error(...)` / `.debug(...)` call, wherever it appears
in a function body, keyed to the enclosing function. The base name (logger, log,
self.logger, self._logger, ...) is intentionally not checked — the framework does not
mandate a variable name, only the method name, per logging-spec.md → Log Levels.

Message text is read from the call's first argument:
  - a plain string constant: logger.info("create order — start")
  - an f-string: logger.info(f"create order — failed: {reason}") — dynamic
    ({...}) segments are treated as a wildcard and do not block extraction, since
    logging-spec.md's Message Format Rules only fix the '<operation> — <state>'
    prefix; a dynamic reason after 'failed:' / 'warning:' is expected.

Only messages matching '<operation> — <state>' (em dash, per Log Output Format)
produce a NormalizedLogPoint — calls that don't follow the convention are silently
skipped here; the raw-print / off-convention checks stay in verify_logs.py.

No comparison logic here. All comparison lives in verify_spec_code.py.
"""
from __future__ import annotations

import ast
import re

from _base import Detector, NormalizedLogPoint

_LEVEL_METHODS = {
    'info': 'info',
    'warning': 'warn',
    'warn': 'warn',
    'error': 'error',
    'debug': 'debug',
}

# '<operation> — <state>' — state is one of start / end[: reason] / failed[: reason] /
# warning[: reason], matching logging-spec.md → Message Format Rules. '�' is the
# placeholder substituted for f-string FormattedValue segments (see _message_text).
_MESSAGE_RE = re.compile(
    r'^(?P<operation>.+?)\s+—\s+(?P<state>start|end(?::.*)?|failed(?::.*)?|warning(?::.*)?)$',
    re.IGNORECASE,
)


class PythonLoggingDetector(Detector):
    """
    Language detector for Python's stdlib-style logging calls (Phase: logging capability).

    Receives pre-discovered .py files from LoggingAdapter.
    Returns NormalizedLogPoint for each call matching the message convention.
    Must not perform file discovery.
    """

    def extract(self, files: list[str]) -> list[NormalizedLogPoint]:
        points: list[NormalizedLogPoint] = []
        for fpath in files:
            if not fpath.endswith('.py'):
                continue
            points.extend(self._parse_file(fpath))
        return points

    def _parse_file(self, fpath: str) -> list[NormalizedLogPoint]:
        try:
            with open(fpath, encoding='utf-8') as f:
                source = f.read()
            tree = ast.parse(source, filename=fpath)
        except (OSError, SyntaxError, UnicodeDecodeError):
            return []

        points: list[NormalizedLogPoint] = []
        _FunctionLogVisitor(points).visit(tree)
        return points


class _FunctionLogVisitor(ast.NodeVisitor):
    """Walks the tree tracking the nearest enclosing function name."""

    def __init__(self, points: list[NormalizedLogPoint]) -> None:
        self._points = points
        self._stack: list[str] = []

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:  # noqa: N802
        self._stack.append(node.name)
        self.generic_visit(node)
        self._stack.pop()

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:  # noqa: N802
        self._stack.append(node.name)
        self.generic_visit(node)
        self._stack.pop()

    def visit_Call(self, node: ast.Call) -> None:  # noqa: N802
        self.generic_visit(node)
        if not self._stack:
            return  # module-level call, not inside any function — nothing to key it to
        if not isinstance(node.func, ast.Attribute):
            return
        level = _LEVEL_METHODS.get(node.func.attr)
        if level is None or not node.args:
            return

        text = _message_text(node.args[0])
        if text is None:
            return
        m = _MESSAGE_RE.match(text.strip())
        if not m:
            return

        self._points.append(NormalizedLogPoint(
            function=self._stack[-1],
            operation=m.group('operation').strip(),
            state=m.group('state').strip(),
            level=level,
        ))


def _message_text(node: ast.expr) -> str | None:
    """Best-effort static text for a log call's message argument.

    Plain string constants resolve directly. f-strings resolve with each dynamic
    {...} segment replaced by a placeholder character, so a static prefix like
    'create order — failed: ' can still match _MESSAGE_RE even though the reason
    itself is a runtime value.
    """
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    if isinstance(node, ast.JoinedStr):
        parts: list[str] = []
        for value in node.values:
            if isinstance(value, ast.Constant) and isinstance(value.value, str):
                parts.append(value.value)
            else:
                parts.append('�')
        return ''.join(parts)
    return None
