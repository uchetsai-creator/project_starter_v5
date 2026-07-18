#!/usr/bin/env python3
"""
_verify_common.py — Shared utilities for project_starter_v4 verify scripts.

Import _is_placeholder from this module in any verify_*.py script.
This file must be co-located with the other verify scripts (templates/script/ in the framework; docs/script/ in user projects).
"""

import re

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


def _section_body(text: str, header_re: str) -> str | None:
    """Return text from matching section header until next same-or-higher heading."""
    m = re.search(header_re, text, re.IGNORECASE | re.MULTILINE)
    if not m:
        return None
    hashes = re.match(r'^(#+)', m.group(0))
    level = len(hashes.group(1)) if hashes else 1
    after = text[m.end():]
    boundary = re.search(r'(?m)^#{1,' + str(level) + r'}\s', after)
    return after[:boundary.start()] if boundary else after
