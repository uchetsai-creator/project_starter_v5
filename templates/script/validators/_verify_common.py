#!/usr/bin/env python3
"""
_verify_common.py — Shared utilities for project_starter_v5 verify scripts.

Import helpers from this module in any verify_*.py script.
This file must be co-located with the other verify scripts (templates/script/ in the framework; docs/script/ in user projects).
"""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# Lazy import — _registry.py is co-located; importing VALID_TYPES triggers no file I/O.
from _registry import VALID_TYPES

# Canonical placeholder patterns — union of all patterns across verify scripts.
# A line matching any of these is treated as unfilled template content.
_PLACEHOLDER_RES = [
    re.compile(r'<!--\s*TODO\b', re.IGNORECASE),
    re.compile(r'<!--\s*TBD\b', re.IGNORECASE),
    re.compile(r'\b_TBD_\b'),
    re.compile(r'\[placeholder\]', re.IGNORECASE),
    re.compile(r'\[your\s+', re.IGNORECASE),
    re.compile(r'\[insert\s+', re.IGNORECASE),
    re.compile(r'\[describe\s+', re.IGNORECASE),
    re.compile(r'\[add\s+', re.IGNORECASE),
    re.compile(r'\[fill\s+', re.IGNORECASE),
    re.compile(r'^\s*_\s*$'),
    re.compile(r'^\s*\.\.\.\s*$'),
    re.compile(r'\[e\.g\.', re.IGNORECASE),
    re.compile(r'\[Component\]', re.IGNORECASE),
    re.compile(r'\[Method\]', re.IGNORECASE),
    re.compile(r'\[/path\]', re.IGNORECASE),
    re.compile(r'\[FunctionName\]', re.IGNORECASE),
    re.compile(r'\[MODEL\]', re.IGNORECASE),
    re.compile(r'\[Stage\s+Name\b', re.IGNORECASE),
    re.compile(r'\[Flow\s+Name\b', re.IGNORECASE),
    re.compile(r'\[module\s+name\]', re.IGNORECASE),
    re.compile(r'\bactualFunctionName\b'),
    re.compile(r'\bpath/to/file\b', re.IGNORECASE),
]


def _is_placeholder(text: str) -> bool:
    """Return True if text contains a template placeholder pattern."""
    return any(r.search(text) for r in _PLACEHOLDER_RES)


def _read_file(path: str) -> list[str] | None:
    """Read a file and return its lines, or None on OSError."""
    try:
        with open(path, encoding='utf-8') as fh:
            return fh.read().splitlines()
    except OSError:
        return None


def _non_blank(lines: list[str]) -> list[str]:
    """Filter empty / whitespace-only lines."""
    return [ln for ln in lines if ln.strip()]


def _append_telemetry(
    entry_or_script: 'dict | str',
    project_type: str = '',
    status: str = '',
    ts: str = '',
) -> None:
    """Append a telemetry entry to .ai/telemetry/validation-result.json.

    Accepts either a dict (legacy style used by verify_docs etc.) or
    positional args (script, project_type, status, ts) used by verify_acceptance.
    """
    if isinstance(entry_or_script, dict):
        entry = entry_or_script
    else:
        entry = {
            'script': entry_or_script,
            'project_type': project_type,
            'status': status,
            'ts': ts,
        }
    telemetry_dir = Path('.ai') / 'telemetry'
    telemetry_dir.mkdir(parents=True, exist_ok=True)
    telemetry_file = telemetry_dir / 'validation-result.json'
    rows: list[dict] = []
    if telemetry_file.exists():
        try:
            rows = json.loads(telemetry_file.read_text())
            if not isinstance(rows, list):
                rows = []
        except (json.JSONDecodeError, OSError):
            rows = []
    rows.append(entry)
    telemetry_file.write_text(json.dumps(rows, indent=2))


def _telemetry_ts() -> str:
    """Return current UTC timestamp in the standard telemetry format."""
    return datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')


def parse_types(raw: str) -> list[str]:
    """Parse a project-type string (including + hybrid types) and validate each part."""
    parts = [p.strip() for p in raw.split('+')]
    for p in parts:
        if p not in VALID_TYPES:
            print(
                f"error: unknown project type '{p}'. Valid: {', '.join(VALID_TYPES)}",
                file=sys.stderr,
            )
            sys.exit(2)
    return parts


def _section_body(text_or_lines: 'str | list[str]', header_re: str) -> 'str | list[str] | None':
    """Return section body from matching header until next same-or-higher heading.

    Accepts either a string or a list of lines.
    Returns the same type as the input (str → str, list → list[str]).
    """
    is_list = isinstance(text_or_lines, list)
    text = '\n'.join(text_or_lines) if is_list else text_or_lines
    m = re.search(header_re, text, re.IGNORECASE | re.MULTILINE)
    if not m:
        return None
    hashes = re.match(r'^(#+)', m.group(0))
    level = len(hashes.group(1)) if hashes else 1
    after = text[m.end():]
    boundary = re.search(r'(?m)^#{1,' + str(level) + r'}\s', after)
    result = after[:boundary.start()] if boundary else after
    return result.splitlines() if is_list else result
