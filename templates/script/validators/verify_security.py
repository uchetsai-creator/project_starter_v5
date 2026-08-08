#!/usr/bin/env python3
"""
verify_security.py — SAST wrapper for project_starter_v5.

Runs existing static-analysis security tools against --src and reports findings in the
same style as the other verify_*.py validators:
  - bandit                     — Python
  - eslint-plugin-security     — JS/TS
  - Semgrep                    — Go, Ruby, Java, PHP, Kotlin, Vue — the exact language
    gap the Spec <-> Code Validator's Limitations section names as having zero drift
    detector coverage. Semgrep is NOT run against Python/JS/TS files — bandit and
    eslint-plugin-security already cover those, and overlapping the same files through
    a second tool would just duplicate findings under different check IDs.

This is a separate, independent gate from verify_spec_code.py. It does not extend that
validator's shape-only spec<->code comparison (see README.md -> Limitations) — it looks
at code alone, with no spec input, for a fixed set of known-unsafe patterns each
underlying tool already recognizes (eval, shell=True, unsafe regex, object injection,
hardcoded secrets, etc.). It is not a general security audit: coverage is limited to
what each tool's rule set catches — see README.md -> Security Scan (SAST) for the exact
scope.

Prerequisites (only needed for the languages actually present in --src):
  Python:                 pip install bandit
  JS/TS:                  npm install --save-dev eslint eslint-plugin-security
  Go/Ruby/Java/PHP/Kotlin/Vue:  pip install semgrep

If a language's files are found under --src but its tool isn't installed,
this prints an explicit [WARN] rather than silently reporting a clean scan —
same philosophy as verify_spec_code.py's zero-coverage warning: an empty
findings list only means "clean" when the tool that would have found
something actually ran.

Usage:
  python3 verify_security.py --src src/ --project-type web-app --strict
  python3 verify_security.py --src src/ --json
  python3 verify_security.py --src src/ --min-severity high --strict
  python3 verify_security.py --list-tools

If --src is not supplied (e.g. called from the pre-commit hook on a project
that hasn't set security_scan_src), the validator prints a warning and exits
0 — it never blocks an unconfigured project.
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
from _verify_common import _append_telemetry, _telemetry_ts, _SKIP_DIRNAMES

_PY_EXT = {'.py'}
_JS_EXT = {'.js', '.jsx', '.ts', '.tsx'}
# Languages with zero spec<->code drift detector coverage per README.md -> Limitations
# ("Rails, Spring Boot, native Android/Kotlin, Vue, Go, PHP... has no automated drift
# detection at all") — routed to Semgrep instead of bandit/eslint, which don't parse them.
_SEMGREP_EXT = {'.go', '.rb', '.java', '.php', '.kt', '.kts', '.vue'}

_SEVERITY_RANK = {'low': 0, 'medium': 1, 'high': 2}

_BANDIT_SEVERITY = {'LOW': 'low', 'MEDIUM': 'medium', 'HIGH': 'high'}

# eslint-plugin-security's `recommended` config assigns "warn" (severity 1) to
# nearly every rule — there is no finer-grained severity signal to read from
# the tool itself, so severity 2 (error) maps to high and 1 (warn) to medium.
# This is a documented heuristic, not a property of the underlying rule.
#
# Flat config (eslint.config.cjs), not the legacy .eslintrc.json format — confirmed by
# actually running this against a real eslint install (not assumed): ESLint 9+ removed
# --no-eslintrc / -c <legacy .json> entirely ("Invalid option '--eslintrc'"). CJS (not a
# plain object dumped to .json) because eslint-plugin-security's own `configs.recommended`
# export must be spread in via a real `require()` call — it is not itself valid JSON (it
# self-references `plugins.security.configs`, which JSON can't represent).
_ESLINT_FLAT_CONFIG_TEMPLATE = """\
const security = require('eslint-plugin-security');
module.exports = [
  {{
    files: {file_globs},
    ...security.configs.recommended,
  }},
];
"""
_ESLINT_FILE_GLOBS = ['**/*.js', '**/*.jsx', '**/*.ts', '**/*.tsx']


# ---------------------------------------------------------------------------
# File discovery
# ---------------------------------------------------------------------------

def _find_files(src: str, exts: set[str]) -> list[str]:
    """Return files under src whose extension is in exts, skipping build/vendor dirs."""
    if os.path.isfile(src):
        return [src] if Path(src).suffix.lower() in exts else []
    found: list[str] = []
    for root, dirs, files in os.walk(src):
        dirs[:] = [d for d in dirs if d not in _SKIP_DIRNAMES and not d.startswith('.')]
        for f in files:
            if Path(f).suffix.lower() in exts:
                found.append(os.path.join(root, f))
    return found


def _which(tool: str) -> str | None:
    return shutil.which(tool)


# ---------------------------------------------------------------------------
# bandit (Python)
# ---------------------------------------------------------------------------

def _run_bandit(exe: str, src: str) -> tuple[str, str, int]:
    """Run bandit -r <src> -f json. bandit exits 1 when it finds issues — that
    is not a tool failure, stdout still holds valid JSON in that case.

    `exe` must be the fully-resolved path from _which(), not the bare 'bandit'
    string — see _run_eslint()'s docstring for why this matters on Windows."""
    proc = subprocess.run(
        [exe, '-r', src, '-f', 'json', '-q'],
        capture_output=True, text=True, encoding='utf-8', errors='replace',
    )
    return proc.stdout, proc.stderr, proc.returncode


