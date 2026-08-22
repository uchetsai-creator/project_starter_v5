#!/usr/bin/env python3
"""
verify_workflow_registry.py — Schema validator for workflow-registry.yaml.

document-registry.yaml has verify_registry.py checking its shape before anything
downstream trusts it. workflow-registry.yaml had no equivalent — a bad entry (a
validator script path that doesn't exist, a task type with an empty validators list, a
missing "default" fallback) only surfaced at orchestrator.py's runtime, not before a
commit. See docs/architecture-analysis.md -> Coupling Problem Catalogue, "Validator
sequencing has no equivalent schema gate."

Checks:
  - top-level 'workflows' key present, is a mapping
  - a 'default' entry exists — orchestrator.py's _build_workflow() silently falls back
    to workflows.get(workflow_key, {}), i.e. zero validators, when the current task
    type has no matching entry and 'default' is also missing
  - each workflow entry is a mapping with only a 'validators' key (no unknown keys)
  - 'validators' is a non-empty list
  - each validator item is a mapping with 'script' (non-empty string, ends in .py) and,
    if present, 'args' (a list of strings)
  - 'script' resolves to a real file. workflow-registry.yaml's script paths are written
    for their *post-init* location in a downstream project (docs/script/validators/...,
    where init.py copies templates/script/ into). Resolution tries that path as-is
    first (the real case for every downstream project), then falls back to translating
    docs/script/ -> templates/script/ (this framework repo's own source location) so
    this validator also works when run against project_starter_v5's own tree.

Usage:
  python3 verify_workflow_registry.py
  python3 verify_workflow_registry.py --registry path/to/workflow-registry.yaml
  python3 verify_workflow_registry.py --json

Exit codes:
  0 — schema valid
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
    print("[FAIL] PyYAML not found. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

_ENTRY_KNOWN_FIELDS: frozenset[str] = frozenset(['validators'])
_ITEM_KNOWN_FIELDS: frozenset[str] = frozenset(['script', 'args'])
_POST_INIT_PREFIX = 'docs/script/'
_FRAMEWORK_SRC_PREFIX = 'templates/script/'


def _resolve_script_path(script: str, root: Path) -> Path | None:
    """Return the resolved path if it exists, or None if it resolves nowhere.

    Tries the path as written first (the real location in a downstream project after
    --init) before falling back to the docs/script/ -> templates/script/ translation
    init.py performs — so this validator works both against a real downstream project
    and against this framework repo's own tree."""
    direct = root / script
    if direct.exists():
        return direct
    if script.startswith(_POST_INIT_PREFIX):
        translated = root / (_FRAMEWORK_SRC_PREFIX + script[len(_POST_INIT_PREFIX):])
        if translated.exists():
            return translated
    return None


def _validate_workflow_entry(entry, root: Path) -> list[str]:
    errors: list[str] = []
    if not isinstance(entry, dict):
        return [f"entry must be a mapping, got {type(entry).__name__}"]

    unknown = set(entry.keys()) - _ENTRY_KNOWN_FIELDS
    if unknown:
        errors.append(f"unknown fields: {sorted(unknown)}")

    validators = entry.get('validators')
    if validators is None:
        errors.append("missing required field 'validators'")
        return errors
    if not isinstance(validators, list):
        errors.append(f"'validators' must be a list, got {type(validators).__name__}")
        return errors
    if not validators:
        errors.append("'validators' is empty — this workflow would run zero checks")

    for i, item in enumerate(validators):
        if not isinstance(item, dict):
            errors.append(f"validators[{i}] must be a mapping, got {type(item).__name__}")
            continue

        item_unknown = set(item.keys()) - _ITEM_KNOWN_FIELDS
        if item_unknown:
            errors.append(f"validators[{i}] unknown fields: {sorted(item_unknown)}")

        script = item.get('script')
        if not isinstance(script, str) or not script.strip():
            errors.append(f"validators[{i}].script must be a non-empty string")
        else:
            if not script.endswith('.py'):
                errors.append(f"validators[{i}].script must end with .py (got '{script}')")
            if _resolve_script_path(script, root) is None:
                errors.append(
                    f"validators[{i}].script '{script}' does not resolve to a real file "
                    f"(tried '{script}' and the templates/script/ translation, both under {root})",
                )

        args = item.get('args', [])
        if not isinstance(args, list):
            errors.append(f"validators[{i}].args must be a list, got {type(args).__name__}")
        else:
            for j, a in enumerate(args):
                if not isinstance(a, str):
                    errors.append(
                        f"validators[{i}].args[{j}] must be a string, got {type(a).__name__}",
                    )

    return errors


