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
It calls a live Claude Code session, and its output is non-deterministic, so it is
a developer-invoked analysis pass, never an automated gate. Findings are printed but never
affect --strict's exit code, for the same reason.

Transport is the official `claude-agent-sdk` (`pip install claude-agent-sdk`) — see
agent_pipeline.py's module docstring for the general rationale (this file was rewritten
off the same hand-rolled `subprocess.run(['claude', '-p', ...])` + manual JSON-envelope
parsing this replaced, for the same reason: the CLI-flags-vary-by-version problem the old
docstring warned about here doesn't exist with the SDK's typed `ClaudeAgentOptions` —
CLAUDE_CLI_EXTRA_ARGS is gone, there's nothing left to override). `/security-review` is
one of Claude Code's own bundled Skills — dispatched by name via the prompt string
(`query(prompt="/security-review", ...)`), the same mechanism the SDK's own docs use to
demonstrate dispatching a user-authored skill; no special-casing needed for it being
bundled rather than project-authored.

Requires: `claude-agent-sdk` installed (`pip install claude-agent-sdk`) and Claude Code
authenticated on whatever machine runs this (`claude auth login`, or ANTHROPIC_API_KEY
set). Missing package, missing/unauthenticated CLI, or a query-level error all print a
[WARN] and skip — same graceful-degradation pattern as semantic.py's ANTHROPIC_API_KEY
check. This is a portability property, not a per-machine dependency baked into this file:
clone this repo onto any machine, install and log into Claude Code once, and it works
there too.

Token/cost accounting: `claude_agent_sdk.query()`'s `ResultMessage` carries the same
ground-truth usage/cost/latency numbers the CLI itself reports (`total_cost_usd`,
`duration_ms`, `num_turns`) — see agent_pipeline.py's module docstring for how the field
names were verified against the installed package rather than assumed. Usage is appended
to logs/telemetry/security-review-usage.json, mirroring semantic.py's token-usage.json,
and dual-emitted as an OTel span the same way.

Permission mode is `dontAsk` + `allowed_tools=["Read", "Glob", "Grep"]` — read-only tools
run without prompting (no human is present to approve anything in a headless run), and
anything else is denied outright rather than falling through to an unregistered
`canUseTool` callback, which would otherwise hang. `/security-review` only needs to read
code to review it.

Run self-test:
    python3 llm_security_review.py   # exits 0 on success; does not call the CLI
"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    from claude_agent_sdk import (
        ClaudeAgentOptions,
        ClaudeSDKError,
        CLIJSONDecodeError,
        CLINotFoundError,
        ProcessError,
        ResultError,
        ResultMessage,
        query,
    )
    _SDK_AVAILABLE = True
except ImportError:
    _SDK_AVAILABLE = False

_DEFAULT_TIMEOUT_SECONDS = 300
_HEADLESS_ALLOWED_TOOLS = ["Read", "Glob", "Grep"]

_EMPTY_RESULT = {
    'ran': False, 'result_text': None, 'cost_usd': None,
    'duration_ms': None, 'num_turns': None, 'error': None,
}


def run_llm_security_review(
    project_root: str = '.',
    timeout: int = _DEFAULT_TIMEOUT_SECONDS,
) -> dict:
    """Invoke the /security-review Skill via claude_agent_sdk.query() in project_root.

    Returns:
      {
        ran: bool,
        result_text: str | None,   # the review's findings, as returned by the skill
        cost_usd: float | None,
        duration_ms: int | None,
        num_turns: int | None,
        error: str | None,
      }
    Never raises — a missing SDK/CLI, failed auth, timeout, or query-level error all
    return ran=False with `error` explaining why, same spirit as semantic.py's
    client-unavailable path returning [] instead of raising.
    """
    if not _SDK_AVAILABLE:
        msg = "claude-agent-sdk is not installed — pip install claude-agent-sdk to enable --llm-review."
        print(f"[WARN] {msg}")
        return {**_EMPTY_RESULT, 'error': msg}

    try:
        return asyncio.run(asyncio.wait_for(
            _run_llm_security_review_async(project_root), timeout=timeout,
        ))
    except asyncio.TimeoutError:
        msg = (
            f"claude_agent_sdk.query() timed out after {timeout}s — pass a longer "
            "timeout to run_llm_security_review()."
        )
        print(f"[WARN] {msg}")
        return {**_EMPTY_RESULT, 'error': msg}


