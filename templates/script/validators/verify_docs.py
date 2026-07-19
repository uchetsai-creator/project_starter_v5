#!/usr/bin/env python3
"""
verify_docs.py — Document completeness audit for project_starter_v5 projects.

Usage:
  python3 docs/script/validators/verify_docs.py --project-type TYPE
  python3 docs/script/validators/verify_docs.py --project-type TYPE --docs PATH
  python3 docs/script/validators/verify_docs.py --project-type TYPE --strict
  python3 docs/script/validators/verify_docs.py --project-type TYPE --json
  python3 docs/script/validators/verify_docs.py --project-type TYPE --content

Valid project types: web-app | cli-tool | library | data-pipeline | ml-pipeline | microservices | llm-app | iac | mobile-app
Hybrid types use +: data-pipeline+web-app  (takes union of both type matrices)
"""

import argparse
import json
import os
import pathlib
import re
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _registry import load_registry, build_matrix, build_file_locations, build_replaces_for, VALID_TYPES

_reg = None
MATRIX = None
FILE_LOCATIONS = None
REPLACES_FOR = None
TYPE_INDEX = None


def _init() -> None:
    global _reg, MATRIX, FILE_LOCATIONS, REPLACES_FOR, TYPE_INDEX
    if _reg is not None:
        return
    _reg = load_registry()
    MATRIX = build_matrix(_reg)
    FILE_LOCATIONS = build_file_locations(_reg)
    REPLACES_FOR = build_replaces_for(_reg)
    TYPE_INDEX = {t: i for i, t in enumerate(VALID_TYPES)}

SCANNED_DIRS = ('specs', 'architecture', 'business')

# ── Content quality constants (used by --content) ────────────────────────────

from _verify_common import _append_telemetry, _is_placeholder, _telemetry_ts

# A section must have at least this many non-empty, non-placeholder lines to
# be considered "filled".
MIN_SECTION_LINES = 3

# Required ## section headers per document.
# Empty list = only fill-ratio and placeholder checks apply (section names are
# too project-specific to enforce universally).
CONTENT_SECTIONS = {
    'architecture.md':      ['## Overview', '## System Components'],
    'backend.md':           ['## Stack', '## Layering'],
    'database.md':          ['## Main Entities'],
    'deployment.md':        ['## Services', '## Build / Deploy Flow'],
    'api-contract.md':      ['## Error Response Format'],
    'pipeline-contract.md': ['## Overview', '## Stage Contracts'],
    'test-plan.md':         ['## Testing Strategy', '## Test Scope'],
    'test-report.md':       ['## Summary', '## Results by Module'],
    'logging-spec.md':      ['## Log Output Format', '## Required Log Points'],
    'business-rules.md':    ['## Rules'],
    'quickstart.md':        ['## Setup', '## Verification'],
}


def _is_content_line(line):
    s = line.strip()
    if not s:
        return False
    if s.startswith('#'):
        return False
    if s == '---':
        return False
    if s.startswith('<!--') and s.endswith('-->'):
        return False
    return True


def scan_content(filepath, doc_name):
    """Analyse fill quality of a single document.

    Returns a dict:
      fill_pct         int  0-100
      placeholder_count int
      unfilled_sections list[str]
      status           'full' | 'partial' | 'poor'
    or None if the file cannot be read.
    """
    try:
        with open(filepath, encoding='utf-8') as fh:
            lines = fh.read().splitlines()
    except OSError:
        return None

    content_lines = [l for l in lines if _is_content_line(l)]
    placeholder_lines = [l for l in content_lines if _is_placeholder(l)]

    total = len(content_lines)
    n_placeholders = len(placeholder_lines)
    fill_pct = int((total - n_placeholders) / max(total, 1) * 100)

    # Check required sections.
    required_sections = CONTENT_SECTIONS.get(doc_name, [])
    unfilled_sections = []

    if required_sections:
        # Build a map of header → body lines.
        section_bodies: dict[str, list[str]] = {}
        current = None
        for line in lines:
            if line.startswith('## '):
                current = line.rstrip()
                section_bodies.setdefault(current, [])
            elif current is not None:
                section_bodies[current].append(line)

        for sec in required_sections:
            body = section_bodies.get(sec, [])
            filled = [l for l in body if _is_content_line(l) and not _is_placeholder(l)]
            if len(filled) < MIN_SECTION_LINES:
                unfilled_sections.append(sec)

    if fill_pct >= 80 and not unfilled_sections:
        status = 'full'
    elif fill_pct >= 50:
        status = 'partial'
    else:
        status = 'poor'

    return {
        'fill_pct': fill_pct,
        'placeholder_count': n_placeholders,
        'unfilled_sections': unfilled_sections,
        'status': status,
    }


