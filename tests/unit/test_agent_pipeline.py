"""Tests for agent_pipeline.py — proves the retry-on-format-noncompliance logic, usage/
cost accumulation, and OTel emission are real, using an injected fake caller so no live
`claude` process or network access is needed. Also proves the two things this design
deliberately does NOT do: retry a role just because it returned a legitimate "fail", and
retry a CLI-level infrastructure failure as if it were the agent's fault.

The fake JSON envelope used in test_default_caller_* below matches the real shape
returned by a live `claude -p "..." --output-format json` call (verified manually before
writing this file — see agent_pipeline.py's module docstring), not a guessed shape.
"""
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "templates" / "script" / "framework"))
sys.path.insert(0, str(REPO_ROOT / "templates" / "script" / "validators"))

import _otel  # noqa: E402
import agent_pipeline  # noqa: E402


def _valid(status="pass", findings=None):
    return json.dumps({"status": status, "findings": findings or []})


def _cr(text, input_tokens=10, output_tokens=5, cost_usd=0.001, duration_ms=100,
        cache_creation=0, cache_read=0):
    return agent_pipeline.CallResult(
        text=text,
        input_tokens=input_tokens,
        output_tokens=output_tokens,
        cache_creation_input_tokens=cache_creation,
        cache_read_input_tokens=cache_read,
        cost_usd=cost_usd,
        duration_ms=duration_ms,
    )


class FakeCaller:
    """Returns queued CallResults (or raises a queued exception) in order, one per call;
    records every prompt it was called with so tests can assert on retry-prompt content
    and call counts."""

    def __init__(self, responses):
        self._responses = list(responses)
        self.prompts: list[str] = []

    def __call__(self, prompt: str):
        self.prompts.append(prompt)
        item = self._responses.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


_ROLE = agent_pipeline.ROLES[0]  # code-quality-check — no dependencies, simplest to isolate


def test_call_agent_succeeds_on_first_attempt():
    caller = FakeCaller([_cr(_valid("pass"))])
    result = agent_pipeline.call_agent(_ROLE, "context", caller=caller)
    assert result["status"] == "pass"
    assert result["_attempts"] == 1
    assert len(caller.prompts) == 1


def test_call_agent_retries_on_malformed_json_then_succeeds():
    caller = FakeCaller([_cr("not json at all"), _cr(_valid("pass"))])
    result = agent_pipeline.call_agent(_ROLE, "context", caller=caller)
    assert result["status"] == "pass"
    assert result["_attempts"] == 2
    assert len(caller.prompts) == 2
    # the retry prompt must carry the previous failure forward, not just repeat the ask
    assert "Validation error" in caller.prompts[1]
    assert "not json at all" in caller.prompts[1]


def test_call_agent_retries_on_schema_violation_then_succeeds():
    missing_status = json.dumps({"findings": []})
    caller = FakeCaller([_cr(missing_status), _cr(_valid("fail", [{"description": "x", "severity": "Low"}]))])
    result = agent_pipeline.call_agent(_ROLE, "context", caller=caller)
    assert result["status"] == "fail"
    assert result["_attempts"] == 2


def test_call_agent_raises_after_exhausting_retries():
    caller = FakeCaller([_cr("garbage"), _cr("still garbage"), _cr("more garbage")])
    with pytest.raises(agent_pipeline.AgentCallError) as excinfo:
        agent_pipeline.call_agent(_ROLE, "context", caller=caller, max_retries=2)
    assert excinfo.value.role_name == "code-quality-check"
    assert len(excinfo.value.attempts) == 3  # 1 initial + 2 retries, bounded, not infinite
    assert len(caller.prompts) == 3


def test_call_agent_does_not_retry_a_legitimate_fail():
    """The whole point of scoping retry to format-compliance only: a well-formed "fail"
    with real findings is a correct answer, not an AI error — retrying it would just be
    re-rolling until the agent says "pass", which this design explicitly refuses to do."""
    caller = FakeCaller([_cr(_valid("fail", [{"description": "missing error handling", "severity": "High"}]))])
    result = agent_pipeline.call_agent(_ROLE, "context", caller=caller)
    assert result["status"] == "fail"
    assert result["_attempts"] == 1
    assert len(caller.prompts) == 1


