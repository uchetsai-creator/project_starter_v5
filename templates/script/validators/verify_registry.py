#!/usr/bin/env python3
"""
verify_registry.py — Registry schema validator for project_starter_v5.

Validates every entry in document-registry.yaml against the schema rules.
No external dependencies beyond PyYAML (already required by orchestrator.py).

Usage:
  python3 verify_registry.py
  python3 verify_registry.py --registry path/to/document-registry.yaml
  python3 verify_registry.py --json

Exit codes:
  0 — all entries valid
  1 — one or more schema violations
  2 — registry file not found or unparseable
"""

import argparse
import json
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    print("❌  PyYAML not found. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

VALID_TYPES: frozenset[str] = frozenset([
    'web-app', 'cli-tool', 'library',
    'data-pipeline', 'ml-pipeline', 'microservices', 'llm-app', 'iac', 'mobile-app',
])
VALID_PRIORITIES: frozenset[str] = frozenset(['high', 'medium', 'low'])
VALID_AUDIENCES: frozenset[str] = frozenset(['internal', 'external'])

REQUIRED_FIELDS: frozenset[str] = frozenset([
    'file', 'path', 'context_priority', 'pdf', 'audience', 'required_sections', 'update_trigger',
])
KNOWN_FIELDS: frozenset[str] = REQUIRED_FIELDS | frozenset([
    'required_for', 'optional_for', 'replaces_for', 'task_types', 'purpose', 'used_by', 'related',
])


def _validate_entry(key: str, meta: dict) -> list[str]:
    errors: list[str] = []

    missing = REQUIRED_FIELDS - meta.keys()
    for field in sorted(missing):
        errors.append(f"missing required field '{field}'")
    if missing:
        return errors

    if not isinstance(meta['file'], str):
        errors.append(f"'file' must be a string, got {type(meta['file']).__name__}")
    elif not meta['file'].endswith('.md'):
        errors.append(f"'file' must end with .md (got '{meta['file']}')")

    if not isinstance(meta['path'], str):
        errors.append(f"'path' must be a string, got {type(meta['path']).__name__}")
    elif not meta['path'].endswith('.md'):
        errors.append(f"'path' must end with .md (got '{meta['path']}')")

    if meta['context_priority'] not in VALID_PRIORITIES:
        errors.append(
            f"'context_priority' must be high|medium|low (got '{meta['context_priority']}')"
        )

    if not isinstance(meta['pdf'], bool):
        errors.append(
            f"'pdf' must be a boolean true/false, got {type(meta['pdf']).__name__} ({meta['pdf']!r})"
        )

    if meta['audience'] not in VALID_AUDIENCES:
        errors.append(f"'audience' must be internal|external (got '{meta['audience']}')")

    if not isinstance(meta['required_sections'], list):
        errors.append(
            f"'required_sections' must be a list, got {type(meta['required_sections']).__name__}"
        )
    else:
        for i, s in enumerate(meta['required_sections']):
            if not isinstance(s, str):
                errors.append(
                    f"'required_sections[{i}]' must be a string, got {type(s).__name__}"
                )

    if not isinstance(meta['update_trigger'], str):
        errors.append(
            f"'update_trigger' must be a string, got {type(meta['update_trigger']).__name__}"
        )
    elif not meta['update_trigger'].strip():
        errors.append("'update_trigger' must not be empty")

    for list_field in ('required_for', 'optional_for'):
        val = meta.get(list_field, [])
        if not isinstance(val, list):
            errors.append(f"'{list_field}' must be a list, got {type(val).__name__}")
        else:
            for pt in val:
                if pt not in VALID_TYPES:
                    errors.append(f"'{list_field}' contains unknown project type '{pt}'")

    rf = meta.get('replaces_for')
    if rf is not None:
        if not isinstance(rf, dict):
            errors.append(f"'replaces_for' must be a mapping, got {type(rf).__name__}")
        else:
            for pt in rf:
                if pt not in VALID_TYPES:
                    errors.append(f"'replaces_for' has unknown project type key '{pt}'")

    unknown = set(meta.keys()) - KNOWN_FIELDS
    if unknown:
        errors.append(f"unknown fields: {sorted(unknown)}")

    return errors


def validate(registry_path: Path) -> dict[str, list[str]]:
    """Validate document-registry.yaml. Returns {doc_key: [error, ...]} for failing entries."""
    with registry_path.open(encoding='utf-8') as fh:
        data = yaml.safe_load(fh) or {}

    documents = data.get('documents', {})
    if not isinstance(documents, dict):
        raise ValueError("Top-level 'documents' key must be a YAML mapping")

    return {
        key: errs
        for key, meta in documents.items()
        if (errs := (
            [f"entry must be a mapping, got {type(meta).__name__}"]
            if not isinstance(meta, dict)
            else _validate_entry(key, meta)
        ))
    }


def _find_registry(cli_path: str | None) -> Path:
    if cli_path:
        return Path(cli_path)
    candidates = [
        Path.cwd() / 'document-registry.yaml',
        Path(__file__).resolve().parent.parent.parent / 'document-registry.yaml',
    ]
    for p in candidates:
        if p.exists():
            return p
    raise FileNotFoundError(
        'document-registry.yaml not found. '
        f'Searched: {[str(c) for c in candidates]}'
    )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Validate document-registry.yaml against the project_starter_v5 schema."
    )
    parser.add_argument(
        '--registry', metavar='PATH',
        help='Path to document-registry.yaml (default: auto-discover from CWD or framework root)',
    )
    parser.add_argument(
        '--json', action='store_true', dest='json_output',
        help='Output results as JSON',
    )
    args = parser.parse_args()

    try:
        registry_path = _find_registry(args.registry)
    except FileNotFoundError as e:
        print(f"❌  {e}", file=sys.stderr)
        sys.exit(2)

    try:
        errors = validate(registry_path)
    except (yaml.YAMLError, ValueError) as e:
        print(f"❌  Failed to parse registry: {e}", file=sys.stderr)
        sys.exit(2)

    if args.json_output:
        print(json.dumps(
            {'registry': str(registry_path), 'valid': not errors, 'errors': errors},
            indent=2,
        ))
    elif not errors:
        total = sum(1 for _ in (yaml.safe_load(
            registry_path.read_text(encoding='utf-8')
        ) or {}).get('documents', {}).items())
        print(f"✅  Registry schema valid — {total} entries ({registry_path.name})")
    else:
        print(f"❌  Registry schema violations ({registry_path.name}):")
        for key in sorted(errors):
            for err in errors[key]:
                print(f"    {key}: {err}")

    sys.exit(1 if errors else 0)


if __name__ == '__main__':
    main()