# ── Core audit ────────────────────────────────────────────────────────────────

def effective_status(doc_name, types):
    """Return R/O/N for the given doc across all declared types (union rule)."""
    _init()
    if doc_name not in MATRIX:
        return None
    row = MATRIX[doc_name]
    ratings = [row[TYPE_INDEX[t]] for t in types]
    if 'R' in ratings:
        return 'R'
    if 'O' in ratings:
        return 'O'
    return 'N'


def collect_existing(docs_dir):
    """Return set of (subdir, filename) for all .md files in scanned subdirectories."""
    found = set()
    for subdir in SCANNED_DIRS:
        path = os.path.join(docs_dir, subdir)
        if not os.path.isdir(path):
            continue
        for fname in os.listdir(path):
            if fname.endswith('.md'):
                found.add((subdir, fname))
    return found


def run_audit(types, docs_dir, check_content=False):
    _init()
    existing = collect_existing(docs_dir)
    matrix_names = set(MATRIX.keys())
    results = []

    for doc_name in MATRIX:
        location = FILE_LOCATIONS.get(doc_name, 'specs')
        status = effective_status(doc_name, types)
        file_exists = (location, doc_name) in existing
        path = f'{location}/{doc_name}'

        if status == 'N':
            replacement = next(
                (REPLACES_FOR[doc_name][t] for t in types if doc_name in REPLACES_FOR and t in REPLACES_FOR[doc_name]),
                None,
            )
            na_note = (f'N/A for {"+".join(types)} but file exists' if file_exists
                       else (f'→ use {replacement}' if replacement else ''))
            entry = {
                'doc': path, 'status': 'orphan' if file_exists else 'na',
                'label': '🔍 Orphan' if file_exists else '—  N/A',
                'note': na_note,
            }
        elif status == 'R':
            entry = {
                'doc': path,
                'status': 'present' if file_exists else 'missing_required',
                'label': '✅ Present' if file_exists else '❌ Missing Required',
                'note': '',
            }
        else:
            entry = {
                'doc': path,
                'status': 'present' if file_exists else 'missing_optional',
                'label': '✅ Present' if file_exists else '⚠️  Missing Optional',
                'note': '(optional)' if file_exists else '',
            }

        if check_content and file_exists and status == 'R':
            full_path = os.path.join(docs_dir, location, doc_name)
            entry['content'] = scan_content(full_path, doc_name)

        results.append(entry)

    for subdir, fname in sorted(existing):
        if fname not in matrix_names:
            results.append({
                'doc': f'{subdir}/{fname}', 'status': 'orphan',
                'label': '🔍 Orphan', 'note': 'not in document matrix',
            })

    return results


# ── Output ────────────────────────────────────────────────────────────────────

def _content_suffix(c):
    if c is None:
        return ''
    if c['status'] == 'full':
        return f"  {c['fill_pct']}% filled ✅"
    issues = []
    if c['placeholder_count']:
        issues.append(f"{c['placeholder_count']} placeholder(s)")
    if c['unfilled_sections']:
        short = [s.lstrip('# ') for s in c['unfilled_sections']]
        issues.append(f"unfilled: {', '.join(short)}")
    symbol = '⚠️ ' if c['status'] == 'partial' else '❌'
    return f"  {c['fill_pct']}% filled {symbol} {'; '.join(issues)}"


