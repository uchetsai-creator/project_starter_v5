#!/usr/bin/env python3
"""
verify_spec_code.py — Spec ↔ code drift validator for project_starter_v5.

Compares what the spec declares against what the code implements. Adapters
translate both spec and code into NormalizedForm objects; the core compares
them. No framework-specific logic lives here — all of that belongs in adapters.

Usage:
  python3 verify_spec_code.py --project-type data-pipeline --adapter airflow \\
      --spec docs/specs/pipeline-contract.md --src src/stages/ --strict
  python3 verify_spec_code.py --project-type cli-tool --adapter click \\
      --spec docs/specs/cli-contract.md --src src/cli.py --strict
  python3 verify_spec_code.py --project-type data-pipeline --adapter airflow \\
      --spec docs/specs/pipeline-contract.md --src src/ --json

If --adapter / --spec / --src are not supplied (e.g. when called from the
pre-commit hook on an unconfigured project), the validator prints a warning
and exits 0 — it never blocks an unconfigured project.

Valid project types:
  web-app | cli-tool | library | data-pipeline | ml-pipeline |
  microservices | llm-app | iac | mobile-app

Valid adapters (Phase 45):
  airflow  — Data Pipeline / ML Pipeline (Apache Airflow)
  click    — CLI Tool (Click)
"""

import argparse
import importlib
import json
import os
import sys
from pathlib import Path

VALID_PROJECT_TYPES = [
    'web-app', 'cli-tool', 'library', 'data-pipeline', 'ml-pipeline',
    'microservices', 'llm-app', 'iac', 'mobile-app',
]

# adapter_name → (module_filename, class_name)
ADAPTER_REGISTRY: dict[str, tuple[str, str]] = {
    'airflow': ('airflow', 'AirflowAdapter'),
    'click':   ('click',   'ClickAdapter'),
}

_ADAPTER_DIR = Path(__file__).resolve().parent / '_spec_code_adapters'


def _load_adapter(adapter_name: str):
    entry = ADAPTER_REGISTRY.get(adapter_name)
    if not entry:
        print(
            f"error: unknown adapter '{adapter_name}'. "
            f"Available: {', '.join(ADAPTER_REGISTRY)}",
            file=sys.stderr,
        )
        sys.exit(2)
    module_name, class_name = entry
    sys.path.insert(0, str(_ADAPTER_DIR))
    try:
        module = importlib.import_module(module_name)
        return getattr(module, class_name)()
    except (ImportError, AttributeError) as exc:
        print(f"error: could not load adapter '{adapter_name}': {exc}", file=sys.stderr)
        sys.exit(2)


# ---------------------------------------------------------------------------
# Comparison helpers
# ---------------------------------------------------------------------------

def _item_key(item) -> str:
    if hasattr(item, 'stage_name'):
        return item.stage_name.lower()
    if hasattr(item, 'method') and hasattr(item, 'path'):
        return f"{item.method.upper()}:{item.path}"
    return getattr(item, 'name', repr(item)).lower()


def _item_label(item) -> str:
    if hasattr(item, 'stage_name'):
        return item.stage_name
    if hasattr(item, 'method') and hasattr(item, 'path'):
        return f"{item.method} {item.path}"
    return getattr(item, 'name', repr(item))


def _item_fields(item) -> list:
    """Return the list of NormalizedField objects for any NormalizedForm."""
    sys.path.insert(0, str(_ADAPTER_DIR))
    from _base import (  # noqa: PLC0415
        NormalizedField, NormalizedStageContract, NormalizedEndpoint,
        NormalizedCommand, NormalizedFunction, NormalizedTool,
        NormalizedResource, NormalizedScreen,
    )
    if isinstance(item, NormalizedStageContract):
        return list(item.input_fields) + list(item.output_fields)
    if isinstance(item, NormalizedEndpoint):
        return list(item.request_fields) + list(item.response_fields)
    if isinstance(item, NormalizedCommand):
        return list(item.flags)
    if isinstance(item, NormalizedFunction):
        return list(item.params)
    if isinstance(item, NormalizedTool):
        return list(item.parameters)
    if isinstance(item, NormalizedResource):
        return [NormalizedField(name=k, type='') for k in item.config_keys]
    if isinstance(item, NormalizedScreen):
        return list(item.props)
    return []


