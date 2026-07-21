#!/usr/bin/env python3
"""
verify_acceptance.py — Functional Acceptance Gate for project_starter_v5 projects.

Checks that declared functional requirements have test coverage and passing results.
Works identically for all 9 project types with type-specific extensions layered on top.

Three-layer traceability chain (Phase 85):
  project-requirements.md  →  test-plan.md  →  test-report.md
  (FR-XXX declared)            (scope covers)   (results ✅ Pass)

Requirement cross-reference (Phase 86):
  Every FR-XXX in project-requirements.md must appear in the Requirement column
  of test-plan.md ## Test Scope / In Scope table.

Type-specific extensions (no web bias):
  data-pipeline, ml-pipeline  — Contract Tests section must have real results
  llm-app                     — eval-log.md latest entry must show ✅ pass

Usage:
  python3 docs/script/validators/verify_acceptance.py --project-type TYPE
  python3 docs/script/validators/verify_acceptance.py --project-type TYPE --docs PATH
  python3 docs/script/validators/verify_acceptance.py --project-type TYPE --strict
  python3 docs/script/validators/verify_acceptance.py --project-type TYPE --json

Valid project types: web-app | cli-tool | library | data-pipeline | ml-pipeline |
                     microservices | llm-app | iac | mobile-app
Hybrid types use +: data-pipeline+web-app
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _verify_common import _append_telemetry, _is_placeholder, _read_file, _section_body, _telemetry_ts
from _registry import VALID_TYPES

# ---------------------------------------------------------------------------
# Per-type required test levels (all 9 types — no web bias)
# ---------------------------------------------------------------------------

REQUIRED_TEST_LEVELS: dict[str, list[str]] = {
    'web-app':        ['Unit', 'Integration', 'E2E'],
    'cli-tool':       ['Unit', 'Integration'],
    'library':        ['Unit', 'Integration'],
    'data-pipeline':  ['Unit', 'Contract', 'E2E'],
    'ml-pipeline':    ['Unit', 'Contract', 'E2E'],
    'microservices':  ['Unit', 'Integration', 'Contract'],
    'llm-app':        ['Integration', 'Contract', 'E2E'],
    'iac':            ['Integration', 'E2E'],
    'mobile-app':     ['Unit', 'Integration', 'E2E'],
}

PIPELINE_TYPES = {'data-pipeline', 'ml-pipeline'}
LLM_TYPES = {'llm-app'}

_FR_LINE = re.compile(r'\*\*FR-(\d+)\*\*')
_AC_LINE = re.compile(r'\*\*AC-\d+\*\*')
_FR_REF = re.compile(r'\bFR-(\d+)\b')
_PLACEHOLDER_ROW = re.compile(
    r'\[e\.g\.,|\[N\]|\[Module\]|\[Feature\]|\[Stage\]|\[Source|\[Command|\[Service|\[FR-',
    re.IGNORECASE,
)
_REAL_TABLE_ROW = re.compile(r'^\|\s*[^[\]|]+\s*\|')
_OVERALL_PASS = re.compile(r'\*\*Overall status:\*\*\s*✅\s*Pass(?!\s*/)', re.IGNORECASE)
_NUMBER_IN_ROW = re.compile(r'\|\s*[\w/ ]+\s*\|\s*(\d+)\s*\|')


def _real_rows(body: list[str]) -> list[str]:
    """Return non-placeholder, non-header table rows from a section body."""
    separator_seen = False
    rows = []
    for line in body:
        if not line.strip().startswith('|'):
            continue
        if re.match(r'\|\s*[-:]+\s*\|', line):
            separator_seen = True
            continue
        if not separator_seen:
            continue
        if _PLACEHOLDER_ROW.search(line):
            continue
        if _REAL_TABLE_ROW.match(line):
            rows.append(line)
    return rows


def _level_in_table(label: str, lines: list[str]) -> bool:
    """Check if a test level keyword appears in a real (non-placeholder) table row."""
    for line in lines:
        if not line.strip().startswith('|'):
            continue
        if _PLACEHOLDER_ROW.search(line):
            continue
        if label.lower() in line.lower():
            return True
    return False


# ---------------------------------------------------------------------------
# Layer 1: project-requirements.md
# ---------------------------------------------------------------------------

def check_requirements(docs_path: str) -> tuple[list[str], list[str]]:
    """Return (issues, fr_ids) where fr_ids is the list of declared FR-XXX numbers."""
    issues: list[str] = []
    fr_ids: list[str] = []

    path = os.path.join(docs_path, 'project-requirements.md')
    lines = _read_file(path)
    if not lines:
        issues.append('project-requirements.md not found or empty')
        return issues, fr_ids

    fr_body = _section_body(lines, '## Functional Requirements')
    if not fr_body:
        issues.append('project-requirements.md: ## Functional Requirements section missing')
    else:
        for line in fr_body:
            if _is_placeholder(line):
                continue
            for m in _FR_LINE.finditer(line):
                fr_ids.append(m.group(1))
        if not fr_ids:
            issues.append(
                'project-requirements.md: ## Functional Requirements has no filled FR-XXX entries'
            )

    ac_body = _section_body(lines, '## Acceptance Criteria')
    if not ac_body:
        issues.append('project-requirements.md: ## Acceptance Criteria section missing')
    else:
        ac_lines = [l for l in ac_body if _AC_LINE.search(l) and not _is_placeholder(l)]
        if not ac_lines:
            issues.append(
                'project-requirements.md: ## Acceptance Criteria has no filled AC-XXX entries'
            )

    return issues, fr_ids


# ---------------------------------------------------------------------------
# Layer 2: test-plan.md
# ---------------------------------------------------------------------------

def check_test_plan(docs_path: str, project_type: str, fr_ids: list[str]) -> list[str]:
    issues: list[str] = []
    path = os.path.join(docs_path, 'specs', 'test-plan.md')
    lines = _read_file(path)
    if not lines:
        issues.append('specs/test-plan.md not found or empty')
        return issues

    # In Scope table must have at least one real row
    scope_body = _section_body(lines, '### In Scope')
    if not scope_body:
        scope_body = _section_body(lines, '## Test Scope')
    real_scope = _real_rows(scope_body) if scope_body else []
    if not real_scope:
        issues.append('specs/test-plan.md: ## Test Scope / In Scope table has no filled rows')

    # Phase 86: every declared FR-XXX must appear in the Requirement column
    if fr_ids and scope_body:
        # Collect all FR numbers referenced in real (non-placeholder) scope rows
        covered: set[str] = set()
        for row in real_scope:
            for m in _FR_REF.finditer(row):
                covered.add(m.group(1))
        uncovered = [fid for fid in fr_ids if fid not in covered]
        for fid in uncovered:
            issues.append(
                f'specs/test-plan.md: FR-{fid} declared in project-requirements.md '
                f'has no test coverage in ## Test Scope / In Scope (add to Requirement column)'
            )

    # Required test levels per project type
    strategy_body = _section_body(lines, '## Testing Strategy')
    if not strategy_body:
        issues.append('specs/test-plan.md: ## Testing Strategy section missing')
    else:
        required = REQUIRED_TEST_LEVELS.get(project_type, [])
        for level in required:
            if not _level_in_table(level, strategy_body):
                issues.append(
                    f'specs/test-plan.md: required test level "{level}" not found in '
                    f'## Testing Strategy (required for {project_type})'
                )

    return issues


# ---------------------------------------------------------------------------
# Layer 3: test-report.md
# ---------------------------------------------------------------------------

def check_test_report(docs_path: str, project_type: str) -> list[str]:
    issues: list[str] = []
    path = os.path.join(docs_path, 'specs', 'test-report.md')
    lines = _read_file(path)
    if not lines:
        issues.append('specs/test-report.md not found or empty')
        return issues

    text = '\n'.join(lines)

    # Overall status must be ✅ Pass
    if not _OVERALL_PASS.search(text):
        issues.append(
            'specs/test-report.md: **Overall status:** is not ✅ Pass '
            '(either placeholder or ❌ Fail)'
        )

    # Summary table must have at least one real number
    summary_body = _section_body(lines, '## Summary')
    has_number = False
    if summary_body:
        for line in summary_body:
            if _NUMBER_IN_ROW.search(line) and not _PLACEHOLDER_ROW.search(line):
                has_number = True
                break
    if not has_number:
        issues.append(
            'specs/test-report.md: ## Summary table has no real test counts (still [N] placeholders)'
        )

    # Results by Module must have real rows (pipeline types use a different section)
    module_body = _section_body(lines, '## Results by Module')
    if module_body:
        if not _real_rows(module_body):
            issues.append('specs/test-report.md: ## Results by Module has no filled rows')
    elif project_type not in PIPELINE_TYPES:
        issues.append('specs/test-report.md: ## Results by Module section missing')

    return issues


# ---------------------------------------------------------------------------
# Type-specific extensions
# ---------------------------------------------------------------------------

def check_pipeline_contracts(docs_path: str) -> list[str]:
    """data-pipeline / ml-pipeline: Contract Tests section must have real results."""
    issues: list[str] = []
    path = os.path.join(docs_path, 'specs', 'test-report.md')
    lines = _read_file(path)
    if not lines:
        return issues  # already caught by check_test_report

    contract_body: list[str] = []
    for heading in ('## [Data Pipeline / ML Pipeline] Contract Tests', '## Contract Tests'):
        contract_body = _section_body(lines, heading)
        if contract_body:
            break

    if not contract_body:
        issues.append(
            'specs/test-report.md: Contract Tests section missing '
            '(required for data-pipeline / ml-pipeline)'
        )
        return issues

    has_result = any(
        ('✅' in line or '❌' in line) and not _PLACEHOLDER_ROW.search(line)
        for line in contract_body
    )
    if not has_result:
        issues.append(
            'specs/test-report.md: Contract Tests section has no real results '
            '(✅ / ❌ expected; still placeholder)'
        )

    return issues


def check_llm_eval(docs_path: str) -> list[str]:
    """llm-app: eval-log.md latest data row must show ✅ pass."""
    issues: list[str] = []
    path = os.path.join(docs_path, 'specs', 'eval-log.md')
    lines = _read_file(path)
    if not lines:
        issues.append('specs/eval-log.md not found or empty (required for llm-app)')
        return issues

    separator_seen = False
    data_rows: list[str] = []
    for line in lines:
        if not line.strip().startswith('|'):
            continue
        if re.match(r'\|\s*[-:]+\s*\|', line):
            separator_seen = True
            continue
        if not separator_seen:
            continue
        if _PLACEHOLDER_ROW.search(line) or _is_placeholder(line):
            continue
        if _REAL_TABLE_ROW.match(line):
            data_rows.append(line)

    if not data_rows:
        issues.append('specs/eval-log.md: no eval run entries found (still placeholder)')
        return issues

    if '✅' not in data_rows[-1]:
        issues.append(
            'specs/eval-log.md: latest eval run does not show ✅ pass '
            '(check Pass? column in the most recent row)'
        )

    return issues


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_types(raw: str) -> list[str]:
    parts = [p.strip() for p in raw.replace('+', ' ').split()]
    for p in parts:
        if p not in VALID_TYPES:
            print(f'ERROR: unknown project type "{p}". Valid: {", ".join(VALID_TYPES)}', file=sys.stderr)
            sys.exit(1)
    return parts


def run_audit(project_types: list[str], docs_path: str) -> dict:
    all_issues: list[str] = []

    req_issues, fr_ids = check_requirements(docs_path)
    all_issues += req_issues

    for pt in project_types:
        all_issues += check_test_plan(docs_path, pt, fr_ids)
        all_issues += check_test_report(docs_path, pt)

        if pt in PIPELINE_TYPES:
            all_issues += check_pipeline_contracts(docs_path)
        if pt in LLM_TYPES:
            all_issues += check_llm_eval(docs_path)

    # Deduplicate while preserving order
    seen: set[str] = set()
    deduped: list[str] = []
    for issue in all_issues:
        if issue not in seen:
            seen.add(issue)
            deduped.append(issue)

    return {'passed': len(deduped) == 0, 'issues': deduped}


def main() -> None:
    parser = argparse.ArgumentParser(
        description='verify_acceptance.py — functional acceptance gate'
    )
    parser.add_argument('--project-type', required=True,
                        help='Project type (e.g. web-app, cli-tool, data-pipeline+web-app)')
    parser.add_argument('--docs', default='docs',
                        help='Path to docs directory (default: docs)')
    parser.add_argument('--strict', action='store_true',
                        help='Exit 1 on any issue')
    parser.add_argument('--json', action='store_true', dest='as_json',
                        help='Output JSON instead of human-readable text')
    args = parser.parse_args()

    project_types = parse_types(args.project_type)
    result = run_audit(project_types, args.docs)

    if args.as_json:
        print(json.dumps(result, indent=2))
    else:
        if result['passed']:
            print(f'verify_acceptance ✅  all acceptance checks passed ({args.project_type})')
        else:
            print(
                f'verify_acceptance ❌  {len(result["issues"])} issue(s) found '
                f'({args.project_type}):'
            )
            for issue in result['issues']:
                print(f'  • {issue}')

    ts = _telemetry_ts()
    status = 'pass' if result['passed'] else 'fail'
    _append_telemetry('verify_acceptance', args.project_type, status, ts)

    if not result['passed'] and args.strict:
        sys.exit(1)


if __name__ == '__main__':
    main()
