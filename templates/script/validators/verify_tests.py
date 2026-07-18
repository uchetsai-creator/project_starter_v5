#!/usr/bin/env python3
"""
verify_tests.py — Test report quality audit for project_starter_v4 projects.

Checks that docs/specs/test-report.md is filled with real results: test count > 0,
pass/fail recorded, Results by Module populated. For Data Pipeline / ML Pipeline:
also checks Contract Tests and Fault Injection sections are non-empty.

Usage:
  python3 docs/script/validators/verify_tests.py --project-type TYPE
  python3 docs/script/validators/verify_tests.py --project-type TYPE --docs PATH
  python3 docs/script/validators/verify_tests.py --project-type TYPE --strict
  python3 docs/script/validators/verify_tests.py --project-type TYPE --json

Valid project types: web-app | cli-tool | library | data-pipeline | ml-pipeline |
                     microservices | llm-app | iac | mobile-app
Hybrid types use +: data-pipeline+web-app
"""

import argparse
import json
import os
import re
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _verify_common import _section_body
from _registry import VALID_TYPES

PIPELINE_TYPES = {'data-pipeline', 'ml-pipeline'}

# test-report.md is Required for all types
TEST_REPORT_PATH = 'specs/test-report.md'

# Matches a table row that has an actual number (not [N] placeholder) in any cell.
_NUMBER_IN_ROW = re.compile(r'\|\s*[\w/ ]+\s*\|\s*(\d+)\s*\|')
# Must match "✅ Pass" or "❌ Fail" alone — not "✅ Pass / ❌ Fail" (template placeholder).
_OVERALL_STATUS_FILLED = re.compile(r'\*\*Overall status:\*\*\s*(✅|❌)\s*(Pass|Fail)(?!\s*/)', re.IGNORECASE)
_PLACEHOLDER_ROW = re.compile(r'\[e\.g\.,|\[N\]|\[Module\]|\[Stage\]|\[Source', re.IGNORECASE)
_REAL_ROW = re.compile(r'^\|\s*[^[\]|]+\s*\|')  # table row without [ ] placeholders



def _read_file(path):
    try:
        with open(path, encoding='utf-8') as fh:
            return fh.read().splitlines()
    except OSError:
        return None


def _real_table_rows(body):
    """Return data rows from a markdown table — skips header, separator, and placeholder rows."""
    separator_seen = False
    rows = []
    for line in body:
        if not line.strip().startswith('|'):
            continue
        if re.match(r'\|\s*[-:]+\s*\|', line):
            separator_seen = True
            continue
        if not separator_seen:
            continue  # skip the header row (before separator line)
        if _PLACEHOLDER_ROW.search(line):
            continue
        if _REAL_ROW.match(line):
            cells = [c.strip() for c in line.split('|')[1:-1]]
            if any(c and c not in ('—', '-', '...', '[result]', '[notes]') for c in cells):
                rows.append(line)
    return rows


# ── checks ───────────────────────────────────────────────────────────────────