def test_call_agent_respects_custom_max_retries():
    caller = FakeCaller([_cr("bad")] * 5)
    with pytest.raises(agent_pipeline.AgentCallError):
        agent_pipeline.call_agent(_ROLE, "context", caller=caller, max_retries=0)
    assert len(caller.prompts) == 1  # max_retries=0 -> exactly one attempt, no retry at all


def test_call_agent_does_not_retry_cli_invocation_errors():
    """A CLI-level failure (crash, bad envelope, --max-budget-usd hit) is an
    infrastructure problem, not the agent giving a malformed answer — it must propagate
    immediately, not get swallowed into the format-compliance retry loop."""
    caller = FakeCaller([agent_pipeline.AgentInvocationError("claude CLI exited 1: boom")])
    with pytest.raises(agent_pipeline.AgentInvocationError):
        agent_pipeline.call_agent(_ROLE, "context", caller=caller, max_retries=2)
    assert len(caller.prompts) == 1  # never retried


def test_call_agent_accumulates_usage_across_retries():
    """A wasted malformed attempt still cost real money — the total must include it, not
    just the final successful attempt's cost."""
    caller = FakeCaller([
        _cr("not json", input_tokens=10, output_tokens=5, cost_usd=0.001, duration_ms=100),
        _cr(_valid("pass"), input_tokens=20, output_tokens=8, cost_usd=0.002, duration_ms=150),
    ])
    result = agent_pipeline.call_agent(_ROLE, "context", caller=caller)
    usage = result["_usage"]
    assert usage["input_tokens"] == 30
    assert usage["output_tokens"] == 13
    assert usage["cost_usd"] == pytest.approx(0.003)
    assert usage["duration_ms"] == 250


def test_agent_call_error_carries_usage_spent_on_failed_attempts():
    caller = FakeCaller([_cr("bad", cost_usd=0.001), _cr("still bad", cost_usd=0.001)])
    with pytest.raises(agent_pipeline.AgentCallError) as excinfo:
        agent_pipeline.call_agent(_ROLE, "context", caller=caller, max_retries=1)
    assert excinfo.value.usage["cost_usd"] == pytest.approx(0.002)


def test_validate_response_rejects_bad_severity():
    bad = json.dumps({"status": "fail", "findings": [{"description": "x", "severity": "Critical"}]})
    with pytest.raises(ValueError, match="severity"):
        agent_pipeline._validate_response(bad)


def test_run_pipeline_respects_dependency_order_and_forwards_upstream_result():
    caller = FakeCaller([_cr(_valid("pass")), _cr(_valid("pass"))])
    result = agent_pipeline.run_pipeline("context", caller=caller)
    assert list(result["roles"].keys()) == ["code-quality-check", "module-completion-check"]
    # module-completion-check's prompt must include code-quality-check's result —
    # proves results are actually integrated, not just run back-to-back independently
    assert "code-quality-check" in caller.prompts[1]
    assert '"status": "pass"' in caller.prompts[1]


def test_run_pipeline_overall_status_is_fail_if_any_role_fails():
    caller = FakeCaller([_cr(_valid("pass")), _cr(_valid("fail", [{"description": "x", "severity": "Nit"}]))])
    result = agent_pipeline.run_pipeline("context", caller=caller)
    assert result["overall_status"] == "fail"


def test_run_pipeline_overall_status_is_pass_if_all_roles_pass():
    caller = FakeCaller([_cr(_valid("pass")), _cr(_valid("pass"))])
    result = agent_pipeline.run_pipeline("context", caller=caller)
    assert result["overall_status"] == "pass"


def test_run_pipeline_total_usage_sums_across_roles():
    caller = FakeCaller([
        _cr(_valid("pass"), input_tokens=10, cost_usd=0.001),
        _cr(_valid("pass"), input_tokens=20, cost_usd=0.002),
    ])
    result = agent_pipeline.run_pipeline("context", caller=caller)
    assert result["total_usage"]["input_tokens"] == 30
    assert result["total_usage"]["cost_usd"] == pytest.approx(0.003)


# --- _default_caller: real CLI wiring, tested against a live-verified envelope shape ---

