#!/usr/bin/env python3
"""
agent_pipeline.py — Multi-agent orchestration layer with format-compliance retry, real
usage/cost tracking, and optional OTel emission.

Runs a small, ordered set of specialized agent roles (reusing this framework's own
Claude Code skills as role definitions — see adapters/claude/skills/) against a shared
context, integrates their results into one report, and retries a role's call when — and
only when — the agent's response fails to parse or fails to match the required JSON
schema. That is the one retry condition this module implements on purpose (a legitimate
finding, e.g. status="fail" with real findings, is never retried — retrying a correct
"fail" result would just be re-rolling the dice until a role happens to say "pass", which
is not error recovery, it's gaming the check).

Roles and their dependency order live in ROLES below. `run_pipeline()` calls each role in
order, passing every already-completed role's result forward as extra context for roles
that declare a dependency on it, and aggregates all role results (including usage) into
one report.

Transport is the official `claude-agent-sdk` (`pip install claude-agent-sdk`), Claude
Code's own headless invocation library — not a hand-rolled `subprocess.run(['claude',
'-p', ...])` call with manual JSON-envelope parsing (see CHANGELOG.md for why this
module was rewritten off that approach). Usage/cost/latency numbers come from the SDK's
own `ResultMessage` (`usage`, `total_cost_usd`, `duration_ms`) — the same ground-truth
envelope the CLI reports, not a client-side token estimate; field names verified against
the installed `claude-agent-sdk` package via `dataclasses.fields()`, not assumed from
docs alone (docs and installed package agreed at the time this was written — see
CHANGELOG.md for the exact version). Unlike the module this replaced, this has NOT been
verified against a live, unmocked `query()` call — only against the real dataclass shape
and monkeypatched tests (see tests/unit/test_agent_pipeline.py's test_default_caller_*
tests). `max_budget_usd` is passed straight through to `ClaudeAgentOptions`, which the SDK
enforces itself.

Permission mode is `dontAsk` + `allowed_tools=["Read", "Glob", "Grep"]` — the SDK docs'
own recommended shape for "a fixed, explicit tool surface for a headless agent": read-only
tools run without prompting (there is no human present to approve anything), and anything
not on that list is denied outright rather than falling through to a `canUseTool`
callback this module never registers (which would otherwise hang forever). A role never
needs to write files or run shell commands to review code — only to read it.

Each attempt is also emitted as a span via this framework's existing optional OTel
dual-emission layer (templates/script/validators/_otel.py) — silently a no-op unless
opentelemetry-* is installed and OTEL_EXPORTER_OTLP_ENDPOINT is set, exactly like every
other caller of that module. Attributes follow OpenTelemetry's GenAI semantic conventions
(`gen_ai.*`) where one exists for the value; that namespace is still marked experimental
upstream as of writing, so names may shift in a future OTel spec revision.

`call_agent()` takes a `caller` callback (`str -> CallResult`) so the retry, validation,
and usage-accumulation logic is fully unit-testable without a live `claude` process or
network access — same reasoning as mcp_tools.py's dict-in/dict-out design in this same
directory. The default caller (`_default_caller`) is real, working SDK wiring against
`claude_agent_sdk.query()`, not a stub — inject a fake caller only in tests. `query` /
`ClaudeAgentOptions` / the SDK exception classes are imported at module level inside a
try/except (mirroring how `framework_fix_agents.py`'s `_get_client()` treats its own
optional `anthropic` import) so this module stays importable even where `claude-agent-sdk`
isn't installed — `_default_caller` raises `AgentInvocationError` with an install hint the
first time it's actually called in that case, rather than failing at import time.

As of this rewrite, nothing in the shipped framework calls `run_pipeline()` yet — see
ROADMAP.md for the planned integration point. This module is deliberately still standalone
infrastructure, not orphaned-and-forgotten; its own test suite is what currently exercises
it, same as before the rewrite.
"""
from __future__ import annotations

import asyncio
import functools
import json
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable

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

_FRAMEWORK_DIR = Path(__file__).resolve().parent
_VALIDATORS_DIR = _FRAMEWORK_DIR.parent / "validators"
_REPO_ROOT = _FRAMEWORK_DIR.parent.parent.parent
_SKILLS_DIR = _REPO_ROOT / "adapters" / "claude" / "skills"