def compare(spec_items: list, code_items: list) -> dict:
    """
    Compare spec vs code NormalizedForm lists.

    Returns:
      missing_in_code: list[str]   — declared in spec, absent in code
      extra_in_code:   list[str]   — in code, not in spec
      field_mismatches: list[dict] — {item, field, issue, spec_type, code_type}

    Issues: removed_from_code | added_in_code | type_changed
    """
    spec_by_key = {_item_key(i): i for i in spec_items}
    code_by_key = {_item_key(i): i for i in code_items}

    missing_in_code = [
        _item_label(spec_by_key[k])
        for k in spec_by_key if k not in code_by_key
    ]
    extra_in_code = [
        _item_label(code_by_key[k])
        for k in code_by_key if k not in spec_by_key
    ]

    field_mismatches: list[dict] = []
    for key in spec_by_key:
        if key not in code_by_key:
            continue
        spec_item = spec_by_key[key]
        code_item = code_by_key[key]
        spec_fields = {f.name: f for f in _item_fields(spec_item)}
        code_fields = {f.name: f for f in _item_fields(code_item)}

        for fname, sf in spec_fields.items():
            if fname not in code_fields:
                field_mismatches.append({
                    'item': _item_label(spec_item),
                    'field': fname,
                    'issue': 'removed_from_code',
                    'spec_type': sf.type,
                    'code_type': None,
                })
            elif sf.type and code_fields[fname].type and sf.type != code_fields[fname].type:
                field_mismatches.append({
                    'item': _item_label(spec_item),
                    'field': fname,
                    'issue': 'type_changed',
                    'spec_type': sf.type,
                    'code_type': code_fields[fname].type,
                })

        for fname, cf in code_fields.items():
            if fname not in spec_fields:
                field_mismatches.append({
                    'item': _item_label(code_item),
                    'field': fname,
                    'issue': 'added_in_code',
                    'spec_type': None,
                    'code_type': cf.type,
                })

    return {
        'missing_in_code': missing_in_code,
        'extra_in_code': extra_in_code,
        'field_mismatches': field_mismatches,
    }


def _has_mismatches(report: dict) -> bool:
    return bool(
        report['missing_in_code'] or
        report['extra_in_code'] or
        report['field_mismatches']
    )


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def print_report(report: dict, spec: str, src: str, adapter: str) -> None:
    print(f"\nSpec ↔ Code Validator  adapter={adapter}")
    print(f"  spec : {spec}")
    print(f"  src  : {src}\n")

    if not _has_mismatches(report):
        print("  ✅  No mismatches — spec and code are in sync.\n")
        return

    if report['missing_in_code']:
        print("  ❌  Declared in spec, missing in code:")
        for label in report['missing_in_code']:
            print(f"       — {label}")

    if report['extra_in_code']:
        print("  ⚠️   In code, not declared in spec:")
        for label in report['extra_in_code']:
            print(f"       — {label}")

    if report['field_mismatches']:
        print("  ❌  Field mismatches:")
        for m in report['field_mismatches']:
            if m['issue'] == 'removed_from_code':
                print(f"       — {m['item']}.{m['field']}: "
                      f"spec={m['spec_type']!r}  →  not found in code")
            elif m['issue'] == 'type_changed':
                print(f"       — {m['item']}.{m['field']}: "
                      f"spec={m['spec_type']!r}  vs  code={m['code_type']!r}")
            elif m['issue'] == 'added_in_code':
                print(f"       — {m['item']}.{m['field']}: "
                      f"in code ({m['code_type']!r}) but not declared in spec")
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description='Validate that source code matches what the spec declares.',
    )
    parser.add_argument(
        '--project-type', choices=VALID_PROJECT_TYPES, metavar='TYPE',
        help=f"Project type ({', '.join(VALID_PROJECT_TYPES)})",
    )
    parser.add_argument(
        '--adapter', metavar='NAME',
        help=f"Framework adapter ({', '.join(ADAPTER_REGISTRY)})",
    )
    parser.add_argument(
        '--spec', metavar='PATH',
        help='Path to spec file (e.g. docs/specs/pipeline-contract.md)',
    )
    parser.add_argument(
        '--src', metavar='PATH',
        help='Path to source file or directory',
    )
    parser.add_argument(
        '--strict', action='store_true',
        help='Exit 1 if any mismatch is found',
    )
    parser.add_argument(
        '--json', action='store_true', dest='json_output',
        help='Output results as JSON',
    )
    parser.add_argument(
        '--dry-run', action='store_true',
        help='Run checks but never exit with a non-zero code',
    )
    args = parser.parse_args()

    # Graceful skip when not fully configured — pre-commit hook may call this
    # before the project has set up --adapter / --spec / --src.
    if not all([args.adapter, args.spec, args.src]):
        print(
            "⚠️   verify_spec_code: --adapter / --spec / --src not configured — skipping.\n"
            "    Pass all three flags (or configure via .project-starter.yml in a future phase).",
        )
        sys.exit(0)

    if not os.path.exists(args.spec):
        print(f"error: spec file not found: {args.spec}", file=sys.stderr)
        sys.exit(2)
    if not os.path.exists(args.src):
        print(f"error: src path not found: {args.src}", file=sys.stderr)
        sys.exit(2)

    adapter_obj = _load_adapter(args.adapter)
    spec_items = adapter_obj.extract_spec(args.spec)
    code_items = adapter_obj.extract_code(args.src)
    report = compare(spec_items, code_items)

    if args.json_output:
        print(json.dumps({
            'project_type': args.project_type,
            'adapter': args.adapter,
            'spec': args.spec,
            'src': args.src,
            **report,
        }, indent=2))
    else:
        print_report(report, args.spec, args.src, args.adapter)

    if args.strict and not args.dry_run and _has_mismatches(report):
        sys.exit(1)


if __name__ == '__main__':
    main()
