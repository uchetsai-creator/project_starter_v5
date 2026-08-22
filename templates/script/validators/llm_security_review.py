#!/usr/bin/env python3
"""
llm_security_review.py — opt-in wrapper invoking Claude Code's /security-review Skill
in headless mode, layered on top of verify_security.py's deterministic SAST pass.

verify_security.py's bandit / eslint-plugin-security / Semgrep tools catch a fixed set
of known-unsafe patterns. This wrapper adds an LLM-driven pass over the current diff for
issues those pattern-matchers cannot see (business-logic auth bypass, unsafe trust
boundaries, prompt injection in an LLM-app project, etc.) — the same trade a human
security reviewer makes over a linter.

Usage via verify_security.py:
    python3 verify_security.py --src src/ --llm-review

Constraint: --llm-review must never appear in workflow-registry.yaml or pre-commit
sequences — same rule as verify_spec_code.py's --semantic (see that file's docstring).
It shells out to a live Claude Code session, and its output is non-deterministic, so it is
a developer-invoked analysis pass, never an automated gate. Findings are printed but never
affect --strict's exit code, for the same reason.

Requires: the `claude` CLI installed and authenticated on whatever machine runs this
(`claude auth login`, or ANTHROPIC_API_KEY set, depending on your auth mode). Missing or
unauthenticated CLI prints a [WARN] and skips — same graceful-degradation pattern as
semantic.py's ANTHROPIC_API_KEY check. This is a portability property, not a per-machine
dependency baked into this file: clone this repo onto any machine, install and log into
Claude Code once, and it works there too.

Token/cost accounting: `claude -p --output-format json` returns a JSON result envelope
that, as of the Claude Code versions this was tested against, includes a cost/usage
summary (`total_cost_usd`, `duration_ms`, `num_turns`). This wrapper reads whatever of
those fields is present via `.get(...)` and never assumes the schema — a CLI version
that renames or drops a field degrades to a None value here, not a crash. Usage is
appended to logs/telemetry/security-review-usage.json, mirroring semantic.py's
token-usage.json, and dual-emitted as an OTel span the same way.

CLI flags for non-interactive tool permission (e.g. --permission-mode) vary by Claude
Code version — verify against `claude --help` on your installed version before relying
on the exact invocation below; override with the CLAUDE_CLI_EXTRA_ARGS env var
(space-separated) if your version needs different flags.

Run self-test:
    python3 llm_security_review.py   # exits 0 on success; does not call the CLI
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

_DEFAULT_TIMEOUT_SECONDS = 300


def _find_claude_cli() -> str | None:
    return shutil.which('claude')


def run_llm_security_review(
    project_root: str = '.',
    timeout: int = _DEFAULT_TIMEOUT_SECONDS,
) -> dict:
    """Invoke `claude -p "/security-review" --output-format json` in project_root.

    Returns:
      {
        ran: bool,
        result_text: str | None,   # the review's findings, as returned by the skill
        cost_usd: float | None,
        duration_ms: int | None,
        num_turns: int | None,
        error: str | None,
      }
    Never raises — a missing CLI, failed auth, timeout, or unparsable output all return
    ran=False (or ran=True with unknown cost fields) with `error` explaining why, same
    spirit as semantic.py's client-unavailable path returning [] instead of raising.
    """
    exe = _find_claude_cli()
    if exe is None:
        msg = (
            "claude CLI not found on PATH — install Claude Code and run `claude auth login` "
            "(or set ANTHROPIC_API_KEY) to enable --llm-review."
        )
        print(f"[WARN] {msg}")
        return {'ran': False, 'result_text': None, 'cost_usd': None,
                'duration_ms': None, 'num_turns': None, 'error': msg}

    extra_args = os.environ.get('CLAUDE_CLI_EXTRA_ARGS', '').split()
    cmd = [exe, '-p', '/security-review', '--output-format', 'json', *extra_args]

    try:
        proc = subprocess.run(
            cmd, cwd=project_root, capture_output=True, text=True,
            encoding='utf-8', errors='replace', timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        msg = (
            f"claude CLI timed out after {timeout}s — set CLAUDE_CLI_EXTRA_ARGS if your "
            "version needs different flags, or pass a longer timeout to run_llm_security_review()."
        )
        print(f"[WARN] {msg}")
        return {'ran': False, 'result_text': None, 'cost_usd': None,
                'duration_ms': None, 'num_turns': None, 'error': msg}
    except OSError as exc:
        msg = f"failed to launch claude CLI: {exc}"
        print(f"[WARN] {msg}")
        return {'ran': False, 'result_text': None, 'cost_usd': None,
                'duration_ms': None, 'num_turns': None, 'error': msg}

    if proc.returncode != 0:
        msg = (
            f"claude CLI exited {proc.returncode} — "
            f"{(proc.stderr or '').strip()[:300] or 'no stderr output'}"
        )
        print(f"[WARN] {msg}")
        return {'ran': False, 'result_text': None, 'cost_usd': None,
                'duration_ms': None, 'num_turns': None, 'error': msg}

    raw = proc.stdout or ''
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        # Older/different CLI versions, or a CLAUDE_CLI_EXTRA_ARGS override that changes
        # --output-format: treat stdout as the review text itself rather than failing
        # the whole pass over an unparsable envelope.
        return {'ran': True, 'result_text': raw.strip() or None, 'cost_usd': None,
                'duration_ms': None, 'num_turns': None, 'error': None}

    return {
        'ran': True,
        'result_text': data.get('result') or data.get('response') or None,
        'cost_usd': data.get('total_cost_usd'),
        'duration_ms': data.get('duration_ms'),
        'num_turns': data.get('num_turns'),
        'error': None,
    }


def _write_review_telemetry(review: dict) -> None:
    """Append one row to logs/telemetry/security-review-usage.json — best-effort,
    never raises, mirroring semantic.py's _write_token_usage_telemetry."""
    if not review.get('ran'):
        return
    entry = {
        'ts': datetime.now(timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'),
        'cost_usd': review.get('cost_usd'),
        'duration_ms': review.get('duration_ms'),
        'num_turns': review.get('num_turns'),
    }
    try:
        output = os.path.join('logs', 'telemetry', 'security-review-usage.json')
        os.makedirs(os.path.dirname(output), exist_ok=True)
        rows = []
        if os.path.exists(output):
            with open(output, encoding='utf-8') as f:
                loaded = json.load(f)
            if isinstance(loaded, list):
                rows = loaded
        rows.append(entry)
        with open(output, 'w', encoding='utf-8') as f:
            json.dump(rows, f, indent=2)
    except Exception as exc:  # noqa: BLE001
        print(f"[WARN] failed to write security-review telemetry: {exc}")

    try:
        validators_dir = Path(__file__).resolve().parent
        if str(validators_dir) not in sys.path:
            sys.path.insert(0, str(validators_dir))
        from _otel import emit as _otel_emit  # noqa: PLC0415
        _otel_emit('llm_security_review', entry)
    except ImportError:
        pass


def print_review(review: dict) -> None:
    print("\nLLM Security Review (Claude Code /security-review, --llm-review)")
    if not review['ran']:
        print(f"  [WARN] skipped — {review['error']}\n")
        return
    if review['cost_usd'] is not None:
        print(
            f"  cost: ${review['cost_usd']:.4f}  "
            f"duration: {review.get('duration_ms')}ms  turns: {review.get('num_turns')}",
        )
    else:
        print("  (cost/duration not reported by this Claude Code version)")
    print("  --- findings ---")
    print(f"  {review['result_text'] or '(no output returned)'}")
    print(
        "\n  Note: this is a non-deterministic LLM pass, developer-invoked only — it never "
        "affects --strict's exit code. Read the findings yourself.\n",
    )


# ---------------------------------------------------------------------------
# Self-test (no real CLI call anywhere below — shutil.which and subprocess.run are
# monkeypatched for every path, including the "success" ones, so this never touches
# the network. See semantic.py's self-test for the same pattern applied to a direct
# Anthropic API client instead of a subprocess CLI call.)
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    import tempfile

    _real_which = shutil.which
    _real_subprocess_run = subprocess.run

    class _MockCompletedProcess:
        def __init__(self, stdout: str, returncode: int = 0, stderr: str = ''):
            self.stdout = stdout
            self.stderr = stderr
            self.returncode = returncode

    # --- test: claude CLI not found -> graceful skip, no exception ---
    shutil.which = lambda name: None  # type: ignore[assignment]
    try:
        result = run_llm_security_review()
        assert result['ran'] is False
        assert result['error'] is not None
    finally:
        shutil.which = _real_which  # type: ignore[assignment]

    # --- test: mocked successful CLI call -> JSON envelope parsed correctly ---
    mock_stdout = json.dumps({
        'result': 'No security findings.',
        'total_cost_usd': 0.0042,
        'duration_ms': 1234,
        'num_turns': 1,
    })
    shutil.which = lambda name: '/fake/path/to/claude'  # type: ignore[assignment]
    subprocess.run = lambda *a, **k: _MockCompletedProcess(mock_stdout)  # type: ignore[assignment]
    try:
        result_ok = run_llm_security_review()
        assert result_ok['ran'] is True
        assert result_ok['result_text'] == 'No security findings.'
        assert result_ok['cost_usd'] == 0.0042
        assert result_ok['duration_ms'] == 1234
        assert result_ok['num_turns'] == 1
        assert result_ok['error'] is None
    finally:
        shutil.which = _real_which  # type: ignore[assignment]
        subprocess.run = _real_subprocess_run  # type: ignore[assignment]

    # --- test: mocked non-JSON stdout -> falls back to raw text, cost unknown ---
    shutil.which = lambda name: '/fake/path/to/claude'  # type: ignore[assignment]
    subprocess.run = lambda *a, **k: _MockCompletedProcess('plain text review output')  # type: ignore[assignment]
    try:
        result_text_only = run_llm_security_review()
        assert result_text_only['ran'] is True
        assert result_text_only['result_text'] == 'plain text review output'
        assert result_text_only['cost_usd'] is None
    finally:
        shutil.which = _real_which  # type: ignore[assignment]
        subprocess.run = _real_subprocess_run  # type: ignore[assignment]

    # --- test: mocked non-zero exit (e.g. auth failure) -> graceful skip ---
    shutil.which = lambda name: '/fake/path/to/claude'  # type: ignore[assignment]
    subprocess.run = lambda *a, **k: _MockCompletedProcess(  # type: ignore[assignment]
        '', returncode=1, stderr='not authenticated',
    )
    try:
        result_auth_fail = run_llm_security_review()
        assert result_auth_fail['ran'] is False
        assert 'not authenticated' in result_auth_fail['error']
    finally:
        shutil.which = _real_which  # type: ignore[assignment]
        subprocess.run = _real_subprocess_run  # type: ignore[assignment]

    # --- test: telemetry write + read-back; ran=False writes nothing ---
    with tempfile.TemporaryDirectory() as tmpdir:
        cwd = os.getcwd()
        os.chdir(tmpdir)
        try:
            _write_review_telemetry({'ran': False})
            assert not os.path.exists('logs/telemetry/security-review-usage.json')

            _write_review_telemetry({
                'ran': True, 'cost_usd': 0.0123, 'duration_ms': 4200, 'num_turns': 3,
            })
            assert os.path.exists('logs/telemetry/security-review-usage.json')
            with open('logs/telemetry/security-review-usage.json', encoding='utf-8') as f:
                rows = json.load(f)
            assert len(rows) == 1
            assert rows[0]['cost_usd'] == 0.0123
        finally:
            os.chdir(cwd)

    print("[OK] llm_security_review self-test passed")
    sys.exit(0)
