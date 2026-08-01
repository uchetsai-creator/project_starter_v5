#!/usr/bin/env python3
"""
verify_index_coverage.py — Index <-> per-item file coverage audit for project_starter_v5 projects.

Some documents are a single index table that points at one file per row:
  docs/business/business-objects.md  -> docs/business/[object]-object.md
  docs/business/business-process.md  -> docs/business/[process]-process.md
  docs/specs/prompt-library.md       -> docs/specs/prompts/[prompt-id]-prompt.md

Unlike module-flow.md / log-<module>.md (audited by verify_module_docs.py against
scan_codebase.py), these per-item files have no source-code equivalent to scan — a
business object or a prompt isn't discovered by walking src/. The only signal
available is the index table itself, so this validator cross-checks it both ways:

  missing_files : declared in the index, but the file doesn't exist
  orphan_files  : file exists under docs/business/ or docs/specs/prompts/, but no
                  row in the matching index references it

Each index is checked only if it exists — that alone is the type-applicability
gate (business-objects.md / business-process.md are N/A for most non-web-app
types and are never created for them; prompt-library.md is llm-app only).

Usage:
  python3 docs/script/validators/verify_index_coverage.py
  python3 docs/script/validators/verify_index_coverage.py --docs PATH
  python3 docs/script/validators/verify_index_coverage.py --strict
  python3 docs/script/validators/verify_index_coverage.py --json
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _verify_common import _append_telemetry, _is_placeholder, _read_file, _telemetry_ts

# Each entry: (index_file, section_header, item_dir, item_suffix, path_is_docs_relative)
# path_is_docs_relative: the File column's own path is relative to docs/ root
# (business indexes) vs. relative to docs/specs/ (prompt-library.md).
_INDEXES = [
    {
        'name': 'business-objects',
        'index_path': 'business/business-objects.md',
        'section': r'## Object Files',
        'item_glob_dir': 'business',
        'item_suffix': '-object.md',
        'path_base': '',  # File column already 'docs/business/...'
    },
    {
        'name': 'business-process',
        'index_path': 'business/business-process.md',
        'section': r'## Process Files',
        'item_glob_dir': 'business',
        'item_suffix': '-process.md',
        'path_base': '',
    },
    {
        'name': 'prompt-library',
        'index_path': 'specs/prompt-library.md',
        'section': r'## Active Prompts',
        'item_glob_dir': 'specs/prompts',
        'item_suffix': '-prompt.md',
        'path_base': 'specs/',  # File column is 'prompts/[id]-prompt.md', relative to docs/specs/
    },
]


def _table_rows(text: str, section_header: str) -> tuple[list[str], list[list[str]]]:
    """Return (header_cells, data_rows) for the first table found under `section_header`."""
    m = re.search(rf'^{section_header}\s*$', text, re.MULTILINE)
    if not m:
        return [], []
    body = text[m.end():]
    next_h = re.search(r'^#{1,3}\s', body, re.MULTILINE)
    if next_h:
        body = body[:next_h.start()]

    header: list[str] = []
    rows: list[list[str]] = []
    header_seen = False
    for line in body.splitlines():
        line = line.strip()
        if not line.startswith('|') or not line.endswith('|'):
            continue
        cols = [c.strip() for c in line.strip('|').split('|')]
        if not header_seen:
            header = cols
            header_seen = True  # first table row is the header
            continue
        if all(re.match(r'^:?-+:?$', c) for c in cols):
            continue  # separator row
        rows.append(cols)
    return header, rows


def _extract_declared_paths(docs_dir: str, cfg: dict) -> tuple[list[str], list[str]]:
    """Returns (declared_relative_paths, skipped_placeholder_labels)."""
    index_path = os.path.join(docs_dir, cfg['index_path'])
    lines = _read_file(index_path)
    if lines is None:
        return [], []

    text = '\n'.join(lines)
    header, rows = _table_rows(text, cfg['section'])
    try:
        file_col = next(i for i, h in enumerate(header) if h.strip().lower() == 'file')
    except StopIteration:
        return [], []  # table has no 'File' column — nothing to cross-check

    declared: list[str] = []
    for cols in rows:
        if len(cols) <= file_col:
            continue
        label, file_cell = cols[0], cols[file_col]
        if _is_placeholder(label) or _is_placeholder(file_cell):
            continue
        rel_path = file_cell.strip('`').strip()
        if not rel_path:
            continue
        # business-objects.md / business-process.md write the File column as a
        # docs-root-relative path (e.g. 'docs/business/order-object.md') even
        # though docs_dir itself is the docs root — strip the redundant prefix
        # so it isn't joined twice. prompt-library.md's File column has no such
        # prefix (it's already relative to docs/specs/), so this is a no-op there.
        if rel_path.startswith('docs/'):
            rel_path = rel_path[len('docs/'):]
        declared.append(rel_path)
    return declared, []


def _existing_item_files(docs_dir: str, cfg: dict) -> set[str]:
    item_dir = os.path.join(docs_dir, cfg['item_glob_dir'])
    if not os.path.isdir(item_dir):
        return set()
    # Exclude the index file itself — e.g. business-process.md ends in '-process.md',
    # the same suffix as its own per-item files, so it would otherwise flag itself as
    # an orphan of its own index.
    index_basename = os.path.basename(cfg['index_path'])
    return {
        fname for fname in os.listdir(item_dir)
        if fname.endswith(cfg['item_suffix'])
        and fname != index_basename
        and os.path.isfile(os.path.join(item_dir, fname))
    }


def audit(docs_dir: str) -> list[dict]:
    """One result dict per index that exists: {name, missing_files, orphan_files}."""
    results: list[dict] = []

    for cfg in _INDEXES:
        index_path = os.path.join(docs_dir, cfg['index_path'])
        if not os.path.isfile(index_path):
            continue  # N/A for this project type / not created yet

        declared, _ = _extract_declared_paths(docs_dir, cfg)
        existing = _existing_item_files(docs_dir, cfg)

        base = os.path.join(docs_dir, cfg['path_base']) if cfg['path_base'] else docs_dir
        declared_basenames: set[str] = set()
        missing_files: list[str] = []
        for rel_path in declared:
            abs_path = os.path.normpath(os.path.join(base, rel_path))
            basename = os.path.basename(abs_path)
            declared_basenames.add(basename)
            if not os.path.isfile(abs_path):
                missing_files.append(rel_path)

        orphan_files = sorted(existing - declared_basenames)

        results.append({
            'name': cfg['name'],
            'index_path': cfg['index_path'],
            'declared_count': len(declared),
            'existing_count': len(existing),
            'missing_files': missing_files,
            'orphan_files': orphan_files,
        })

    return results


def print_results(results: list[dict]) -> None:
    if not results:
        print("[WARN] No index files found (business-objects.md / business-process.md / "
              "prompt-library.md) — nothing to check.")
        return

    print("\nIndex <-> File Coverage")
    print('─' * 70)
    for r in results:
        print(f"\n{r['index_path']}")
        print(f"  Declared : {r['declared_count']}   Existing files : {r['existing_count']}")
        if r['missing_files']:
            print("  [FAIL] Declared in index, file missing:")
            for f in r['missing_files']:
                print(f"       - {f}")
        if r['orphan_files']:
            print("  [WARN] File exists, no row in index:")
            for f in r['orphan_files']:
                print(f"       - {f}")
        if not r['missing_files'] and not r['orphan_files']:
            print("  [OK] Index and files match")
    print()


def print_results_json(results: list[dict], docs_dir: str) -> None:
    print(json.dumps({'docs_dir': docs_dir, 'indexes': results}, ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(
        description='Audit index <-> per-item file coverage for project_starter_v5 projects.',
    )
    parser.add_argument('--docs', default='docs', metavar='PATH',
                        help='Path to docs directory (default: docs)')
    parser.add_argument('--strict', action='store_true', help='Exit 1 if any check fails')
    parser.add_argument('--json', action='store_true', dest='json_output', help='Output results as JSON')
    parser.add_argument('--telemetry', action='store_true',
                        help='Append result to .ai/telemetry/validation-result.json')
    args = parser.parse_args()

    if not os.path.isdir(args.docs):
        print(f'error: docs directory not found: {args.docs}', file=sys.stderr)
        sys.exit(2)

    results = audit(args.docs)

    if args.json_output:
        print_results_json(results, args.docs)
    else:
        print_results(results)

    if args.telemetry:
        fail_count = sum(1 for r in results if r['missing_files'])
        warn_count = sum(1 for r in results if r['orphan_files'])
        _append_telemetry({
            'ts': _telemetry_ts(),
            'project_type': None,
            'validator': 'verify_index_coverage.py',
            'level': 'fail' if fail_count > 0 else 'warn' if warn_count > 0 else 'pass',
            'warn_count': warn_count,
            'fail_count': fail_count,
            'failed_docs': [r['name'] for r in results if r['missing_files']],
        })

    if args.strict and any(r['missing_files'] for r in results):
        sys.exit(1)


if __name__ == '__main__':
    main()
