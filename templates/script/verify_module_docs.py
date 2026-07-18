#!/usr/bin/env python3
"""
verify_module_docs.py — Module flow coverage & quality audit for project_starter_v4 projects.

Checks that every module has a flow file in docs/modules/ and that each flow file
has required sections filled, gated by module type × project type.

When --src is provided, cross-references against scan_codebase.py to detect undocumented
modules. Without --src, audits only existing flow files in docs/modules/.

Usage:
  python3 docs/script/verify_module_docs.py --project-type TYPE
  python3 docs/script/verify_module_docs.py --project-type TYPE --src PATH --docs PATH
  python3 docs/script/verify_module_docs.py --project-type TYPE --strict
  python3 docs/script/verify_module_docs.py --project-type TYPE --json

Valid project types: web-app | cli-tool | library | data-pipeline | ml-pipeline |
                     microservices | llm-app | iac | mobile-app
Hybrid types use +: data-pipeline+web-app
"""

import argparse
import json
import os
import re
import subprocess
import sys

VALID_TYPES = [
    'web-app', 'cli-tool', 'library',
    'data-pipeline', 'ml-pipeline', 'microservices', 'llm-app', 'iac', 'mobile-app',
]

MODULE_TYPES = ['Pipeline Stage', 'Feature', 'Background Job', 'Shared Utility']

# Primary module type expected per project type (informational — used in summary hint)
PRIMARY_MODULE_TYPE = {
    'web-app':       'Feature',
    'cli-tool':      'Feature',
    'library':       'Shared Utility',
    'data-pipeline': 'Pipeline Stage',
    'ml-pipeline':   'Pipeline Stage',
    'microservices': 'Feature',
    'llm-app':       'Feature',
    'iac':           'Feature',
    'mobile-app':    'Feature',
}

MIN_EH_LINES = 3   # minimum non-blank lines required in an Error Handling section

# Placeholder patterns shared across module types
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _verify_common import _is_placeholder


def _read_file(path: str) -> list[str] | None:
    try:
        with open(path, encoding='utf-8') as fh:
            return fh.read().splitlines()
    except OSError:
        return None


def _non_blank(lines: list[str]) -> list[str]:
    return [ln for ln in lines if ln.strip()]


# ---------------------------------------------------------------------------
# Module type detection
# ---------------------------------------------------------------------------

def detect_module_type(lines: list[str]) -> str | None:
    """Extract module type from the file header (first 30 lines).

    Supports both canonical form ('Module type: X') and common variant ('**Type:** X').
    """
    for line in lines[:30]:
        m = re.search(r'(?:Module\s+type|(?:\*{0,2}Type\*{0,2}))\s*[:：]\s*(.+)', line, re.IGNORECASE)
        if m:
            raw = m.group(1).strip().rstrip('.')
            for mt in MODULE_TYPES:
                if mt.lower() in raw.lower():
                    return mt
    return None


# ---------------------------------------------------------------------------
# Quality checks per module type
# ---------------------------------------------------------------------------

