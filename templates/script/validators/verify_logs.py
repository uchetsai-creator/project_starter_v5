#!/usr/bin/env python3
"""
verify_logs.py — Log documentation quality audit for project_starter_v4 projects.

Checks that logging-spec.md has required sections filled, and that each module
log file (docs/modules/*/log-*.md) documents trace_id, structured fields, and
no raw print statements. Per-type addenda: pipeline row count, LLM call log fields.

Usage:
  python3 docs/script/validators/verify_logs.py --project-type TYPE
  python3 docs/script/validators/verify_logs.py --project-type TYPE --docs PATH
  python3 docs/script/validators/verify_logs.py --project-type TYPE --strict
  python3 docs/script/validators/verify_logs.py --project-type TYPE --json

Valid project types: web-app | cli-tool | library | data-pipeline | ml-pipeline |
                     microservices | llm-app | iac | mobile-app
Hybrid types use +: data-pipeline+web-app
"""

import argparse
import glob
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _verify_common import _is_placeholder, _section_body

VALID_TYPES = [
    'web-app', 'cli-tool', 'library',
    'data-pipeline', 'ml-pipeline', 'microservices', 'llm-app', 'iac', 'mobile-app',
]

# Types where logging-spec.md is Required or Optional
LOGGING_REQUIRED = {'web-app', 'cli-tool', 'data-pipeline', 'ml-pipeline', 'microservices', 'mobile-app'}
LOGGING_OPTIONAL = {'llm-app'}

# Types where trace_id propagation is expected
TRACE_ID_TYPES = {'web-app', 'data-pipeline', 'ml-pipeline', 'llm-app', 'microservices', 'mobile-app'}

# Per-type addenda
PIPELINE_TYPES = {'data-pipeline', 'ml-pipeline'}
LLM_TYPES = {'llm-app'}

# Required sections in logging-spec.md that must have ≥ MIN_SECTION_LINES filled lines
LOGGING_SPEC_SECTIONS = [
    '## Log Output Format',
    '## Required Log Points',
    '## Module Naming Convention',
]

MIN_SECTION_LINES = 3

# Module log file patterns
_PRINT_RE = re.compile(r'\bprint\s*\(|console\.(log|error|warn)\s*\(', re.IGNORECASE)
_STRUCTURED_RE = re.compile(r'(\{[^}]{2,}\}|key=value|→\s*\{|"trace_id"|structured|json payload|log payload)', re.IGNORECASE)
_TRACE_ID_RE = re.compile(r'trace.?id', re.IGNORECASE)
_ROW_COUNT_RE = re.compile(r'row.?count|rows.?processed|records.?processed|record.?count|rows.?in\b|rows.?out\b', re.IGNORECASE)
_LLM_FIELDS_RE = re.compile(r'\bmodel\b|\btoken\b|\bprompt\b|\bcompletion\b|\bllm.?call\b|\binference\b', re.IGNORECASE)


def _read_file(path):
    try:
        with open(path, encoding='utf-8') as fh:
            return fh.read().splitlines()
    except OSError:
        return None


def _filled_lines(body):
    return [
        l for l in body
        if l.strip()
        and not l.strip().startswith('#')
        and l.strip() != '---'
        and not (l.strip().startswith('<!--') and l.strip().endswith('-->'))
        and not _is_placeholder(l)
    ]


# ── logging-spec.md checks ────────────────────────────────────────────────────

def check_logging_spec(docs_dir, types):
    """Audit docs/specs/logging-spec.md for required sections and per-type addenda."""
    path = os.path.join(docs_dir, 'specs', 'logging-spec.md')
    results = []

    applicable = any(t in LOGGING_REQUIRED or t in LOGGING_OPTIONAL for t in types)
    if not applicable:
        return results  # N/A for library / iac

    if not os.path.exists(path):
        results.append({
            'file': 'specs/logging-spec.md',
            'check': 'file exists',
            'status': 'fail',
            'detail': 'logging-spec.md not found — create from templates/specs/logging-spec.md',
        })
        return results

    lines = _read_file(path)
    if lines is None:
        results.append({
            'file': 'specs/logging-spec.md',
            'check': 'file readable',
            'status': 'fail',
            'detail': 'cannot read file',
        })
        return results

    full_text = '\n'.join(lines)

    # Required sections filled
    for section in LOGGING_SPEC_SECTIONS:
        body = _section_body(full_text, re.escape(section))
        filled = _filled_lines(body.splitlines() if body else [])
        if len(filled) < MIN_SECTION_LINES:
            results.append({
                'file': 'specs/logging-spec.md',
                'check': f'section filled: {section.lstrip("# ")}',
                'status': 'warn',
                'detail': f'{len(filled)} filled line(s) — need ≥ {MIN_SECTION_LINES}',
            })
        else:
            results.append({
                'file': 'specs/logging-spec.md',
                'check': f'section filled: {section.lstrip("# ")}',
                'status': 'pass',
                'detail': f'{len(filled)} filled line(s)',
            })

    # trace_id documented for applicable types
    if any(t in TRACE_ID_TYPES for t in types):
        if _TRACE_ID_RE.search(full_text):
            results.append({
                'file': 'specs/logging-spec.md',
                'check': 'trace_id documented',
                'status': 'pass',
                'detail': 'trace_id found in spec',
            })
        else:
            results.append({
                'file': 'specs/logging-spec.md',
                'check': 'trace_id documented',
                'status': 'fail',
                'detail': 'trace_id not mentioned — add Request Tracing section',
            })

    # Per-type: pipeline row count field
    if any(t in PIPELINE_TYPES for t in types):
        if _ROW_COUNT_RE.search(full_text):
            results.append({
                'file': 'specs/logging-spec.md',
                'check': 'pipeline row count field',
                'status': 'pass',
                'detail': 'row count field documented',
            })
        else:
            results.append({
                'file': 'specs/logging-spec.md',
                'check': 'pipeline row count field',
                'status': 'warn',
                'detail': 'row count not documented — add row_count to Required Log Points for pipeline stages',
            })

    # Per-type: LLM call log fields
    if any(t in LLM_TYPES for t in types):
        if _LLM_FIELDS_RE.search(full_text):
            results.append({
                'file': 'specs/logging-spec.md',
                'check': 'LLM call log fields',
                'status': 'pass',
                'detail': 'LLM call fields documented',
            })
        else:
            results.append({
                'file': 'specs/logging-spec.md',
                'check': 'LLM call log fields',
                'status': 'warn',
                'detail': 'LLM call fields not documented — add model/token fields to Required Log Points',
            })

    return results


