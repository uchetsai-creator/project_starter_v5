#!/usr/bin/env python3
"""
verify_spec_code.py — Spec ↔ code drift validator for project_starter_v5.

Phase 52.5 introduces a capability-based adapter layer:

  verify_spec_code.py
          │
          ▼
  Capability Adapter  (spec parsing + file discovery + detector orchestration)
          │
          ├── Framework Detector A
          └── Framework Detector B
                  │
                  ▼
          Normalized Representation → Validation Result

Compares what the spec declares against what the code implements. Capability
adapters translate both spec and code into NormalizedForm objects; the core
compares them. No framework-specific logic lives here.

Usage (capability adapters — new in Phase 52.5):
  python3 verify_spec_code.py --project-type data-pipeline --adapter data-pipeline \\
      --spec docs/specs/pipeline-contract.md --src src/stages/ --strict
  python3 verify_spec_code.py --adapter web-api \\
      --spec docs/specs/api-contract.md --src src/ --framework fastapi --strict

Usage (legacy framework names — still work identically):
  python3 verify_spec_code.py --project-type data-pipeline --adapter airflow \\
      --spec docs/specs/pipeline-contract.md --src src/stages/ --strict
  python3 verify_spec_code.py --project-type cli-tool --adapter click \\
      --spec docs/specs/cli-contract.md --src src/cli.py --strict

If --adapter / --spec / --src are not supplied (e.g. when called from the
pre-commit hook on an unconfigured project), the validator prints a warning
and exits 0 — it never blocks an unconfigured project.

Valid project types:
  web-app | cli-tool | library | data-pipeline | ml-pipeline |
  microservices | llm-app | iac | mobile-app

Capability adapters (Phase 52.5):
  data-pipeline   — Data Pipeline / ML Pipeline  (auto-detects: airflow, dagster, prefect)
  web-api         — Web App / Microservices       (auto-detects: fastapi, flask, express)
  cli             — CLI Tool                      (auto-detects: click)
  library         — Library / SDK                 (auto-detects: python_library)
  llm-app         — AI / LLM App                  (auto-detects: tool_schema)
  iac             — IaC / DevOps                  (auto-detects: terraform, pulumi)
  mobile          — Mobile App                    (auto-detects: react_native, flutter)

Legacy adapter names (Phase 45-47) — still work, now route through capability adapters:
  airflow         — Data Pipeline / ML Pipeline (Apache Airflow)
  click           — CLI Tool (Click)
  fastapi         — Web App / Microservices (FastAPI)
  flask           — Web App / Microservices (Flask)
  express         — Web App / Microservices (Express / Node.js)
  dagster         — Data Pipeline / ML Pipeline (Dagster)
  prefect         — Data Pipeline / ML Pipeline (Prefect)
  python_library  — Library / SDK (Python __all__ + type hints)
  tool_schema     — AI / LLM App (Python docstrings / OpenAI tool schema JSON)
  terraform       — IaC / DevOps (Terraform HCL)
  pulumi          — IaC / DevOps (Pulumi Python)
  react_native    — Mobile App (React Native TSX/JSX)
  flutter         — Mobile App (Flutter Dart)

Phase 48 — Semantic matching (opt-in, not a registered adapter):
  --semantic      Wrap the selected adapter with SemanticAdapter for LLM-assisted
                  field matching. Requires ANTHROPIC_API_KEY. Never use in automated
                  sequences (pre-commit, workflow-registry) — opt-in only.
"""

import argparse
import importlib
import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _registry import VALID_TYPES

# adapter_name → (module_filename, class_name, framework_hint | None)
# Phase 52.5: 3-tuple. framework_hint is passed to the capability adapter's
# __init__(framework=...) to restrict which detector(s) are run.
ADAPTER_REGISTRY: dict[str, tuple[str, str, str | None]] = {
    # Capability adapters (Phase 52.5) — primary interface
    'data-pipeline':  ('_capability_pipeline', 'DataPipelineAdapter', None),
    'web-api':        ('_capability_web_api',  'WebAPIAdapter',       None),
    'cli':            ('_capability_cli',      'CLIAdapter',          None),
    'library':        ('_capability_library',  'LibraryAdapter',      None),
    'llm-app':        ('_capability_llm',      'LLMAdapter',          None),
    'iac':            ('_capability_iac',       'IaCAdapter',          None),
    'mobile':         ('_capability_mobile',   'MobileAdapter',       None),
    # Legacy aliases (Phase 45-47) — route through capability adapters with framework hint
    'airflow':        ('_capability_pipeline', 'DataPipelineAdapter', 'airflow'),
    'dagster':        ('_capability_pipeline', 'DataPipelineAdapter', 'dagster'),
    'prefect':        ('_capability_pipeline', 'DataPipelineAdapter', 'prefect'),
    'fastapi':        ('_capability_web_api',  'WebAPIAdapter',       'fastapi'),
    'flask':          ('_capability_web_api',  'WebAPIAdapter',       'flask'),
    'express':        ('_capability_web_api',  'WebAPIAdapter',       'express'),
    'click':          ('_capability_cli',      'CLIAdapter',          'click'),
    'python_library': ('_capability_library',  'LibraryAdapter',      'python_library'),
    'tool_schema':    ('_capability_llm',      'LLMAdapter',          'tool_schema'),
    'terraform':      ('_capability_iac',       'IaCAdapter',          'terraform'),
    'pulumi':         ('_capability_iac',       'IaCAdapter',          'pulumi'),
    'react_native':   ('_capability_mobile',   'MobileAdapter',       'react_native'),
    'flutter':        ('_capability_mobile',   'MobileAdapter',       'flutter'),
}