def check_pipeline_stage(lines: list[str]) -> list[str]:
    """Quality check for Pipeline Stage flow files. Returns list of issues."""
    issues: list[str] = []
    text = '\n'.join(lines)

    # Input block — look for Source:, Format:, and Schema:/Naming:
    input_m = re.search(r'(?m)^Input\s*:', text)
    if not input_m:
        issues.append("Missing Input contract block")
    else:
        # Grab text from Input: until the next arrow or Output:
        input_end = re.search(r'(?m)^(Output\s*:|↓)', text[input_m.end():])
        block = text[input_m.end(): input_m.end() + input_end.start()] if input_end else text[input_m.end():]
        for field in ('Source', 'Format'):
            fm = re.search(rf'(?m)^\s*{field}\s*:\s*(.+)', block)
            if not fm or not fm.group(1).strip() or _is_placeholder(fm.group(1)):
                issues.append(f"Input contract: {field} empty or placeholder")
        if not re.search(r'(?m)^\s*(Schema|Naming)\s*:\s*\S', block):
            issues.append("Input contract: Schema/Naming missing")

    # Output block — look for Destination: and Format:
    output_m = re.search(r'(?m)^Output\s*:', text)
    if not output_m:
        issues.append("Missing Output contract block")
    else:
        output_end = re.search(r'(?m)^(Error Handling|##)', text[output_m.end():])
        block = text[output_m.end(): output_m.end() + output_end.start()] if output_end else text[output_m.end():]
        for field in ('Destination', 'Format'):
            fm = re.search(rf'(?m)^\s*{field}\s*:\s*(.+)', block)
            if not fm or not fm.group(1).strip() or _is_placeholder(fm.group(1)):
                issues.append(f"Output contract: {field} empty or placeholder")

    # Error Handling section
    eh_m = re.search(r'(?m)^Error Handling\s*:', text)
    if not eh_m:
        issues.append("Error Handling section missing")
    else:
        eh_end = re.search(r'(?m)^(##\s|\Z)', text[eh_m.end():])
        eh_text = text[eh_m.end(): eh_m.end() + eh_end.start()] if eh_end else text[eh_m.end():]
        eh_lines = _non_blank(eh_text.splitlines())
        if not re.search(r'\btransient\b', eh_text, re.IGNORECASE):
            issues.append("Error Handling: transient failure case missing")
        if not re.search(r'missing.?input|input.?missing', eh_text, re.IGNORECASE):
            issues.append("Error Handling: missing-input case missing")
        if len(eh_lines) < MIN_EH_LINES:
            issues.append(f"Error Handling < {MIN_EH_LINES} lines (found {len(eh_lines)})")

    return issues


def check_feature(lines: list[str]) -> list[str]:
    """Quality check for Feature module flow files. Returns list of issues."""
    issues: list[str] = []
    text = '\n'.join(lines)

    func_vals = re.findall(r'Function\s*:\s*(.+)', text)
    file_vals = re.findall(r'File\s*:\s*(.+)', text)

    real_funcs = [v for v in func_vals if v.strip() and not _is_placeholder(v)]
    real_files = [v for v in file_vals if v.strip() and not _is_placeholder(v)]

    if not real_funcs:
        if re.search(r'Not Supported', text, re.IGNORECASE):
            pass  # all operations explicitly marked Not Supported — acceptable
        else:
            issues.append("No real Function: values (all placeholder or missing)")
    if not real_files:
        if not real_funcs:
            pass  # already reported above
        else:
            issues.append("No real File: values (all placeholder or missing)")

    return issues


def check_background_job(lines: list[str]) -> list[str]:
    """Quality check for Background Job flow files. Returns list of issues."""
    issues: list[str] = []
    text = '\n'.join(lines)

    # Trigger line
    trig_m = re.search(r'Trigger\s*:\s*(.+)', text)
    if not trig_m or not trig_m.group(1).strip() or _is_placeholder(trig_m.group(1)):
        issues.append("Trigger: line missing or placeholder")

    # Success path
    if not re.search(r'→\s*(acknowledge|commit)|[Oo]n\s+success', text):
        issues.append("Success path (→ acknowledge / → commit / On success) not documented")

    # Error Handling section
    eh_m = re.search(r'(?m)^Error Handling\s*:', text)
    if not eh_m:
        issues.append("Error Handling section missing")
    else:
        eh_end = re.search(r'(?m)^(##\s|\Z)', text[eh_m.end():])
        eh_text = text[eh_m.end(): eh_m.end() + eh_end.start()] if eh_end else text[eh_m.end():]
        eh_lines = _non_blank(eh_text.splitlines())
        if not re.search(r'\btransient\b', eh_text, re.IGNORECASE):
            issues.append("Error Handling: transient failure case missing")
        if not re.search(r'\bpermanent\b', eh_text, re.IGNORECASE):
            issues.append("Error Handling: permanent failure case missing")
        if len(eh_lines) < MIN_EH_LINES:
            issues.append(f"Error Handling < {MIN_EH_LINES} lines (found {len(eh_lines)})")

    return issues


