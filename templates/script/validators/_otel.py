"""
_otel.py — optional OpenTelemetry dual-emission for project_starter_v5 telemetry.

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

import os

_tracer = None
_provider = None
_init_attempted = False


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

        from opentelemetry.sdk.resources import Resource  # noqa: PLC0415
        from opentelemetry.sdk.trace import TracerProvider  # noqa: PLC0415
        from opentelemetry.sdk.trace.export import BatchSpanProcessor  # noqa: PLC0415
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import (  # noqa: PLC0415
            OTLPSpanExporter,
        )
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


def emit(name: str, attributes: dict) -> None:
    """Emit one OTel span named `name` with `attributes`. Always safe to call
    unconditionally — no-ops (does not raise) whenever OTel isn't usable, per this
    module's docstring."""
    try:
        tracer = _get_tracer()
        if tracer is None:
            return
        with tracer.start_as_current_span(name) as span:
            for k, v in _stringify_attributes(attributes).items():
                span.set_attribute(k, v)
        if _provider is not None:
            _provider.force_flush(timeout_millis=2000)
    except Exception:  # noqa: BLE001 — telemetry must never break the caller
        return