# Read-only tool surface for a headless role call — see module docstring's Permission
# mode paragraph for why dontAsk + this allowlist, not bypassPermissions or plan.
_HEADLESS_ALLOWED_TOOLS = ["Read", "Glob", "Grep"]

_VALID_SEVERITIES = {"High", "Medium", "Low", "Nit"}
_VALID_STATUSES = {"pass", "fail"}

# Safety default: every role call is capped unless the caller explicitly passes
# max_budget_usd=None. A stuck retry loop or a runaway prompt should hit this cap and
# fail loudly (AgentInvocationError) rather than spend an unbounded amount silently.
DEFAULT_MAX_BUDGET_USD_PER_CALL = 0.50

_USAGE_FIELDS = (
    "input_tokens", "output_tokens", "cache_creation_input_tokens",
    "cache_read_input_tokens", "cost_usd", "duration_ms",
)

# Dependency order matters: module-completion-check's own SKILL.md assumes a module is
# already known-good, so it only makes sense to run after code-quality-check has passed
# judgment on the same code — this is the "agent-to-agent dependency" this pipeline exists
# to demonstrate, not just two independent calls bundled together.
ROLES: list[dict] = [
    {
        "name": "code-quality-check",
        "skill_path": _SKILLS_DIR / "code-quality-check" / "SKILL.md",
        "depends_on": [],
    },
    {
        "name": "module-completion-check",
        "skill_path": _SKILLS_DIR / "module-completion-check" / "SKILL.md",
        "depends_on": ["code-quality-check"],
    },
]

RESPONSE_SCHEMA_DESCRIPTION = (
    'Respond with ONLY a JSON object of the shape: '
    '{"status": "pass"|"fail", "findings": [{"description": str, "severity": '
    '"High"|"Medium"|"Low"|"Nit"}]}. No prose outside the JSON.'
)


class AgentInvocationError(Exception):
    """Raised when the underlying `claude_agent_sdk.query()` call itself fails —
    claude-agent-sdk not installed, the CLI binary it wraps not found, a query process
    failure, an unparseable response, the SDK's own is_error flag, or a max_budget_usd
    cap hit. This is an infrastructure failure, not the agent producing a malformed
    answer, so call_agent() never retries it under the format-compliance loop — retrying
    a broken query the same way as a bad JSON reply would hide a real operational
    problem."""


class AgentCallError(Exception):
    """Raised when a role's response still fails to parse/validate after exhausting
    format-compliance retries — carries every raw attempt (so a human can see what the
    agent actually said) and the accumulated usage across all attempts (so a human can
    see what the failed attempts cost, not just that they failed)."""

    def __init__(self, role_name: str, attempts: list[str], last_error: str, usage: dict):
        self.role_name = role_name
        self.attempts = attempts
        self.last_error = last_error
        self.usage = usage
        super().__init__(
            f"role {role_name!r} failed after {len(attempts)} attempt(s): {last_error} "
            f"(cost so far: ${usage['cost_usd']:.4f})"
        )


@dataclass
class CallResult:
    """One `claude_agent_sdk.query()` invocation, reduced to what call_agent() needs:
    the agent's actual text answer plus the SDK's ground-truth usage/cost/latency
    numbers (from ResultMessage — the same envelope the `claude` CLI itself reports)."""

    text: str
    input_tokens: int
    output_tokens: int
    cache_creation_input_tokens: int
    cache_read_input_tokens: int
    cost_usd: float
    duration_ms: int


Caller = Callable[[str], CallResult]


def _default_caller(prompt: str, max_budget_usd: float | None = None) -> CallResult:
    """Real wiring against the official claude-agent-sdk. Synchronous wrapper around
    _default_caller_async() via asyncio.run() — call_agent()/run_pipeline() and the
    Caller type stay synchronous, so this is the one place the async/sync boundary
    lives, not spread across the whole module."""
    if not _SDK_AVAILABLE:
        raise AgentInvocationError(
            "claude-agent-sdk is not installed — pip install claude-agent-sdk"
        )
    return asyncio.run(_default_caller_async(prompt, max_budget_usd))