def _parse_bandit_json(raw: str) -> list[dict]:
    if not raw or not raw.strip():
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []
    findings = []
    for r in data.get('results', []):
        findings.append({
            'tool': 'bandit',
            'file': r.get('filename', ''),
            'line': r.get('line_number', 0),
            'severity': _BANDIT_SEVERITY.get(str(r.get('issue_severity', '')).upper(), 'low'),
            'rule': r.get('test_id', ''),
            'message': (r.get('issue_text') or '').strip(),
        })
    return findings


# ---------------------------------------------------------------------------
# eslint-plugin-security (JS/TS)
# ---------------------------------------------------------------------------

def _run_eslint(exe: str, src: str) -> tuple[str, str, int]:
    """Run eslint against src with a throwaway config enabling only the
    security plugin's recommended rules — isolated from whatever eslint
    config the target project already has, so this never picks up
    unrelated style rules.

    `exe` must be the fully-resolved path from _which('eslint'), never the bare
    'eslint' string — confirmed as a real bug during development: npm installs
    eslint on Windows as eslint.CMD/eslint.ps1 shims (plus an extension-less
    POSIX shell script for other platforms), and subprocess.run(['eslint', ...])
    without shell=True cannot execute those — Windows CreateProcess needs the
    concrete resolved path (with its real extension), which is exactly what
    shutil.which() (used by _which()) already resolves via PATHEXT. bandit and
    semgrep happen to avoid this because pip packages console-script entry
    points as real .exe files on Windows; eslint's npm-style shim does not.

    The generated eslint.config.cjs is written into the current working directory
    (not an OS temp dir) and cleaned up afterward — confirmed necessary by actually
    running this: Node's require('eslint-plugin-security') resolves relative to the
    config file's own location by walking up through its ancestor directories'
    node_modules/, so a config file living in an unrelated OS temp directory cannot
    find a plugin installed under the target project's node_modules/ no matter how
    that plugin was installed (locally or globally) — it must live somewhere in the
    project's own directory tree. This framework already assumes cwd == project
    root everywhere else (e.g. _append_telemetry's Path('.ai') / 'telemetry'), so
    writing here is consistent with every other relative path in this codebase, not
    a new assumption introduced just for this function."""
    cfg_path = os.path.join(
        os.getcwd(), f'.eslint-security-{os.getpid()}.config.cjs',
    )
    try:
        with open(cfg_path, 'w', encoding='utf-8') as fh:
            fh.write(_ESLINT_FLAT_CONFIG_TEMPLATE.format(file_globs=_ESLINT_FILE_GLOBS))
        proc = subprocess.run(
            [exe, '--no-config-lookup', '--config', cfg_path, '-f', 'json', src],
            capture_output=True, text=True, encoding='utf-8', errors='replace',
        )
        return proc.stdout, proc.stderr, proc.returncode
    finally:
        try:
            os.remove(cfg_path)
        except OSError:
            pass


