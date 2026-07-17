#!/usr/bin/env python3
"""
verify_docs.py — Document completeness audit for project_starter_v4 projects.

Usage:
  python3 docs/script/verify_docs.py --project-type TYPE
  python3 docs/script/verify_docs.py --project-type TYPE --docs PATH
  python3 docs/script/verify_docs.py --project-type TYPE --strict
  python3 docs/script/verify_docs.py --project-type TYPE --json

Valid project types: web-app | cli-tool | library | data-pipeline | ml-pipeline | microservices | llm-app | iac | mobile-app
Hybrid types use +: data-pipeline+web-app  (takes union of both type matrices)
"""

import argparse
import json
import os
import sys

VALID_TYPES = [
    'web-app', 'cli-tool', 'library',
    'data-pipeline', 'ml-pipeline', 'microservices', 'llm-app', 'iac', 'mobile-app',
]

TYPE_INDEX = {t: i for i, t in enumerate(VALID_TYPES)}

# R = Required, O = Optional, N = Not applicable
# Column order: web-app, cli-tool, library, data-pipeline, ml-pipeline, microservices, llm-app, iac, mobile-app
# Derived from templates/init/document-matrix.md — conditional cells (e.g. "⚠️ if DB") treated as O.
MATRIX = {
    'architecture.md':         ('R', 'R', 'O', 'R', 'R', 'R', 'R', 'N', 'R'),
    'backend.md':              ('R', 'R', 'N', 'R', 'R', 'O', 'O', 'N', 'O'),
    'frontend.md':             ('O', 'N', 'N', 'N', 'N', 'O', 'O', 'N', 'R'),
    'database.md':             ('R', 'O', 'N', 'R', 'R', 'O', 'O', 'N', 'O'),
    'deployment.md':           ('R', 'N', 'N', 'R', 'R', 'R', 'O', 'N', 'N'),
    'distribution.md':         ('N', 'R', 'R', 'N', 'N', 'N', 'N', 'N', 'R'),
    'api-contract.md':         ('R', 'N', 'N', 'N', 'N', 'R', 'O', 'N', 'O'),
    'cli-contract.md':         ('N', 'R', 'N', 'N', 'N', 'N', 'O', 'N', 'N'),
    'public-api.md':           ('N', 'N', 'R', 'N', 'N', 'N', 'N', 'N', 'N'),
    'pipeline-contract.md':    ('N', 'N', 'N', 'R', 'R', 'N', 'N', 'N', 'N'),
    'pipeline-debug.md':       ('N', 'N', 'N', 'R', 'R', 'N', 'N', 'N', 'N'),
    'llm-contract.md':         ('N', 'N', 'N', 'N', 'N', 'N', 'R', 'N', 'N'),
    'prompt-library.md':       ('N', 'N', 'N', 'N', 'N', 'N', 'R', 'N', 'N'),
    'eval-spec.md':            ('N', 'N', 'N', 'N', 'N', 'N', 'R', 'N', 'N'),
    'eval-log.md':             ('N', 'N', 'N', 'N', 'N', 'N', 'R', 'N', 'N'),
    'llm-debug.md':            ('N', 'N', 'N', 'N', 'N', 'N', 'R', 'N', 'N'),
    'rag-contract.md':         ('N', 'N', 'N', 'N', 'N', 'N', 'O', 'N', 'N'),
    'mcp-contract.md':         ('N', 'N', 'N', 'N', 'N', 'N', 'O', 'N', 'N'),
    'service-catalog.md':      ('N', 'N', 'N', 'N', 'N', 'R', 'N', 'N', 'N'),
    'service-contract.md':     ('N', 'N', 'N', 'N', 'N', 'R', 'N', 'N', 'N'),
    'event-catalog.md':        ('N', 'N', 'N', 'N', 'N', 'O', 'N', 'N', 'N'),
    'model-contract.md':       ('N', 'N', 'N', 'N', 'R', 'N', 'N', 'N', 'N'),
    'experiment-log.md':       ('N', 'N', 'N', 'N', 'R', 'N', 'N', 'N', 'N'),
    'release-guide.md':        ('N', 'R', 'R', 'N', 'N', 'N', 'N', 'N', 'N'),
    'compatibility-matrix.md': ('N', 'O', 'R', 'N', 'N', 'N', 'N', 'N', 'O'),
    'permissions.md':          ('R', 'N', 'N', 'N', 'N', 'R', 'O', 'N', 'O'),
    'data-model.md':           ('R', 'O', 'N', 'R', 'R', 'O', 'O', 'N', 'O'),
    'business-process.md':     ('R', 'O', 'N', 'O', 'N', 'R', 'N', 'N', 'O'),
    'business-objects.md':     ('R', 'N', 'N', 'N', 'N', 'R', 'N', 'N', 'N'),
    'business-rules.md':       ('R', 'O', 'N', 'R', 'O', 'R', 'O', 'N', 'O'),
    'logging-spec.md':         ('R', 'R', 'N', 'R', 'R', 'R', 'O', 'N', 'R'),
    'research.md':             ('R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R'),
    'quickstart.md':           ('R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R'),
    # IaC / DevOps — specific documents
    'topology.md':             ('N', 'N', 'N', 'N', 'N', 'N', 'N', 'R', 'N'),
    'runbook.md':              ('N', 'N', 'N', 'N', 'N', 'N', 'N', 'R', 'N'),
    'drift-policy.md':         ('N', 'N', 'N', 'N', 'N', 'N', 'N', 'R', 'N'),
    # Mobile App — specific documents
    'mobile-contract.md':      ('N', 'N', 'N', 'N', 'N', 'N', 'N', 'N', 'R'),
    # Universal — all project types
    'test-plan.md':            ('R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R'),
    'test-report.md':          ('R', 'R', 'R', 'R', 'R', 'R', 'R', 'R', 'R'),
}