_REAL_ENVELOPE_SHAPE = {
    "type": "result", "subtype": "success", "is_error": False,
    "duration_ms": 2284, "duration_api_ms": 3405, "num_turns": 1,
    "result": "pong", "stop_reason": "end_turn",
    "session_id": "37111c71-8d77-4539-8694-51807c018b19",
    "total_cost_usd": 0.03374835,
    "usage": {
        "input_tokens": 2, "cache_creation_input_tokens": 7617,
        "cache_read_input_tokens": 15692, "output_tokens": 4,
    },
}


def test_default_caller_parses_real_envelope_shape(monkeypatch):
    captured_cmd = {}

    def fake_run(cmd, **kwargs):
        captured_cmd["cmd"] = cmd
        class _P:
            returncode = 0
            stdout = json.dumps(_REAL_ENVELOPE_SHAPE)
            stderr = ""
        return _P()

    monkeypatch.setattr(agent_pipeline.subprocess, "run", fake_run)
    result = agent_pipeline._default_caller("ping", max_budget_usd=0.5)

    assert result.text == "pong"
    assert result.input_tokens == 2
    assert result.output_tokens == 4
    assert result.cache_creation_input_tokens == 7617
    assert result.cache_read_input_tokens == 15692
    assert result.cost_usd == pytest.approx(0.03374835)
    assert result.duration_ms == 2284
    assert "--output-format" in captured_cmd["cmd"] and "json" in captured_cmd["cmd"]
    assert "--max-budget-usd" in captured_cmd["cmd"] and "0.5" in captured_cmd["cmd"]


def test_default_caller_omits_budget_flag_when_none(monkeypatch):
    captured_cmd = {}

    def fake_run(cmd, **kwargs):
        captured_cmd["cmd"] = cmd
        class _P:
            returncode = 0
            stdout = json.dumps(_REAL_ENVELOPE_SHAPE)
            stderr = ""
        return _P()

    monkeypatch.setattr(agent_pipeline.subprocess, "run", fake_run)
    agent_pipeline._default_caller("ping", max_budget_usd=None)
    assert "--max-budget-usd" not in captured_cmd["cmd"]


def test_default_caller_raises_agent_invocation_error_on_is_error(monkeypatch):
    envelope = dict(_REAL_ENVELOPE_SHAPE, is_error=True, subtype="error_max_turns")

    def fake_run(cmd, **kwargs):
        class _P:
            returncode = 0
            stdout = json.dumps(envelope)
            stderr = ""
        return _P()

    monkeypatch.setattr(agent_pipeline.subprocess, "run", fake_run)
    with pytest.raises(agent_pipeline.AgentInvocationError, match="error_max_turns"):
        agent_pipeline._default_caller("ping")


def test_default_caller_raises_agent_invocation_error_on_nonzero_exit(monkeypatch):
    def fake_run(cmd, **kwargs):
        class _P:
            returncode = 1
            stdout = ""
            stderr = "boom"
        return _P()

    monkeypatch.setattr(agent_pipeline.subprocess, "run", fake_run)
    with pytest.raises(agent_pipeline.AgentInvocationError, match="boom"):
        agent_pipeline._default_caller("ping")


# --- OTel emission: reuses this framework's existing optional _otel.py dual-emission ---

def test_call_agent_emits_one_otel_span_per_attempt(monkeypatch):
    calls = []
    monkeypatch.setattr(_otel, "emit", lambda name, attrs, **kw: calls.append((name, attrs)))
    caller = FakeCaller([_cr("not json"), _cr(_valid("pass"), input_tokens=7)])

    agent_pipeline.call_agent(_ROLE, "context", caller=caller)

    assert len(calls) == 2  # one span per attempt, including the failed one
    name, attrs = calls[1]
    assert name == "agent_pipeline.role_call"
    assert attrs["agent_pipeline.role"] == "code-quality-check"
    assert attrs["agent_pipeline.attempt"] == 2
    assert attrs["gen_ai.usage.input_tokens"] == 7
    assert attrs["agent_pipeline.retry_reason"] is not None  # 2nd attempt was a retry


def test_emit_span_is_a_silent_noop_when_otel_unavailable(monkeypatch):
    monkeypatch.setitem(sys.modules, "_otel", None)  # forces ImportError on `from _otel import ...`
    agent_pipeline._emit_span("code-quality-check", 1, _cr(_valid("pass")), None)  # must not raise
