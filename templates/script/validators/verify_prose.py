#!/usr/bin/env python3
"""
verify_prose.py — prose-quality wrapper for project_starter_v5, using Vale (vale.sh).

verify_docs.py / verify_content.py check *fill quality*: is a section a placeholder,
does a table have real rows. Neither can tell a well-written sentence from an empty
one — "This is obviously very simple to set up" passes every existing check exactly as
well as a sentence that actually explains something, and a bare "TBD" or "coming soon"
written as prose (not `[TBD]` or `<!-- TODO -->`) passes _verify_common.py's placeholder
regex entirely. This validator is the layer above that: it runs Vale against every .md
file under --docs using a small custom style shipped in _prose_style/ (see that
directory's .vale.ini — no `vale sync` / external style package, no network dependency,
consistent with this framework's offline-friendly design elsewhere).

Custom rules shipped (styles/Custom/*.yml — extend this, don't hand-edit generated output):
  WeaselWords                 — vague qualifiers (very, obviously, simply, just, ...)
  NaturalLanguagePlaceholders — TBD / coming soon / TODO written as prose, not brackets

This is a separate, independent gate from verify_docs.py / verify_content.py — it does
not replace their placeholder-fill checks, and it is not a general writing-quality
grader. It is not a general security/spec check either — see README.md -> Prose Quality
(Vale) for exact scope.

Prerequisites: install Vale — https://vale.sh/docs/install (Homebrew / Scoop / a
prebuilt binary from GitHub releases; not a pip/npm package).

Usage:
  python3 verify_prose.py --docs docs/ --strict
  python3 verify_prose.py --docs docs/ --json
  python3 verify_prose.py --docs docs/ --min-severity high --strict
  python3 verify_prose.py --list-tools

If --docs is not supplied (e.g. called from the pre-commit hook on a project that
hasn't enabled prose_scan_enabled), the validator prints a warning and exits 0 — it
never blocks an unconfigured project.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _verify_common import _SKIP_DIRNAMES, _append_telemetry, _telemetry_ts

_STYLE_DIR = Path(__file__).resolve().parent / '_prose_style'
_VALE_CONFIG = _STYLE_DIR / '.vale.ini'

_SEVERITY_RANK = {'low': 0, 'medium': 1, 'high': 2}
_VALE_SEVERITY = {'suggestion': 'low', 'warning': 'medium', 'error': 'high'}


def _which(tool: str) -> str | None:
    return shutil.which(tool)


def _find_md_files(docs: str) -> list[str]:
    if os.path.isfile(docs):
        return [docs] if docs.lower().endswith('.md') else []
    found: list[str] = []
    for root, dirs, files in os.walk(docs):
        dirs[:] = [d for d in dirs if d not in _SKIP_DIRNAMES and not d.startswith('.')]
        for f in files:
            if f.lower().endswith('.md'):
                found.append(os.path.join(root, f))
    return found


def _run_vale(files: list[str]) -> tuple[str, str, int]:
    """Run vale against an explicit file list, using this framework's shipped
    self-contained style (no vale sync / external package needed)."""
    proc = subprocess.run(
        ['vale', '--config', str(_VALE_CONFIG), '--output=JSON', *files],
        capture_output=True, text=True, encoding='utf-8', errors='replace',
    )
    return proc.stdout, proc.stderr, proc.returncode


def _parse_vale_json(raw: str) -> list[dict]:
    if not raw or not raw.strip():
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []
    findings = []
    for file_path, alerts in data.items():
        for a in alerts:
            findings.append({
                'tool': 'vale',
                'file': file_path,
                'line': a.get('Line', 0),
                'severity': _VALE_SEVERITY.get(str(a.get('Severity', '')).lower(), 'low'),
                'rule': a.get('Check', ''),
                'message': (a.get('Message') or '').strip(),
            })
    return findings


# ---------------------------------------------------------------------------
# Scan orchestration
# ---------------------------------------------------------------------------

def run_scan(docs: str, min_severity: str = 'medium') -> dict:
    """Run Vale against every .md file under docs.

    Returns:
      { docs, tools_run, tools_skipped, findings, blocking_findings, passed }
    tools_skipped mirrors verify_security.py's shape: an empty findings list only
    means "clean" when Vale actually ran — a missing install is reported explicitly,
    not silently treated as a pass.
    """
    md_files = _find_md_files(docs)

    findings: list[dict] = []
    tools_run: list[str] = []
    tools_skipped: list[dict] = []

    if md_files:
        if _which('vale'):
            raw, err, rc = _run_vale(md_files)
            if rc not in (0, 1):
                tools_skipped.append({
                    'tool': 'vale', 'language': 'markdown', 'files': len(md_files),
                    'reason': f"vale exited with code {rc} — {(err or '').strip()[:200] or 'no stderr output'}",
                })
            else:
                findings += _parse_vale_json(raw)
                tools_run.append('vale')
        else:
            tools_skipped.append({
                'tool': 'vale', 'language': 'markdown', 'files': len(md_files),
                'reason': 'vale not installed — see https://vale.sh/docs/install',
            })

    threshold = _SEVERITY_RANK.get(min_severity, 1)
    blocking = [f for f in findings if _SEVERITY_RANK.get(f['severity'], 0) >= threshold]

    return {
        'docs': docs,
        'tools_run': tools_run,
        'tools_skipped': tools_skipped,
        'findings': findings,
        'blocking_findings': len(blocking),
        'passed': len(blocking) == 0,
    }


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def print_report(result: dict, min_severity: str) -> None:
    print(f"\nProse Quality (Vale)  docs={result['docs']}")
    if result['tools_run']:
        print(f"  tools run: {', '.join(result['tools_run'])}")
    for skip in result['tools_skipped']:
        print(
            f"  [WARN] {skip['tool']} skipped ({skip['language']}, "
            f"{skip['files']} file(s) found): {skip['reason']}"
        )

    if not result['findings']:
        if not result['tools_run'] and not result['tools_skipped']:
            print("  [OK]  No .md files found under --docs — nothing to scan.\n")
        elif not result['tools_skipped']:
            print("  [OK]  No findings.\n")
        else:
            print(
                "  [OK]  No findings from the tool(s) that did run — but see [WARN] above: "
                "coverage is incomplete, this is not a confirmed clean scan.\n"
            )
        return

    by_sev: dict[str, list[dict]] = {'high': [], 'medium': [], 'low': []}
    for f in result['findings']:
        by_sev.setdefault(f['severity'], []).append(f)

    threshold = _SEVERITY_RANK.get(min_severity, 1)
    for sev in ('high', 'medium', 'low'):
        items = by_sev.get(sev, [])
        if not items:
            continue
        tag = '[FAIL]' if _SEVERITY_RANK[sev] >= threshold else '[INFO]'
        print(f"  {tag}  {sev.upper()} ({len(items)}):")
        for f in items:
            print(f"       — {f['file']}:{f['line']}  [{f['rule']}]  {f['message']}")
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[union-attr]  # guard above only narrows sys.stdout

    parser = argparse.ArgumentParser(
        description='verify_prose.py — prose-quality wrapper (Vale)',
    )
    parser.add_argument('--docs', metavar='PATH', help='Path to docs directory or a single .md file')
    parser.add_argument(
        '--project-type', metavar='TYPE',
        help='Project type, used only to label the telemetry row (this check is not type-gated)',
    )
    parser.add_argument(
        '--min-severity', choices=['low', 'medium', 'high'], default='medium',
        help='Minimum severity that counts toward --strict (default: medium)',
    )
    parser.add_argument(
        '--strict', action='store_true',
        help='Exit 1 if any finding at or above --min-severity is found',
    )
    parser.add_argument(
        '--json', action='store_true', dest='json_output',
        help='Output results as JSON',
    )
    parser.add_argument(
        '--list-tools', action='store_true',
        help='Print whether Vale is installed and exit',
    )
    args = parser.parse_args()

    if args.list_tools:
        found = _which('vale')
        status = f'found at {found}' if found else 'NOT installed'
        print(f"  {'vale':<8} (Markdown): {status}")
        sys.exit(0)

    if not args.docs:
        print(
            "[WARN] verify_prose: --docs not configured — skipping.\n"
            "    This project has no prose-quality scanning until this is set. Set\n"
            "    prose_scan_enabled: true in .project-starter.yml (the pre-commit hook reads\n"
            "    it automatically and passes docs_path — no need to pass --docs by hand), or\n"
            "    pass --docs directly. See README.md -> Prose Quality (Vale).",
        )
        sys.exit(0)

    if not os.path.exists(args.docs):
        print(f"error: docs path not found: {args.docs}", file=sys.stderr)
        sys.exit(2)

    result = run_scan(args.docs, args.min_severity)

    if args.json_output:
        print(json.dumps(result, indent=2))
    else:
        print_report(result, args.min_severity)

    ts = _telemetry_ts()
    status = 'pass' if result['passed'] else 'fail'
    _append_telemetry('verify_prose', args.project_type or '', status, ts)

    if args.strict and not result['passed']:
        sys.exit(1)


if __name__ == '__main__':
    main()