async def _default_caller_async(prompt: str, max_budget_usd: float | None) -> CallResult:
    """dontAsk + Read/Glob/Grep-only, no cwd/system_prompt override — see module
    docstring's Permission mode paragraph. max_budget_usd is enforced by the SDK
    itself when set (ClaudeAgentOptions.max_budget_usd), not checked after the fact."""
    options = ClaudeAgentOptions(
        permission_mode="dontAsk",
        allowed_tools=_HEADLESS_ALLOWED_TOOLS,
        max_budget_usd=max_budget_usd,
    )
    try:
        result_message: ResultMessage | None = None
        async for message in query(prompt=prompt, options=options):
            if isinstance(message, ResultMessage):
                result_message = message
    except CLINotFoundError as e:
        raise AgentInvocationError(
            f"claude-agent-sdk could not find the Claude Code CLI it wraps: {e}"
        ) from e
    except (ProcessError, ResultError) as e:
        raise AgentInvocationError(f"claude_agent_sdk.query() failed: {e}") from e
    except (CLIJSONDecodeError, ClaudeSDKError) as e:
        # ClaudeSDKError is the SDK's base class — this also catches MessageParseError,
        # which isn't exported at package top level to import and catch by name.
        raise AgentInvocationError(
            f"claude_agent_sdk.query() returned an unparseable response: {e}"
        ) from e

    if result_message is None:
        raise AgentInvocationError("claude_agent_sdk.query() produced no ResultMessage")
    if result_message.is_error:
        raise AgentInvocationError(
            f"claude_agent_sdk.query() reported an error: {result_message.subtype!r}"
        )

    usage = result_message.usage or {}
    return CallResult(
        text=result_message.result or "",
        input_tokens=usage.get("input_tokens", 0),
        output_tokens=usage.get("output_tokens", 0),
        cache_creation_input_tokens=usage.get("cache_creation_input_tokens", 0),
        cache_read_input_tokens=usage.get("cache_read_input_tokens", 0),
        cost_usd=result_message.total_cost_usd or 0.0,
        duration_ms=result_message.duration_ms,
    )


def _validate_response(raw: str) -> dict:
    """Raises ValueError with a human-readable reason on any schema violation — the
    exact reason is what gets fed back to the agent on retry, not a generic 'try again'."""
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as e:
        raise ValueError(f"response is not valid JSON: {e}") from e

    if not isinstance(parsed, dict):
        raise ValueError("response JSON must be an object")

    status = parsed.get("status")
    if status not in _VALID_STATUSES:
        raise ValueError(f"'status' must be one of {sorted(_VALID_STATUSES)}, got {status!r}")

    findings = parsed.get("findings")
    if not isinstance(findings, list):
        raise ValueError("'findings' must be a list")
    for i, finding in enumerate(findings):
        if not isinstance(finding, dict) or "description" not in finding or "severity" not in finding:
            raise ValueError(f"findings[{i}] must have 'description' and 'severity'")
        if finding["severity"] not in _VALID_SEVERITIES:
            raise ValueError(
                f"findings[{i}].severity must be one of {sorted(_VALID_SEVERITIES)}, "
                f"got {finding['severity']!r}"
            )

    return parsed


def _build_prompt(role: dict, context: str, prior_raw: str | None, prior_error: str | None) -> str:
    skill_text = role["skill_path"].read_text(encoding="utf-8")
    parts = [skill_text, "\n---\n", RESPONSE_SCHEMA_DESCRIPTION, "\n---\n", context]
    if prior_error is not None:
        # Format-compliance retry: tell the agent exactly what it got wrong last time
        # so the retry is a targeted correction, not an unguided second guess.
        parts.append(
            "\n---\nYour previous response did not match the required format.\n"
            f"Previous response:\n{prior_raw}\n\nValidation error: {prior_error}\n"
            "Respond again, fixing this — JSON only, matching the schema above."
        )
    return "\n".join(parts)


def _empty_usage() -> dict:
    return {field: (0.0 if field == "cost_usd" else 0) for field in _USAGE_FIELDS}


def _add_usage(totals: dict, call_result: CallResult) -> None:
    for field in _USAGE_FIELDS:
        totals[field] += getattr(call_result, field)