_ADAPTER_DIR = Path(__file__).resolve().parent / '_spec_code_adapters'
sys.path.insert(0, str(_ADAPTER_DIR))


def _load_adapter(adapter_name: str, framework_hint: str | None = None):
    """
    Load a capability adapter by name and return an instantiated adapter object.

    Args:
        adapter_name:   Key into ADAPTER_REGISTRY (e.g. 'airflow', 'data-pipeline').
        framework_hint: Value of --framework CLI flag. Explicit --framework takes
                        precedence over the registry's built-in hint.

    Returns:
        Instantiated FrameworkAdapter subclass.
    """
    entry = ADAPTER_REGISTRY.get(adapter_name)
    if not entry:
        print(
            f"error: unknown adapter '{adapter_name}'. "
            f"Available: {', '.join(ADAPTER_REGISTRY)}",
            file=sys.stderr,
        )
        sys.exit(2)
    module_name, class_name, registry_hint = entry
    # Explicit --framework flag takes precedence over the registry's built-in hint
    effective_framework = framework_hint or registry_hint
    try:
        module = importlib.import_module(module_name)
        cls = getattr(module, class_name)
        # Pass framework hint if the adapter accepts it
        try:
            return cls(framework=effective_framework)
        except TypeError:
            return cls()
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
# Semantic output
# ---------------------------------------------------------------------------

_VERDICT_ICON = {
    'likely_same': '⚠️ ',
    'different':   '❌',
    'uncertain':   '❓',
}


def print_semantic_report(verdicts: list[dict]) -> None:
    if not verdicts:
        return
    print("  Semantic matching (LLM-assisted):")
    for v in verdicts:
        icon = _VERDICT_ICON.get(v['verdict'], '❓')
        print(
            f"       {icon} {v['item']}: "
            f"spec={v['spec_field']!r}:{v['spec_type']!r}  "
            f"vs  code={v['code_field']!r}:{v['code_type']!r}\n"
            f"           → {v['verdict']}: {v['reasoning']}"
        )
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description='Validate that source code matches what the spec declares.',
    )
    parser.add_argument(
        '--project-type', choices=VALID_TYPES, metavar='TYPE',
        help=f"Project type ({', '.join(VALID_TYPES)})",
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
    parser.add_argument(
        '--list-adapters', action='store_true',
        help='Print all registered adapter names and exit',
    )
    parser.add_argument(
        '--framework', metavar='NAME',
        help=(
            'Framework hint for explicit detector selection within a capability adapter '
            '(e.g. --adapter data-pipeline --framework airflow). '
            'Overrides the registry hint for legacy names.'
        ),
    )
    parser.add_argument(
        '--semantic', action='store_true',
        help=(
            'Wrap the selected adapter with SemanticAdapter for LLM-assisted field matching '
            '(requires ANTHROPIC_API_KEY; never use in automated sequences)'
        ),
    )
    args = parser.parse_args()

    if args.list_adapters:
        # Group by capability (module) for readability
        capability_adapters = {
            name: entry for name, entry in ADAPTER_REGISTRY.items()
            if entry[2] is None  # no built-in framework hint → primary capability
        }
        legacy_adapters = {
            name: entry for name, entry in ADAPTER_REGISTRY.items()
            if entry[2] is not None  # has built-in framework hint → legacy alias
        }
        print("Capability adapters (Phase 52.5):")
        for name in sorted(capability_adapters):
            module, cls, _ = ADAPTER_REGISTRY[name]
            print(f"  {name:<16}  {cls}  (module: {module})")
        print("\nLegacy framework aliases (route through capability adapters):")
        for name in sorted(legacy_adapters):
            module, cls, hint = ADAPTER_REGISTRY[name]
            print(f"  {name:<16}  {cls}  (framework: {hint})")
        sys.exit(0)

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

    adapter_obj = _load_adapter(args.adapter, framework_hint=getattr(args, 'framework', None))
    if args.semantic:
        from semantic import SemanticAdapter  # noqa: PLC0415
        adapter_obj = SemanticAdapter(wraps=adapter_obj)

    spec_items = adapter_obj.extract_spec(args.spec)
    code_items = adapter_obj.extract_code(args.src)
    report = compare(spec_items, code_items)

    semantic_verdicts: list[dict] = []
    if args.semantic and hasattr(adapter_obj, 'semantic_compare'):
        semantic_verdicts = adapter_obj.semantic_compare(report)

    if args.json_output:
        print(json.dumps({
            'project_type': args.project_type,
            'adapter': args.adapter,
            'spec': args.spec,
            'src': args.src,
            **report,
            'semantic_verdicts': semantic_verdicts,
        }, indent=2))
    else:
        print_report(report, args.spec, args.src, args.adapter)
        if semantic_verdicts:
            print_semantic_report(semantic_verdicts)

    if args.strict and args.dry_run:
        print(
            "warning: --strict is ignored when --dry-run is active; exit code will always be 0",
            file=sys.stderr,
        )
    if args.strict and not args.dry_run and _has_mismatches(report):
        sys.exit(1)


if __name__ == '__main__':
    main()