def _parse_eslint_json(raw: str) -> list[dict]:
    if not raw or not raw.strip():
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []
    findings = []
    for file_result in data:
        for m in file_result.get('messages', []):
            rule_id = m.get('ruleId') or ''
            if not rule_id.startswith('security/'):
                continue
            findings.append({
                'tool': 'eslint-plugin-security',
                'file': file_result.get('filePath', ''),
                'line': m.get('line', 0),
                'severity': 'high' if m.get('severity') == 2 else 'medium',
                'rule': rule_id,
                'message': (m.get('message') or '').strip(),
            })
    return findings


# ---------------------------------------------------------------------------
# Semgrep (Go / Ruby / Java / PHP / Kotlin / Vue — languages bandit/eslint don't parse)
# ---------------------------------------------------------------------------

_SEMGREP_SEVERITY = {'ERROR': 'high', 'WARNING': 'medium', 'INFO': 'low'}


def _run_semgrep(exe: str, files: list[str]) -> tuple[str, str, int]:
    """Run semgrep against an explicit file list (not a directory) so it only touches
    the languages bandit/eslint don't cover, instead of re-scanning Python/JS/TS and
    duplicating findings those tools already report under different check IDs.

    `exe` should be the fully-resolved path from _which() — semgrep's pip-packaged
    console-script happens to be a real .exe on Windows so a bare 'semgrep' string
    works today, but resolving it the same way as bandit/eslint keeps this from being
    an accident of one packaging method (see _run_eslint()'s docstring for the case
    where it genuinely matters)."""
    proc = subprocess.run(
        [exe, 'scan', '--config=auto', '--json', '--quiet', *files],
        capture_output=True, text=True, encoding='utf-8', errors='replace',
    )
    return proc.stdout, proc.stderr, proc.returncode


def _parse_semgrep_json(raw: str) -> list[dict]:
    if not raw or not raw.strip():
        return []
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        return []
    findings = []
    for r in data.get('results', []):
        extra = r.get('extra', {})
        findings.append({
            'tool': 'semgrep',
            'file': r.get('path', ''),
            'line': (r.get('start') or {}).get('line', 0),
            'severity': _SEMGREP_SEVERITY.get(str(extra.get('severity', '')).upper(), 'low'),
            'rule': r.get('check_id', ''),
            'message': (extra.get('message') or '').strip(),
        })
    return findings


# ---------------------------------------------------------------------------
# Scan orchestration
# ---------------------------------------------------------------------------