def check_shared_utility(lines: list[str]) -> list[str]:
    """Quality check for Shared Utility flow files. Returns list of issues."""
    issues: list[str] = []
    text = '\n'.join(lines)

    # plantuml class block
    uml_m = re.search(r'@startuml(.+?)@enduml', text, re.DOTALL)
    if not uml_m:
        issues.append("plantuml class block missing (@startuml / @enduml not found)")
    else:
        block = uml_m.group(1)
        if 'class ' not in block:
            issues.append("plantuml block: no class declaration found")
        else:
            method_lines = [ln for ln in block.splitlines()
                            if re.match(r'\s*[+\-#~]\s*\S', ln)]
            real_methods = [ln for ln in method_lines if not _is_placeholder(ln)]
            if not real_methods:
                issues.append("plantuml class: no real method signatures (all placeholder)")

    # Used by table
    used_m = re.search(r'\*\*Used by\*\*|^Used by\s*:', text, re.MULTILINE | re.IGNORECASE)
    if not used_m:
        issues.append("'Used by' section missing")
    else:
        after = text[used_m.end():]
        # Collect table data rows (skip header and separator rows)
        rows = re.findall(r'^\|\s*([^|\n]+?)\s*\|\s*([^|\n]+?)\s*\|', after, re.MULTILINE)
        real_rows = [
            r for r in rows
            if r[0].strip() not in ('Module', '---', ':---', ':-')
            and not _is_placeholder(r[0])
            and r[0].strip()
            and not re.match(r'^[-:]+$', r[0].strip())
        ]
        if not real_rows:
            issues.append("'Used by' table has no real rows (placeholder or header only)")

    return issues


def check_quality(lines: list[str], module_type: str) -> tuple[str, list[str]]:
    """Return (status, issues). status: 'pass' | 'fail' | 'unknown'."""
    if module_type == 'Pipeline Stage':
        issues = check_pipeline_stage(lines)
    elif module_type == 'Feature':
        issues = check_feature(lines)
    elif module_type == 'Background Job':
        issues = check_background_job(lines)
    elif module_type == 'Shared Utility':
        issues = check_shared_utility(lines)
    else:
        return ('unknown', [f"Unrecognized module type '{module_type}'"])
    return ('pass' if not issues else 'fail', issues)


# ---------------------------------------------------------------------------
# Module discovery
# ---------------------------------------------------------------------------

def _find_scan_script(script_dir: str, docs_dir: str) -> str | None:
    for candidate in (
        os.path.join(script_dir, 'scan_codebase.py'),
        os.path.join(docs_dir, 'script', 'scan_codebase.py'),
    ):
        if os.path.isfile(candidate):
            return candidate
    return None


def scan_modules_from_src(
    src: str, project_type: str, docs_dir: str, script_dir: str,
) -> list[dict] | None:
    """Invoke scan_codebase.py --format json; return non-shared module list or None."""
    scan_script = _find_scan_script(script_dir, docs_dir)
    if not scan_script:
        print("  ⚠️  scan_codebase.py not found — skipping coverage check", file=sys.stderr)
        return None
    try:
        result = subprocess.run(
            [sys.executable, scan_script, src,
             '--project-type', project_type, '--format', 'json',
             '--docs', docs_dir],
            capture_output=True, text=True, timeout=30,
        )
        if result.returncode != 0:
            print(
                f"  ⚠️  scan_codebase.py error (exit {result.returncode}): "
                f"{result.stderr.strip()[:200]}",
                file=sys.stderr,
            )
            return None
        data = json.loads(result.stdout)
        return [m for m in data.get('modules', []) if m.get('status') != '—']
    except (json.JSONDecodeError, subprocess.TimeoutExpired, OSError) as exc:
        print(f"  ⚠️  scan_codebase.py call failed: {exc}", file=sys.stderr)
        return None