FILE_LOCATIONS = {
    'architecture.md':         'architecture',
    'backend.md':              'architecture',
    'frontend.md':             'architecture',
    'database.md':             'architecture',
    'deployment.md':           'architecture',
    'distribution.md':         'architecture',
    'api-contract.md':         'specs',
    'cli-contract.md':         'specs',
    'public-api.md':           'specs',
    'pipeline-contract.md':    'specs',
    'pipeline-debug.md':       'specs',
    'llm-contract.md':         'specs',
    'prompt-library.md':       'specs',
    'eval-spec.md':            'specs',
    'eval-log.md':             'specs',
    'llm-debug.md':            'specs',
    'rag-contract.md':         'specs',
    'mcp-contract.md':         'specs',
    'service-catalog.md':      'specs',
    'service-contract.md':     'specs',
    'event-catalog.md':        'specs',
    'model-contract.md':       'specs',
    'experiment-log.md':       'specs',
    'release-guide.md':        'specs',
    'compatibility-matrix.md': 'specs',
    'permissions.md':          'specs',
    'data-model.md':           'specs',
    'business-process.md':     'business',
    'business-objects.md':     'business',
    'business-rules.md':       'business',
    'logging-spec.md':         'specs',
    'research.md':             'specs',
    'quickstart.md':           'specs',
    # IaC / DevOps
    'topology.md':             'architecture',
    'runbook.md':              'specs',
    'drift-policy.md':         'specs',
    # Mobile App
    'mobile-contract.md':      'specs',
    # Universal
    'test-plan.md':            'specs',
    'test-report.md':          'specs',
}

SCANNED_DIRS = ('specs', 'architecture', 'business')


def effective_status(doc_name, types):
    """Return R/O/N for the given doc across all declared types (union rule)."""
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


def run_audit(types, docs_dir):
    existing = collect_existing(docs_dir)
    matrix_names = set(MATRIX.keys())
    results = []

    for doc_name in MATRIX:
        location = FILE_LOCATIONS.get(doc_name, 'specs')
        status = effective_status(doc_name, types)
        file_exists = (location, doc_name) in existing
        path = f'{location}/{doc_name}'

        if status == 'N':
            if file_exists:
                results.append({'doc': path, 'status': 'orphan',
                                'label': '🔍 Orphan',
                                'note': f'N/A for {"+".join(types)} but file exists'})
            else:
                results.append({'doc': path, 'status': 'na', 'label': '—  N/A', 'note': ''})
        elif status == 'R':
            if file_exists:
                results.append({'doc': path, 'status': 'present', 'label': '✅ Present', 'note': ''})
            else:
                results.append({'doc': path, 'status': 'missing_required',
                                'label': '❌ Missing Required', 'note': ''})
        else:
            if file_exists:
                results.append({'doc': path, 'status': 'present',
                                'label': '✅ Present', 'note': '(optional)'})
            else:
                results.append({'doc': path, 'status': 'missing_optional',
                                'label': '⚠️  Missing Optional', 'note': ''})

    for subdir, fname in sorted(existing):
        if fname not in matrix_names:
            results.append({'doc': f'{subdir}/{fname}', 'status': 'orphan',
                            'label': '🔍 Orphan', 'note': 'not in document matrix'})

    return results


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
            print(f'  {r["label"]:<24} {r["doc"]}{note}')

    total_required = counts['present'] + counts['missing_required']
    present_required = sum(
        1 for r in results if r['status'] == 'present' and r['note'] != '(optional)'
    )

    print()
    print(f'  Required : {present_required} / {total_required} present')
    if counts['missing_optional']:
        print(f'  Optional missing : {counts["missing_optional"]}')
    if counts['orphan']:
        print(f'  Orphans  : {counts["orphan"]}')
    print()


def main():
    parser = argparse.ArgumentParser(
        description='Audit document completeness for a project_starter_v4 project.',
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

    results = run_audit(types, args.docs)

    if args.json_output:
        print(json.dumps(
            {'project_type': args.project_type, 'results': results},
            ensure_ascii=False, indent=2,
        ))
    else:
        print_results(results, types)

    if args.strict and any(r['status'] == 'missing_required' for r in results):
        sys.exit(1)


if __name__ == '__main__':
    main()