def print_results(results, types):
    type_str = '+'.join(types)
    print(f'\nDocument audit — project type: {type_str}\n')

    counts = {s: 0 for s in ('present', 'missing_required', 'missing_optional', 'na', 'orphan')}
    order = ['missing_required', 'missing_optional', 'orphan', 'present', 'na']
    grouped = {s: [] for s in order}

    for r in results:
        grouped[r['status']].append(r)
        counts[r['status']] += 1

    for status in order:
        for r in grouped[status]:
            note = f'  {r["note"]}' if r['note'] else ''
            content = _content_suffix(r.get('content'))
            print(f'  {r["label"]:<24} {r["doc"]}{note}{content}')

    total_required = counts['present'] + counts['missing_required']
    present_required = sum(
        1 for r in results if r['status'] == 'present' and r.get('note') != '(optional)'
    )

    print()
    print(f'  Required : {present_required} / {total_required} present')
    if counts['missing_optional']:
        print(f'  Optional missing : {counts["missing_optional"]}')
    if counts['orphan']:
        print(f'  Orphans  : {counts["orphan"]}')

    content_results = [r for r in results if r.get('content')]
    if content_results:
        fully_filled = sum(1 for r in content_results if r['content']['status'] == 'full')
        print(f'  Spec fill: {fully_filled} / {len(content_results)} documents fully filled')

    print()


# ── Telemetry ─────────────────────────────────────────────────────────────────

def _write_telemetry(project_type: str, results: list[dict]) -> None:
    fail_count = sum(1 for r in results if r['status'] == 'missing_required')
    warn_count = sum(1 for r in results if r['status'] == 'missing_optional')
    failed_docs = [os.path.basename(r['doc']) for r in results if r['status'] == 'missing_required']
    _append_telemetry({
        'ts': _telemetry_ts(),
        'project_type': project_type,
        'validator': 'verify_docs.py',
        'level': 'fail' if fail_count > 0 else 'pass',
        'warn_count': warn_count,
        'fail_count': fail_count,
        'failed_docs': failed_docs,
    })


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='Audit document completeness for a project_starter_v5 project.',
    )
    parser.add_argument(
        '--project-type', required=True,
        help='Project type (e.g. web-app, data-pipeline+web-app)',
    )
    parser.add_argument(
        '--docs', default='docs',
        help='Path to docs/ directory (default: docs)',
    )
    parser.add_argument(
        '--strict', action='store_true',
        help='Exit with code 1 if any Required document is missing',
    )
    parser.add_argument(
        '--json', action='store_true', dest='json_output',
        help='Output results as JSON',
    )
    parser.add_argument(
        '--content', action='store_true',
        help='Also check fill quality: placeholders, required sections, fill ratio',
    )
    parser.add_argument(
        '--telemetry', action='store_true',
        help='Append run result to .ai/telemetry/validation-result.json',
    )
    args = parser.parse_args()

    types = [t.strip() for t in args.project_type.split('+')]
    invalid = [t for t in types if t not in VALID_TYPES]
    if invalid:
        print(f'error: unknown project type(s): {", ".join(invalid)}', file=sys.stderr)
        print(f'valid types: {", ".join(VALID_TYPES)}', file=sys.stderr)
        sys.exit(2)

    if not os.path.isdir(args.docs):
        print(f'error: docs directory not found: {args.docs}', file=sys.stderr)
        sys.exit(2)

    results = run_audit(types, args.docs, check_content=args.content)

    if args.json_output:
        print(json.dumps(
            {'project_type': args.project_type, 'results': results},
            ensure_ascii=False, indent=2,
        ))
    else:
        print_results(results, types)

    if args.telemetry:
        _write_telemetry(args.project_type, results)

    if args.strict and any(r['status'] == 'missing_required' for r in results):
        sys.exit(1)


if __name__ == '__main__':
    main()