def run_scan(src: str, min_severity: str = 'medium') -> dict:
    """Run whichever tools apply to the languages found under src.

    Returns:
      {
        src, tools_run, tools_skipped, findings, blocking_findings, passed
      }
    tools_skipped entries explain *why* a language's files weren't scanned
    (tool missing, or the tool itself errored) — the same "don't let an
    unscanned language look like a clean pass" concern verify_spec_code.py's
    zero_coverage warning addresses for spec<->code drift.
    """
    py_files = _find_files(src, _PY_EXT)
    js_files = _find_files(src, _JS_EXT)

    findings: list[dict] = []
    tools_run: list[str] = []
    tools_skipped: list[dict] = []

    if py_files:
        bandit_exe = _which('bandit')
        if bandit_exe:
            raw, err, rc = _run_bandit(bandit_exe, src)
            if rc not in (0, 1):
                tools_skipped.append({
                    'tool': 'bandit', 'language': 'python', 'files': len(py_files),
                    'reason': f"bandit exited with code {rc} — {(err or '').strip()[:200] or 'no stderr output'}",
                })
            else:
                findings += _parse_bandit_json(raw)
                tools_run.append('bandit')
        else:
            tools_skipped.append({
                'tool': 'bandit', 'language': 'python', 'files': len(py_files),
                'reason': 'bandit not installed — run: pip install bandit',
            })

    if js_files:
        eslint_exe = _which('eslint')
        if eslint_exe:
            raw, err, rc = _run_eslint(eslint_exe, src)
            if rc not in (0, 1):
                tools_skipped.append({
                    'tool': 'eslint-plugin-security', 'language': 'javascript/typescript',
                    'files': len(js_files),
                    'reason': (
                        f"eslint exited with code {rc} — {(err or '').strip()[:200] or 'no stderr output'}. "
                        "Likely eslint-plugin-security is not installed — "
                        "run: npm install --save-dev eslint eslint-plugin-security"
                    ),
                })
            else:
                findings += _parse_eslint_json(raw)
                tools_run.append('eslint-plugin-security')
        else:
            tools_skipped.append({
                'tool': 'eslint-plugin-security', 'language': 'javascript/typescript',
                'files': len(js_files),
                'reason': 'eslint not installed — run: npm install --save-dev eslint eslint-plugin-security',
            })

    semgrep_files = _find_files(src, _SEMGREP_EXT)
    if semgrep_files:
        semgrep_exe = _which('semgrep')
        if semgrep_exe:
            raw, err, rc = _run_semgrep(semgrep_exe, semgrep_files)
            if rc not in (0, 1):
                tools_skipped.append({
                    'tool': 'semgrep', 'language': 'go/ruby/java/php/kotlin/vue',
                    'files': len(semgrep_files),
                    'reason': f"semgrep exited with code {rc} — {(err or '').strip()[:200] or 'no stderr output'}",
                })
            else:
                findings += _parse_semgrep_json(raw)
                tools_run.append('semgrep')
        else:
            tools_skipped.append({
                'tool': 'semgrep', 'language': 'go/ruby/java/php/kotlin/vue',
                'files': len(semgrep_files),
                'reason': 'semgrep not installed — run: pip install semgrep',
            })

    threshold = _SEVERITY_RANK.get(min_severity, 1)
    blocking = [f for f in findings if _SEVERITY_RANK.get(f['severity'], 0) >= threshold]

    return {
        'src': src,
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
    print(f"\nSecurity Scan (SAST)  src={result['src']}")
    if result['tools_run']:
        print(f"  tools run: {', '.join(result['tools_run'])}")
    for skip in result['tools_skipped']:
        print(
            f"  [WARN] {skip['tool']} skipped ({skip['language']}, "
            f"{skip['files']} file(s) found): {skip['reason']}"
        )

    if not result['findings']:
        if not result['tools_run'] and not result['tools_skipped']:
            print("  [OK]  No Python or JS/TS files found under --src — nothing to scan.\n")
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
    # Force UTF-8 stdout/stderr — see verify_spec_code.py's main() for the
    # Windows-console rationale (non-ASCII "—" otherwise crashes print()).
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")

    parser = argparse.ArgumentParser(
        description='verify_security.py — SAST wrapper (bandit / eslint-plugin-security)',
    )
    parser.add_argument('--src', metavar='PATH', help='Path to source file or directory')
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
        help='Print which SAST tools are installed and exit',
    )
    args = parser.parse_args()

    if args.list_tools:
        for tool, lang in (
            ('bandit', 'Python'),
            ('eslint', 'JavaScript/TypeScript (requires eslint-plugin-security)'),
            ('semgrep', 'Go/Ruby/Java/PHP/Kotlin/Vue'),
        ):
            found = _which(tool)
            status = f'found at {found}' if found else 'NOT installed'
            print(f"  {tool:<8} ({lang}): {status}")
        sys.exit(0)

    # Graceful skip when not configured — pre-commit hook may call this before
    # the project has set security_scan_src, matching verify_spec_code.py's
    # unconfigured-skip behavior.
    if not args.src:
        print(
            "[WARN] verify_security: --src not configured — skipping.\n"
            "    This project has no SAST scanning until this is set. Set security_scan_src\n"
            "    in .project-starter.yml (the pre-commit hook and orchestrator.py both read\n"
            "    it automatically — no need to pass --src by hand), or pass --src directly.\n"
            "    See README.md -> Security Scan (SAST).",
        )
        sys.exit(0)

    if not os.path.exists(args.src):
        print(f"error: src path not found: {args.src}", file=sys.stderr)
        sys.exit(2)

    result = run_scan(args.src, args.min_severity)

    if args.json_output:
        print(json.dumps(result, indent=2))
    else:
        print_report(result, args.min_severity)

    ts = _telemetry_ts()
    status = 'pass' if result['passed'] else 'fail'
    _append_telemetry('verify_security', args.project_type or '', status, ts)

    if args.strict and not result['passed']:
        sys.exit(1)


if __name__ == '__main__':
    main()
