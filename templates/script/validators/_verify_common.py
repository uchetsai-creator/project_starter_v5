#!/usr/bin/env python3
"""
_verify_common.py — Shared utilities for project_starter_v5 verify scripts.

Import helpers from this module in any verify_*.py script.
This file must be co-located with the other verify scripts (templates/script/ in the framework; docs/script/ in user projects).
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import overload

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
    re.compile(r'^\s*[-*_]{3,}\s*$'),  # bare markdown horizontal rule (---, ***, ___)
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
    # Generic catch-all: templates wrap unfilled values in a single bracket pair
    # (e.g. "[Component A]", "[Database]", "[your API key]"). A value that is
    # *entirely* one bracket span, start to end, is always unfilled template
    # content — real project content has no reason to bracket-wrap a whole field.
    re.compile(r'^\s*\[.+\]\s*$', re.DOTALL),
]


def _is_placeholder(text: str) -> bool:
    """Return True if text contains a template placeholder pattern."""
    return any(r.search(text) for r in _PLACEHOLDER_RES)


def _strip_bracket_blocks(text: str) -> str:
    """Remove `[ ... ]` instructional/example spans from section bodies.

    Templates wrap entire unfilled blocks in a single bracket pair, sometimes
    spanning many lines (e.g. backend.md's Stack section). Per-line placeholder
    checks can't see across lines to know a line is still inside such a span, so
    callers that check "is there real content in this section" strip these spans
    from the whole body first.
    """
    return re.sub(r'\[[^\[\]]*\]', '', text, flags=re.DOTALL)


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

    Accepts either a dict — the schema documented in README.md -> validation-result.json,
    with keys 'ts'/'project_type'/'validator'/'level' (used by every validator in this
    framework as of Phase 52.6, after verify_security.py and verify_acceptance.py were moved
    off the positional style to stop writing a different key set, 'script'/'status', into the
    same append-only file) — or positional args (script, project_type, status, ts), kept only
    for external/third-party callers still using the old convention.
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

    # Optional OTel dual-emission — see _otel.py's docstring. No-ops unconditionally
    # unless both opentelemetry-* is installed AND OTEL_EXPORTER_OTLP_ENDPOINT is set;
    # the local JSON write above is unaffected either way.
    try:
        from _otel import emit as _otel_emit  # noqa: PLC0415
        _otel_emit(entry.get('script', 'verify'), entry)
    except ImportError:
        pass


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


def read_doc_profile() -> str:
    """Best-effort read of doc_profile from .project-starter.yml at cwd (project root).
    Defaults to 'full' for a missing file, missing field, or any value other than exactly
    'lite' -- lite mode is opt-in, never silently assumed. Deliberately a small hand-parsed
    reader rather than a PyYAML-based one, matching every other validator/hook that reads a
    single .project-starter.yml scalar (e.g. adapters/claude/pretooluse_scope_guard.py) --
    the validators have no PyYAML dependency today and shouldn't gain one for one field.
    Shared here (rather than duplicated per-script) since verify_docs.py and
    verify_content.py both need it and are already siblings importing this module."""
    try:
        with open('.project-starter.yml', encoding='utf-8') as f:
            for line in f:
                if line.startswith('doc_profile:'):
                    value = line.split(':', 1)[1].strip().strip('"\'')
                    return 'lite' if value == 'lite' else 'full'
    except OSError:
        pass
    return 'full'


@overload
def _section_body(text_or_lines: str, header_re: str) -> 'str | None': ...
@overload
def _section_body(text_or_lines: 'list[str]', header_re: str) -> 'list[str] | None': ...
def _section_body(text_or_lines: 'str | list[str]', header_re: str) -> 'str | list[str] | None':
    """Return section body from matching header until next same-or-higher heading.

    Accepts either a string or a list of lines.
    Returns the same type as the input (str → str, list → list[str]) — the two
    @overload signatures above exist purely so callers that always pass one type
    don't have to narrow a `str | list[str]` union back down themselves (e.g.
    `.splitlines()` on a known-str result); the implementation below is unchanged.
    """
    if isinstance(text_or_lines, list):
        is_list = True
        text = '\n'.join(text_or_lines)
    else:
        is_list = False
        text = text_or_lines
    m = re.search(header_re, text, re.IGNORECASE | re.MULTILINE)
    if not m:
        return None
    hashes = re.match(r'^(#+)', m.group(0))
    level = len(hashes.group(1)) if hashes else 1
    after = text[m.end():]
    boundary = re.search(r'(?m)^#{1,' + str(level) + r'}\s', after)
    result = after[:boundary.start()] if boundary else after
    result = _strip_bracket_blocks(result)
    return result.splitlines() if is_list else result


# ---------------------------------------------------------------------------
# Zero-coverage detection — shared by verify_spec_code.py and scan_codebase.py
# ---------------------------------------------------------------------------

# Files that commonly sit in an otherwise-empty source folder and don't count as
# "real code exists here" — a bare .gitkeep or README shouldn't trigger a
# zero-coverage warning meant for "code exists but nothing recognized it".
_NON_CODE_FILENAMES = {'.gitkeep', '.gitignore', '.ds_store', 'readme.md', 'readme.txt', 'license'}
_SKIP_DIRNAMES = {'.git', '__pycache__', 'node_modules', '.venv', 'venv', 'dist', 'build'}


def _src_has_real_files(src: str) -> bool:
    """True if `src` contains at least one file that isn't just a placeholder.

    Used to distinguish two very different reasons a scan/extraction can come back
    empty: legitimately no code written yet (nothing to warn about), vs real code
    exists but nothing recognized it — wrong adapter/framework hint, a folder-naming
    heuristic that doesn't match this project's layout, or no detector registered
    for this language at all. Reporting "0/0 = 100%" or "no mismatches" in that
    second case isn't a real pass — it means nothing was actually checked.
    """
    if os.path.isfile(src):
        return Path(src).name.lower() not in _NON_CODE_FILENAMES
    for root, dirs, files in os.walk(src):
        dirs[:] = [d for d in dirs if d not in _SKIP_DIRNAMES and not d.startswith('.')]
        for f in files:
            if f.lower() not in _NON_CODE_FILENAMES:
                return True
    return False