def check_test_report(docs_dir, types):
    path = os.path.join(docs_dir, TEST_REPORT_PATH)
    results = []

    if not os.path.exists(path):
        results.append({
            'file': TEST_REPORT_PATH,
            'check': 'file exists',
            'status': 'fail',
            'detail': 'test-report.md not found — create from templates/specs/test-report.md',
        })
        return results

    lines = _read_file(path)
    if lines is None:
        results.append({
            'file': TEST_REPORT_PATH,
            'check': 'file readable',
            'status': 'fail',
            'detail': 'cannot read file',
        })
        return results

    full_text = '\n'.join(lines)

    # ── Check 1: Summary table has real test counts ───────────────────────────
    summary_body = _section_body(full_text, r'^##\s+Summary')
    number_rows = [l for l in (summary_body.splitlines() if summary_body else [])
                   if _NUMBER_IN_ROW.search(l) and not _PLACEHOLDER_ROW.search(l)]
    has_counts = len(number_rows) > 0

    # Verify at least one Total > 0
    nonzero = False
    for row in number_rows:
        cells = [c.strip() for c in row.split('|')[1:-1]]
        for cell in cells:
            if cell.isdigit() and int(cell) > 0:
                nonzero = True
                break
        if nonzero:
            break

    if not has_counts:
        results.append({
            'file': TEST_REPORT_PATH,
            'check': 'test counts filled',
            'status': 'fail',
            'detail': 'Summary table still has [N] placeholders — replace with actual test counts',
        })
    elif not nonzero:
        results.append({
            'file': TEST_REPORT_PATH,
            'check': 'test count > 0',
            'status': 'warn',
            'detail': 'all test counts are 0 — run tests and record actual results',
        })
    else:
        results.append({
            'file': TEST_REPORT_PATH,
            'check': 'test counts filled',
            'status': 'pass',
            'detail': f'{len(number_rows)} row(s) with real counts',
        })

    # ── Check 2: Overall status recorded ────────────────────────────────────
    if _OVERALL_STATUS_FILLED.search(full_text):
        results.append({
            'file': TEST_REPORT_PATH,
            'check': 'overall status recorded',
            'status': 'pass',
            'detail': 'Overall status line filled (✅ Pass or ❌ Fail)',
        })
    else:
        results.append({
            'file': TEST_REPORT_PATH,
            'check': 'overall status recorded',
            'status': 'fail',
            'detail': 'Overall status not filled — set to "✅ Pass" or "❌ Fail"',
        })

    # ── Check 3: Results by Module populated (non-pipeline) ──────────────────
    is_pipeline = any(t in PIPELINE_TYPES for t in types)
    if not is_pipeline:
        module_body = _section_body(full_text, r'^##\s+Results by Module')
        real_rows = _real_table_rows(module_body.splitlines() if module_body else [])
        if real_rows:
            results.append({
                'file': TEST_REPORT_PATH,
                'check': 'Results by Module populated',
                'status': 'pass',
                'detail': f'{len(real_rows)} module row(s) with real results',
            })
        else:
            results.append({
                'file': TEST_REPORT_PATH,
                'check': 'Results by Module populated',
                'status': 'fail',
                'detail': 'Results by Module has no filled rows — add actual per-module test results',
            })

    # ── Checks 4 & 5: Pipeline-specific sections ─────────────────────────────
    if is_pipeline:
        # Contract Tests section
        contract_body = _section_body(full_text, r'contract tests|quality gate')
        if contract_body is None:
            results.append({
                'file': TEST_REPORT_PATH,
                'check': 'Contract Tests section present',
                'status': 'fail',
                'detail': 'No "Contract Tests" section found — add from the pipeline template',
            })
        else:
            _contract_lines = contract_body.splitlines() if contract_body else []
            real_rows = _real_table_rows(_contract_lines)
            # Also check for Result: line with actual data (not a template placeholder)
            result_lines = [
                l for l in _contract_lines
                if re.search(r'\*\*Result:\*\*.*success=', l, re.IGNORECASE)
                and not _PLACEHOLDER_ROW.search(l)
                and not re.search(r'=\[|\[True|\[False', l)
            ]
            filled = len(real_rows) > 0 or len(result_lines) > 0
            results.append({
                'file': TEST_REPORT_PATH,
                'check': 'Contract Tests section filled',
                'status': 'pass' if filled else 'fail',
                'detail': f'{len(real_rows)} expectation row(s) + {len(result_lines)} Result line(s)' if filled
                          else 'Contract Tests section is empty — fill with GE/pandera results',
            })

        # Fault Injection section
        fault_body = _section_body(full_text, r'fault injection')
        if fault_body is None:
            results.append({
                'file': TEST_REPORT_PATH,
                'check': 'Fault Injection section present',
                'status': 'fail',
                'detail': 'No "Fault Injection Tests" section found — add from the pipeline template',
            })
        else:
            real_rows = _real_table_rows(fault_body.splitlines() if fault_body else [])
            results.append({
                'file': TEST_REPORT_PATH,
                'check': 'Fault Injection section filled',
                'status': 'pass' if real_rows else 'fail',
                'detail': f'{len(real_rows)} scenario row(s)' if real_rows
                          else 'Fault Injection section has no scenarios — add break-kit test results',
            })

    return results


# ── output ────────────────────────────────────────────────────────────────────

_STATUS_ICON = {'pass': '✅', 'warn': '⚠️ ', 'fail': '❌'}


def _fill_score(results):
    total = len(results)
    passed = sum(1 for r in results if r['status'] == 'pass')
    return passed, total


def print_results(results, types):
    type_str = '+'.join(types)
    print(f'\nTest report quality audit — project type: {type_str}\n')

    for r in results:
        icon = _STATUS_ICON.get(r['status'], '?')
        print(f'  {icon}  {r["check"]}: {r["detail"]}')

    print()
    passed, total = _fill_score(results)
    fail_count = sum(1 for r in results if r['status'] == 'fail')
    warn_count = sum(1 for r in results if r['status'] == 'warn')

    print(f'  Fill score : {passed} / {total} checks passed')
    if fail_count > 0:
        print('  Verdict    : FAIL')
    elif warn_count > 0:
        print('  Verdict    : WARN')
    else:
        print('  Verdict    : PASS')
    print()


# ── CLI ───────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description='Audit test report quality for a project_starter_v4 project.',
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

    results = check_test_report(args.docs, types)

    if args.json_output:
        passed, total = _fill_score(results)
        verdict = 'FAIL' if any(r['status'] == 'fail' for r in results) else \
                  'WARN' if any(r['status'] == 'warn' for r in results) else 'PASS'
        print(json.dumps({
            'project_type': args.project_type,
            'fill_score': f'{passed}/{total}',
            'verdict': verdict,
            'results': results,
        }, ensure_ascii=False, indent=2))
    else:
        print_results(results, types)

    if args.strict and any(r['status'] == 'fail' for r in results):
        sys.exit(1)


if __name__ == '__main__':
    main()