def find_docs_modules(docs_dir: str) -> list[dict]:
    """Return [{name, flow_file_path}] for all subdirs under docs/modules/."""
    modules_root = os.path.join(docs_dir, 'modules')
    results: list[dict] = []
    if not os.path.isdir(modules_root):
        return results
    for entry in sorted(os.scandir(modules_root), key=lambda e: e.name):
        if not entry.is_dir():
            continue
        flow_path = os.path.join(entry.path, f'{entry.name}-module-data-flow.md')
        results.append({
            'name': entry.name,
            'flow_file_path': flow_path if os.path.isfile(flow_path) else None,
        })
    return results


# ---------------------------------------------------------------------------
# Core audit
# ---------------------------------------------------------------------------

def audit(project_type: str, docs_dir: str, src: str | None, script_dir: str) -> list[dict]:
    """Build per-module result list. Each entry: {name, scan_type, flow_present, module_type,
    quality, issues, flow_file_path}."""
    results: list[dict] = []

    if src:
        # Coverage mode: use scan_codebase.py to get full module list
        scan_modules = scan_modules_from_src(src, project_type, docs_dir, script_dir)
        if scan_modules is None:
            scan_modules = []

        # Build a lookup from docs/modules/
        docs_mods = {m['name']: m['flow_file_path'] for m in find_docs_modules(docs_dir)}

        for sm in scan_modules:
            name = sm['name']
            # scan_codebase type may be 'Pipeline Stage (detected)', 'Feature', etc.
            scan_type = sm.get('type', '')
            flow_path = docs_mods.get(name)
            if flow_path is None:
                # Check by flow_file field from scan output
                scan_flow = sm.get('flow_file')
                if scan_flow and os.path.isfile(scan_flow):
                    flow_path = scan_flow

            if not flow_path:
                results.append({
                    'name': name,
                    'scan_type': scan_type,
                    'flow_present': False,
                    'module_type': None,
                    'quality': None,
                    'issues': [],
                    'flow_file_path': None,
                })
                continue

            lines = _read_file(flow_path) or []
            module_type = detect_module_type(lines)
            quality, issues = check_quality(lines, module_type or '')
            results.append({
                'name': name,
                'scan_type': scan_type,
                'flow_present': True,
                'module_type': module_type,
                'quality': quality,
                'issues': issues,
                'flow_file_path': flow_path,
            })
    else:
        # Quality-only mode: audit whatever exists in docs/modules/
        for m in find_docs_modules(docs_dir):
            name = m['name']
            flow_path = m['flow_file_path']
            if not flow_path:
                # Directory exists but no flow file
                results.append({
                    'name': name,
                    'scan_type': '',
                    'flow_present': False,
                    'module_type': None,
                    'quality': None,
                    'issues': [],
                    'flow_file_path': None,
                })
                continue
            lines = _read_file(flow_path) or []
            module_type = detect_module_type(lines)
            quality, issues = check_quality(lines, module_type or '')
            results.append({
                'name': name,
                'scan_type': '',
                'flow_present': True,
                'module_type': module_type,
                'quality': quality,
                'issues': issues,
                'flow_file_path': flow_path,
            })

    return results


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def _type_label(module_type: str | None, scan_type: str) -> str:
    if module_type:
        return module_type
    if scan_type:
        # Normalize scan_codebase labels: 'Pipeline Stage (detected)' → 'Pipeline Stage'
        for mt in MODULE_TYPES:
            if mt.lower() in scan_type.lower():
                return mt
        return scan_type
    return 'Unknown'