# ── module log file checks ────────────────────────────────────────────────────

def check_module_log_file(path, types):
    """Check a single log-*.md file for format compliance."""
    lines = _read_file(path)
    if lines is None:
        return [{'file': path, 'check': 'file readable', 'status': 'fail', 'detail': 'cannot read file'}]

    full_text = '\n'.join(lines)
    results = []

    # trace_id
    if any(t in TRACE_ID_TYPES for t in types):
        found = bool(_TRACE_ID_RE.search(full_text))
        results.append({
            'file': path,
            'check': 'trace_id',
            'status': 'pass' if found else 'warn',
            'detail': 'trace_id documented' if found else 'trace_id not mentioned in log points',
        })

    # Structured format (JSON fields or key=value notation documented)
    found = bool(_STRUCTURED_RE.search(full_text))
    results.append({
        'file': path,
        'check': 'structured format',
        'status': 'pass' if found else 'warn',
        'detail': 'structured fields documented' if found else 'no structured field format (expected JSON or key=value notation)',
    })

    # No raw print / console.log statements
    matches = _PRINT_RE.findall(full_text)
    results.append({
        'file': path,
        'check': 'no raw print statements',
        'status': 'fail' if matches else 'pass',
        'detail': f'{len(matches)} raw print/console statement(s) — use the shared logger utility' if matches else 'no raw print statements',
    })

    # Per-type: pipeline row count
    if any(t in PIPELINE_TYPES for t in types):
        found = bool(_ROW_COUNT_RE.search(full_text))
        results.append({
            'file': path,
            'check': 'pipeline row count field',
            'status': 'pass' if found else 'warn',
            'detail': 'row count field found' if found else 'row count not documented — add for pipeline stage log points',
        })

    # Per-type: LLM call fields
    if any(t in LLM_TYPES for t in types):
        found = bool(_LLM_FIELDS_RE.search(full_text))
        results.append({
            'file': path,
            'check': 'LLM call log fields',
            'status': 'pass' if found else 'warn',
            'detail': 'LLM call fields found' if found else 'LLM call fields not documented — add model/token fields',
        })

    return results


# ── scan ──────────────────────────────────────────────────────────────────────

def run_audit(docs_dir, types):
    spec_results = check_logging_spec(docs_dir, types)

    modules_dir = os.path.join(docs_dir, 'modules')
    log_files = sorted(glob.glob(os.path.join(modules_dir, '**', 'log-*.md'), recursive=True))

    log_results = []
    for path in log_files:
        log_results.extend(check_module_log_file(path, types))

    return spec_results, log_results, len(log_files)


# ── output ────────────────────────────────────────────────────────────────────

_STATUS_ICON = {'pass': '✅', 'warn': '⚠️ ', 'fail': '❌'}


def print_results(spec_results, log_results, log_file_count, types):
    type_str = '+'.join(types)
    print(f'\nLog quality audit — project type: {type_str}\n')

    all_results = spec_results + log_results
    files_seen: dict = {}
    for r in all_results:
        files_seen.setdefault(r['file'], []).append(r)

    for filepath, checks in files_seen.items():
        print(f'  {filepath}')
        for c in checks:
            icon = _STATUS_ICON.get(c['status'], '?')
            print(f'    {icon}  {c["check"]}: {c["detail"]}')
        print()

    fail_count = sum(1 for r in all_results if r['status'] == 'fail')
    warn_count = sum(1 for r in all_results if r['status'] == 'warn')
    pass_count = sum(1 for r in all_results if r['status'] == 'pass')

    print(f'  Module log files scanned : {log_file_count}')
    print(f'  Checks : {pass_count} pass  ·  {warn_count} warn  ·  {fail_count} fail')
    if fail_count > 0:
        print('  Verdict : FAIL')
    elif warn_count > 0:
        print('  Verdict : WARN')
    else:
        print('  Verdict : PASS')
    print()


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='Audit log documentation quality for a project_starter_v4 project.',
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
        help='Exit with code 1 if any check fails',
    )
    parser.add_argument(
        '--json', action='store_true', dest='json_output',
        help='Output results as JSON',
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

    spec_results, log_results, log_file_count = run_audit(args.docs, types)
    all_results = spec_results + log_results

    if args.json_output:
        print(json.dumps({
            'project_type': args.project_type,
            'log_files_scanned': log_file_count,
            'results': all_results,
        }, ensure_ascii=False, indent=2))
    else:
        print_results(spec_results, log_results, log_file_count, types)

    if args.strict and any(r['status'] == 'fail' for r in all_results):
        sys.exit(1)


if __name__ == '__main__':
    main()