def _emit_span(role_name: str, attempt: int, call_result: CallResult, retry_reason: str | None) -> None:
    """Best-effort emission through this framework's existing _otel.py dual-emission
    layer — silently no-ops if OTel isn't installed/configured, or if _otel.py isn't
    importable from this location, exactly like every other caller of that module
    (see _otel.py's own docstring: "either one missing means a silent no-op, never an
    error"). Never raises."""
    try:
        if str(_VALIDATORS_DIR) not in sys.path:
            sys.path.insert(0, str(_VALIDATORS_DIR))
        from _otel import emit as _otel_emit  # noqa: PLC0415
    except ImportError:
        return

    _otel_emit(
        "agent_pipeline.role_call",
        {
            "gen_ai.system": "anthropic",
            "agent_pipeline.role": role_name,
            "agent_pipeline.attempt": attempt,
            "agent_pipeline.retry_reason": retry_reason,
            "gen_ai.usage.input_tokens": call_result.input_tokens,
            "gen_ai.usage.output_tokens": call_result.output_tokens,
            "agent_pipeline.cache_creation_input_tokens": call_result.cache_creation_input_tokens,
            "agent_pipeline.cache_read_input_tokens": call_result.cache_read_input_tokens,
            "agent_pipeline.cost_usd": call_result.cost_usd,
            "agent_pipeline.duration_ms": call_result.duration_ms,
        },
    )


def call_agent(
    role: dict,
    context: str,
    caller: Caller | None = None,
    max_retries: int = 2,
    max_budget_usd: float | None = DEFAULT_MAX_BUDGET_USD_PER_CALL,
) -> dict:
    """Calls `role` with `context`, retrying only on format/schema non-compliance, up to
    `max_retries` extra attempts (max_retries=2 -> 3 total calls). A legitimate
    status="fail" response is returned as-is on the first attempt — this function never
    retries because it dislikes the content of a well-formed answer. Every attempt's
    usage/cost is accumulated into the returned result's "_usage" — a wasted malformed
    attempt still cost real money and that cost is not hidden."""
    caller = caller or functools.partial(_default_caller, max_budget_usd=max_budget_usd)
    attempts: list[str] = []
    usage_totals = _empty_usage()
    prior_raw: str | None = None
    prior_error: str | None = None

    for attempt in range(max_retries + 1):
        prompt = _build_prompt(role, context, prior_raw, prior_error)
        call_result = caller(prompt)
        attempts.append(call_result.text)
        _add_usage(usage_totals, call_result)
        _emit_span(role["name"], attempt + 1, call_result, prior_error)

        try:
            result = _validate_response(call_result.text)
            result["_attempts"] = len(attempts)
            result["_usage"] = usage_totals
            return result
        except ValueError as e:
            if attempt == max_retries:
                raise AgentCallError(role["name"], attempts, str(e), usage_totals) from e
            prior_raw, prior_error = call_result.text, str(e)

    raise AssertionError("unreachable")  # loop always returns or raises above


def _ordered_roles() -> list[dict]:
    """Topological order by `depends_on`, stable otherwise. With only two roles and one
    dependency edge today this is overkill for the current ROLES list, but it means a
    third role can declare a dependency without anyone having to hand-sort ROLES again."""
    resolved: list[dict] = []
    resolved_names: set[str] = set()
    remaining = list(ROLES)
    while remaining:
        progressed = False
        for role in list(remaining):
            if set(role["depends_on"]) <= resolved_names:
                resolved.append(role)
                resolved_names.add(role["name"])
                remaining.remove(role)
                progressed = True
        if not progressed:
            missing = [r["name"] for r in remaining]
            raise ValueError(f"unresolvable role dependencies (cycle?): {missing}")
    return resolved


def run_pipeline(
    context: str,
    caller: Caller | None = None,
    max_retries: int = 2,
    max_budget_usd: float | None = DEFAULT_MAX_BUDGET_USD_PER_CALL,
) -> dict:
    """Runs every role in ROLES in dependency order, folding each completed role's result
    into the context passed to roles that depend on it, and returns one aggregated report
    including a "total_usage" summed across every role and every attempt (including
    retries)."""
    results: dict[str, dict] = {}
    for role in _ordered_roles():
        role_context = context
        if role["depends_on"]:
            upstream = {name: results[name] for name in role["depends_on"]}
            role_context += "\n---\nUpstream role results:\n" + json.dumps(upstream)
        results[role["name"]] = call_agent(
            role, role_context, caller=caller, max_retries=max_retries, max_budget_usd=max_budget_usd,
        )

    overall_status = "pass" if all(r["status"] == "pass" for r in results.values()) else "fail"
    total_usage = _empty_usage()
    for r in results.values():
        for field in _USAGE_FIELDS:
            total_usage[field] += r["_usage"][field]

    return {"overall_status": overall_status, "roles": results, "total_usage": total_usage}