def print_results(results: list[dict], project_type: str, src: str | None) -> None:
    SEP = '─' * 70
    print(f"\nModule Flow Coverage & Quality — {project_type}")
    print(SEP)
    print(f"{'Module':<28} {'Type':<18} {'Flow file':<14} Quality")
    print(SEP)

    for r in results:
        name = r['name'][:26]
        type_lbl = _type_label(r['module_type'], r['scan_type'])[:16]
        if not r['flow_present']:
            flow_col = '❌ Missing'
            quality_col = '—'
        else:
            flow_col = '✅ Present'
            if r['quality'] == 'pass':
                quality_col = '✅  Fully filled'
            elif r['quality'] == 'unknown':
                quality_col = f"⚠️  Unknown type — {r['issues'][0] if r['issues'] else ''}"
            else:
                # Show first issue inline; rest on following lines
                first = r['issues'][0] if r['issues'] else 'issues found'
                quality_col = f"⚠️  {first}"

        print(f"{name:<28} {type_lbl:<18} {flow_col:<14} {quality_col}")

        # Additional issues on continuation lines
        for issue in (r['issues'][1:] if r['flow_present'] and r['quality'] == 'fail' else []):
            print(f"{'':28} {'':18} {'':14} ⚠️  {issue}")

    print()

    # Summary
    total = len(results)
    present = sum(1 for r in results if r['flow_present'])
    fully_filled = sum(1 for r in results if r['flow_present'] and r['quality'] == 'pass')

    if src:
        print(f"Coverage : {present} / {total} modules documented")
    print(f"Quality  : {fully_filled} / {present} existing flow files fully filled")
    print()


def print_results_json(results: list[dict], project_type: str, docs_dir: str, src: str | None) -> None:
    total = len(results)
    present = sum(1 for r in results if r['flow_present'])
    fully_filled = sum(1 for r in results if r['flow_present'] and r['quality'] == 'pass')

    payload = {
        'project_type': project_type,
        'docs_dir': docs_dir,
        'src_dir': src,
        'modules': [
            {
                'name': r['name'],
                'detected_type': r['scan_type'],
                'module_type': r['module_type'],
                'flow_file_present': r['flow_present'],
                'flow_file_path': r['flow_file_path'],
                'quality': r['quality'],
                'issues': r['issues'],
            }
            for r in results
        ],
        'summary': {
            'total_modules': total,
            'documented': present,
            'quality_pass': fully_filled,
        },
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_types(raw: str) -> list[str]:
    parts = [p.strip() for p in raw.split('+')]
    for p in parts:
        if p not in VALID_TYPES:
            print(f"error: unknown project type '{p}'. Valid: {', '.join(VALID_TYPES)}", file=sys.stderr)
            sys.exit(2)
    return parts


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit module flow file coverage and quality for project_starter_v4 projects.",
    )
    parser.add_argument(
        '--project-type', required=True, metavar='TYPE',
        help=f"Project type. Valid: {', '.join(VALID_TYPES)}. Hybrid: TYPE+TYPE",
    )
    parser.add_argument('--src', default=None, metavar='PATH',
                        help='Source directory to cross-reference via scan_codebase.py')
    parser.add_argument('--docs', default='docs', metavar='PATH',
                        help='Path to docs directory (default: docs)')
    parser.add_argument('--strict', action='store_true',
                        help='Exit 1 if any check fails')
    parser.add_argument('--json', action='store_true', dest='json_output',
                        help='Output results as JSON')
    args = parser.parse_args()

    project_types = parse_types(args.project_type)
    primary_type = project_types[0]

    script_dir = os.path.dirname(os.path.abspath(__file__))
    docs_dir = args.docs

    if not os.path.isdir(docs_dir):
        print(f"error: docs directory not found: {docs_dir}", file=sys.stderr)
        sys.exit(2)

    results = audit(primary_type, docs_dir, args.src, script_dir)

    if not results:
        msg = "No modules found"
        msg += f" in {docs_dir}/modules/" if not args.src else f" via scan_codebase.py ({args.src})"
        if args.json_output:
            print(json.dumps({'project_type': primary_type, 'modules': [], 'message': msg}))
        else:
            print(f"⚠️  {msg}")
        sys.exit(0)

    if args.json_output:
        print_results_json(results, primary_type, docs_dir, args.src)
    else:
        print_results(results, primary_type, args.src)

    if args.strict:
        has_failure = any(
            not r['flow_present'] or r['quality'] == 'fail'
            for r in results
        )
        if has_failure:
            sys.exit(1)


if __name__ == '__main__':
    main()
