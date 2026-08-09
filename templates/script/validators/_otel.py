"""
_otel.py — optional OpenTelemetry dual-emission for project_starter_v5 telemetry.

Trace correlation: every span emitted while docs/current-state.md has a scoped Current
Task shares that task's trace_id, as a direct child of one synthetic "task: <name>" root
span created on the task's first emit() call. Each emit() call happens in its own process
(a validator invocation, an orchestrator.py run), so this is cross-process trace-context
propagation done by hand: the root's trace_id/span_id are persisted to
logs/telemetry/.otel_trace_context.json and reconstructed as a NonRecordingSpan parent
context on every later call for the same task -- OTel's normal in-process parent/child
tracking cannot see across separate Python processes on its own. A task change (the
persisted task name no longer matches the current one) starts a fresh trace. See README.md
-> Telemetry for how to point this at a local Jaeger and see the resulting waterfall.

Every place that already writes local JSON telemetry (.ai/telemetry/validation-result.json,
logs/telemetry/task-run.json, logs/telemetry/.orchestrator_runs.json,
logs/telemetry/skip-verify.json) can additionally emit the same event as an OTel span —
for teams that want it visible in a real observability backend (Honeycomb, Grafana Tempo,
Jaeger, ...) instead of only as local files. This is dual-write, not a replacement: the
local JSON files keep being written exactly as before, unconditionally — some of that data
is read back synchronously by this same framework (e.g. orchestrator.py's own run counter),
which an external OTel backend cannot serve back to a local process the same way. See
README.md -> Telemetry for the full explanation of why this is additive, not a migration.

Fully optional at two independent levels — either one missing means a silent no-op, never
an error:
  1. opentelemetry-api / -sdk / -exporter-otlp-proto-http not installed.
  2. OTEL_EXPORTER_OTLP_ENDPOINT environment variable not set (installed but unconfigured
     is the expected common case — this module never tries to export to nowhere).

Never raises, never blocks, and never prints noise on a failed export (e.g. the configured
collector is temporarily unreachable) — this is telemetry, not a gate. A pre-commit hook or
CI step must behave identically whether or not the collector happens to be reachable right
now; the OTel SDK's own internal error logging is deliberately suppressed for this reason
(confirmed: without suppression, a single unreachable-collector export prints a multi-frame
traceback to stderr on every call — unacceptable noise for something this optional).

Install:    pip install opentelemetry-api opentelemetry-sdk opentelemetry-exporter-otlp-proto-http
Configure:  export OTEL_EXPORTER_OTLP_ENDPOINT=https://your-collector:4318
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path

_tracer = None
_provider = None
_init_attempted = False

_TRACE_STATE_REL = Path("logs") / "telemetry" / ".otel_trace_context.json"


def _get_tracer():
    """Lazily build a tracer once per process. Returns None if OTel isn't usable —
    either not installed, or installed but no endpoint configured."""
    global _tracer, _provider, _init_attempted
    if _init_attempted:
        return _tracer
    _init_attempted = True

    if not os.environ.get('OTEL_EXPORTER_OTLP_ENDPOINT'):
        return None

    try:
        import logging
        logging.getLogger('opentelemetry').setLevel(logging.CRITICAL)

        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (  # noqa: PLC0415
            OTLPSpanExporter,
        )
        from opentelemetry.sdk.resources import Resource  # noqa: PLC0415
        from opentelemetry.sdk.trace import TracerProvider  # noqa: PLC0415
        from opentelemetry.sdk.trace.export import BatchSpanProcessor  # noqa: PLC0415
    except ImportError:
        return None

    try:
        _provider = TracerProvider(
            resource=Resource.create({'service.name': 'project_starter_v5'}),
        )
        exporter = OTLPSpanExporter(timeout=2)
        _provider.add_span_processor(
            BatchSpanProcessor(exporter, schedule_delay_millis=100),
        )
        _tracer = _provider.get_tracer('project_starter_v5')
    except Exception:  # noqa: BLE001 — telemetry setup must never break the caller
        _tracer = None

    return _tracer


def _current_task_name(cwd: str) -> str | None:
    """Best-effort read of the scoped Current Task name from current-state.md — same
    parsing pretooluse_scope_guard.py already uses, kept independent rather than shared
    since that module lives under adapters/claude/ (Claude-Code-specific) and this one
    must work from any validator regardless of which agent tool is in use. Returns None
    for no file, no Task line, or an unfilled `[...]` placeholder — callers fall back to
    an uncorrelated span in that case, same as before this feature existed."""
    cwd_path = Path(cwd)
    docs_path = "docs"
    try:
        for line in (cwd_path / ".project-starter.yml").read_text(encoding="utf-8").splitlines():
            if line.startswith("docs_path:"):
                docs_path = line.split(":", 1)[1].strip().strip("\"'") or "docs"
                break
    except OSError:
        pass

    try:
        content = (cwd_path / docs_path.strip("/") / "current-state.md").read_text(encoding="utf-8")
    except OSError:
        return None

    m = re.search(r"^\*\*Task:\*\*\s*(.*)$", content, re.MULTILINE)
    if not m:
        return None
    task = m.group(1).strip()
    if not task or re.match(r"^\[.*\]$", task):
        return None
    return task


def _load_trace_state(cwd: str) -> dict | None:
    try:
        return json.loads((Path(cwd) / _TRACE_STATE_REL).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _save_trace_state(cwd: str, state: dict) -> None:
    path = Path(cwd) / _TRACE_STATE_REL
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state), encoding="utf-8")


def _task_parent_context(task_name: str, cwd: str):
    """Context whose current span is a NonRecordingSpan pointing at this task's root span
    — created once per task, on the first emit() call for it, then reconstructed from the
    persisted trace_id/span_id on every later call (including from other processes). Every
    span started with this as its parent shares the task's trace_id and shows up as a
    direct child of the root in a trace-waterfall view. Returns None if OTel isn't usable —
    callers must already have confirmed _get_tracer() is non-None before calling this."""
    from opentelemetry import trace  # noqa: PLC0415

    state = _load_trace_state(cwd)
    if state and state.get("task") == task_name:
        trace_id = int(state["trace_id"], 16)
        span_id = int(state["span_id"], 16)
    else:
        # New task, or first emit() ever for it — create and export the root span once.
        with _tracer.start_as_current_span(f"task: {task_name}") as root_span:
            root_span.set_attribute("task", task_name)
            ctx = root_span.get_span_context()
            trace_id, span_id = ctx.trace_id, ctx.span_id
        if _provider is not None:
            _provider.force_flush(timeout_millis=2000)
        _save_trace_state(cwd, {
            "task": task_name,
            "trace_id": format(trace_id, "032x"),
            "span_id": format(span_id, "016x"),
        })

    span_context = trace.SpanContext(
        trace_id=trace_id,
        span_id=span_id,
        is_remote=True,
        trace_flags=trace.TraceFlags(trace.TraceFlags.SAMPLED),
    )
    return trace.set_span_in_context(trace.NonRecordingSpan(span_context))


def _stringify_attributes(data: dict) -> dict:
    """Span attributes must be primitive types — coerce anything else to str, drop None."""
    attrs: dict = {}
    for k, v in data.items():
        if v is None:
            continue
        if isinstance(v, (str, bool, int, float)):
            attrs[str(k)] = v
        else:
            attrs[str(k)] = str(v)
    return attrs


def emit(name: str, attributes: dict, cwd: str = ".") -> None:
    """Emit one OTel span named `name` with `attributes`. Always safe to call
    unconditionally — no-ops (does not raise) whenever OTel isn't usable, per this
    module's docstring. When docs/current-state.md (resolved from `cwd`) has a scoped
    Current Task, the span is correlated into that task's trace (see _task_parent_context);
    otherwise it's an uncorrelated single span, same as before this feature existed."""
    try:
        tracer = _get_tracer()
        if tracer is None:
            return
        task_name = _current_task_name(cwd)
        parent_context = _task_parent_context(task_name, cwd) if task_name else None
        with tracer.start_as_current_span(name, context=parent_context) as span:
            for k, v in _stringify_attributes(attributes).items():
                span.set_attribute(k, v)
        if _provider is not None:
            _provider.force_flush(timeout_millis=2000)
    except Exception:  # noqa: BLE001 — telemetry must never break the caller
        return