def validate(registry_path: Path) -> dict[str, list[str]]:
    """Validate workflow-registry.yaml. Returns {task_type: [error, ...]} for failing
    entries; '<top-level>' holds errors not tied to one specific entry."""
    with registry_path.open(encoding='utf-8') as fh:
        data = yaml.safe_load(fh) or {}

    workflows = data.get('workflows')
    if not isinstance(workflows, dict):
        raise ValueError("Top-level 'workflows' key must be a YAML mapping")

    root = registry_path.resolve().parent
    results: dict[str, list[str]] = {}

    if 'default' not in workflows:
        results['<top-level>'] = [
            "no 'default' workflow entry — orchestrator.py's _build_workflow() silently "
            "falls back to zero validators for any task type not explicitly listed here",
        ]

    for name, entry in workflows.items():
        errs = _validate_workflow_entry(entry, root)
        if errs:
            results[name] = errs

    return results


def _find_registry(cli_path: str | None) -> Path:
    if cli_path:
        return Path(cli_path)
    candidates = [
        Path.cwd() / 'workflow-registry.yaml',
        Path(__file__).resolve().parent.parent.parent / 'workflow-registry.yaml',
    ]
    for p in candidates:
        if p.exists():
            return p
    raise FileNotFoundError(
        'workflow-registry.yaml not found. '
        f'Searched: {[str(c) for c in candidates]}',
    )


def main() -> None:
    # Force UTF-8 stdout/stderr — see verify_registry.py's main() for the
    # Windows-console rationale (non-ASCII characters otherwise crash print()).
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[union-attr]  # guard above only narrows sys.stdout

    parser = argparse.ArgumentParser(
        description="Validate workflow-registry.yaml against the project_starter_v5 schema.",
    )
    parser.add_argument(
        '--registry', metavar='PATH',
        help='Path to workflow-registry.yaml (default: auto-discover from CWD or framework root)',
    )
    parser.add_argument(
        '--json', action='store_true', dest='json_output',
        help='Output results as JSON',
    )
    args = parser.parse_args()

    try:
        registry_path = _find_registry(args.registry)
    except FileNotFoundError as e:
        print(f"[FAIL] {e}", file=sys.stderr)
        sys.exit(2)

    try:
        errors = validate(registry_path)
    except (yaml.YAMLError, ValueError) as e:
        print(f"[FAIL] Failed to parse registry: {e}", file=sys.stderr)
        sys.exit(2)

    if args.json_output:
        print(json.dumps(
            {'registry': str(registry_path), 'valid': not errors, 'errors': errors},
            indent=2,
        ))
    elif not errors:
        total = sum(1 for _ in (yaml.safe_load(
            registry_path.read_text(encoding='utf-8')
        ) or {}).get('workflows', {}).items())
        print(f"[OK] Workflow registry schema valid — {total} task type(s) ({registry_path.name})")
    else:
        print(f"[FAIL] Workflow registry schema violations ({registry_path.name}):")
        for key in sorted(errors):
            for err in errors[key]:
                print(f"    {key}: {err}")

    sys.exit(1 if errors else 0)


if __name__ == '__main__':
    main()