async def _run_llm_security_review_async(project_root: str) -> dict:
    options = ClaudeAgentOptions(
        cwd=project_root,
        permission_mode="dontAsk",
        allowed_tools=_HEADLESS_ALLOWED_TOOLS,
    )
    try:
        result_message: ResultMessage | None = None
        async for message in query(prompt="/security-review", options=options):
            if isinstance(message, ResultMessage):
                result_message = message
    except CLINotFoundError as e:
        msg = (
            "claude-agent-sdk could not find the Claude Code CLI it wraps — install "
            f"Claude Code and run `claude auth login` (or set ANTHROPIC_API_KEY): {e}"
        )
        print(f"[WARN] {msg}")
        return {**_EMPTY_RESULT, 'error': msg}
    except (ProcessError, ResultError) as e:
        msg = f"claude_agent_sdk.query() failed: {e}"
        print(f"[WARN] {msg}")
        return {**_EMPTY_RESULT, 'error': msg}
    except (CLIJSONDecodeError, ClaudeSDKError) as e:
        # ClaudeSDKError is the SDK's base class — also catches MessageParseError,
        # which isn't exported at package top level to import and catch by name.
        msg = f"claude_agent_sdk.query() returned an unparseable response: {e}"
        print(f"[WARN] {msg}")
        return {**_EMPTY_RESULT, 'error': msg}

    if result_message is None:
        msg = "claude_agent_sdk.query() produced no ResultMessage"
        print(f"[WARN] {msg}")
        return {**_EMPTY_RESULT, 'error': msg}
    if result_message.is_error:
        msg = f"claude_agent_sdk.query() reported an error: {result_message.subtype!r}"
        print(f"[WARN] {msg}")
        return {**_EMPTY_RESULT, 'error': msg}

    return {
        'ran': True,
        'result_text': result_message.result or None,
        'cost_usd': result_message.total_cost_usd,
        'duration_ms': result_message.duration_ms,
        'num_turns': result_message.num_turns,
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
# Self-test (no real CLI call anywhere below — the SDK's query() is monkeypatched for
# every path, including the "success" ones, so this never touches the network. See
# semantic.py's self-test for the same pattern applied to a direct Anthropic API client,
# and agent_pipeline.py's test_agent_pipeline.py for the same query()-mocking approach
# — the SDK's own Transport class is an unstable internal API, not its intended test
# seam; mocking query() itself is.)
# ---------------------------------------------------------------------------

if __name__ == '__main__':
    import tempfile

    if not _SDK_AVAILABLE:
        print("[SKIP] llm_security_review self-test — claude-agent-sdk not installed")
        sys.exit(0)

    _real_query = query

    def _fake_result_message(**overrides) -> ResultMessage:
        fields: dict = {
            'subtype': 'success', 'duration_ms': 1234, 'duration_api_ms': 1500,
            'is_error': False, 'num_turns': 1, 'session_id': 'test-session',
            'stop_reason': 'end_turn', 'total_cost_usd': 0.0042,
            'result': 'No security findings.',
        }
        fields.update(overrides)
        return ResultMessage(**fields)  # type: ignore[arg-type]

    def _set_fake_query(result_message=None, exc=None):
        async def fake_query(*, prompt, options=None, transport=None):
            if exc is not None:
                raise exc
                yield  # pragma: no cover — makes this an async generator; never reached
            yield result_message
        globals()['query'] = fake_query

    def _restore_query():
        globals()['query'] = _real_query

    # --- test: CLI not found -> graceful skip, no exception ---
    _set_fake_query(exc=CLINotFoundError("claude CLI not found"))
    try:
        result = run_llm_security_review()
        assert result['ran'] is False
        assert result['error'] is not None
    finally:
        _restore_query()

    # --- test: mocked successful query -> ResultMessage fields mapped correctly ---
    _set_fake_query(result_message=_fake_result_message())
    try:
        result_ok = run_llm_security_review()
        assert result_ok['ran'] is True
        assert result_ok['result_text'] == 'No security findings.'
        assert result_ok['cost_usd'] == 0.0042
        assert result_ok['duration_ms'] == 1234
        assert result_ok['num_turns'] == 1
        assert result_ok['error'] is None
    finally:
        _restore_query()

    # --- test: mocked is_error result -> graceful skip ---
    _set_fake_query(result_message=_fake_result_message(
        is_error=True, subtype='error_during_execution', result=None,
    ))
    try:
        result_auth_fail = run_llm_security_review()
        assert result_auth_fail['ran'] is False
        assert 'error_during_execution' in result_auth_fail['error']
    finally:
        _restore_query()

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
