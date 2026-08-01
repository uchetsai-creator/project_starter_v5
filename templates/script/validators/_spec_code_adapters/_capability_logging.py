"""
_capability_logging.py — LoggingAdapter for project_starter_v5.

Capability adapter for the code-level logging check: does the source code actually
call the logger at the points documented in docs/modules/<module>/log-<module-name>.md?
This is separate from verify_logs.py, which only audits documentation quality — this
adapter is the one that reads real source files.

Architecture:
  LoggingAdapter (this file)
      │  extract_spec() — parses one or all log-<module-name>.md files (structured table)
      │  extract_code() — discovers source files, delegates to language detector(s)
      └── PythonLoggingDetector (first language; add more the same way as they come up)

Spec format (log-<module-name>.md) — see logging-spec.md → Module Log File Format:
  | Function | Operation | State | Level |
  |---|---|---|---|
  | create_order | create order | start | info |
  | create_order | create order | end: success | info |

Invariants:
  - No language-specific parsing logic here.
  - Detector selection is the only framework-awareness in this adapter.
  - File discovery lives here, not in detectors.
  - extract_spec() / extract_code() never raise; return [] on any error.
"""
from __future__ import annotations

import os
import re

from _base import FrameworkAdapter, NormalizedLogPoint

_DETECTORS: dict[str, tuple[str, str, tuple[str, ...]]] = {
    'python_logging': ('python_logging', 'PythonLoggingDetector', ('.py',)),
    'javascript_logging': (
        'javascript_logging', 'JavaScriptLoggingDetector',
        ('.js', '.jsx', '.ts', '.tsx', '.mjs', '.cjs'),
    ),
    # Add one entry per language as a detector is built.
}

_ROW_RE = re.compile(r'^\|(.+)\|\s*$', re.MULTILINE)


class LoggingAdapter(FrameworkAdapter):
    """
    Capability adapter for the logging code-check (all project types).

    Args:
        framework: Optional language hint (e.g. 'python_logging'). When supplied,
                   only the matching detector runs. When None, all registered
                   detectors run and results are unioned.
    """

    def __init__(self, framework: str | None = None) -> None:
        self._framework = framework

    # ------------------------------------------------------------------ spec

    def extract_spec(self, spec_path: str) -> list[NormalizedLogPoint]:
        """
        Parse one log-<module-name>.md file, or every log-*.md file under a
        directory (e.g. docs/modules/), into NormalizedLogPoint items.
        """
        paths = self._discover_spec_files(spec_path)
        points: list[NormalizedLogPoint] = []
        for path in paths:
            points.extend(self._parse_log_file(path))
        return points

    def _discover_spec_files(self, spec_path: str) -> list[str]:
        if os.path.isfile(spec_path):
            return [spec_path]
        if os.path.isdir(spec_path):
            return sorted(
                os.path.join(root, fname)
                for root, _, fnames in os.walk(spec_path)
                for fname in fnames
                if fname.startswith('log-') and fname.endswith('.md')
            )
        return []

    def _parse_log_file(self, path: str) -> list[NormalizedLogPoint]:
        try:
            with open(path, encoding='utf-8') as f:
                text = f.read()
        except OSError:
            return []

        points: list[NormalizedLogPoint] = []
        header_seen = False
        for row in _ROW_RE.finditer(text):
            cols = [c.strip().strip('`') for c in row.group(1).split('|')]
            if len(cols) < 4:
                continue
            function, operation, state, level = cols[0], cols[1], cols[2], cols[3]
            # Skip header row and the |---|---| separator row
            if not header_seen:
                if function.lower() == 'function':
                    header_seen = True
                continue
            if re.match(r'^:?-+:?$', function):
                continue
            if not function or not state:
                continue
            points.append(NormalizedLogPoint(
                function=function, operation=operation,
                state=state, level=level.lower(),
            ))
        return points

    # ------------------------------------------------------------------ code

    def extract_code(self, src_path: str) -> list[NormalizedLogPoint]:
        """
        Discover source files and delegate to language detector(s).

        With framework hint: only the matching detector runs.
        Without hint: all registered detectors run and results are unioned.
        """
        active_detectors = (
            {self._framework: _DETECTORS[self._framework]}
            if self._framework and self._framework in _DETECTORS
            else _DETECTORS
        )

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
