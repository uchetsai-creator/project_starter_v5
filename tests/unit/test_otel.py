"""Tests for _otel.py — optional OpenTelemetry dual-emission.

emit() must be safe to call unconditionally from every telemetry write point
(_verify_common._append_telemetry, orchestrator._track_orchestrator_run, the
skip-verify block in .githooks/pre-commit) regardless of whether opentelemetry-* is
installed or OTEL_EXPORTER_OTLP_ENDPOINT is configured — these tests cover both the
common no-op case and, when the real packages are installed, the "configured but
collector unreachable" case, confirmed manually not to raise or print noise before
writing this test (see CHANGELOG.md).
"""
import importlib.util
import subprocess
import sys
from pathlib import Path

import pytest

_OTEL_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "templates" / "script" / "validators" / "_otel.py"
)


def _fresh_module():
    """Load a fresh copy each test — _otel.py caches _tracer/_init_attempted at module
    level, and tests need to control that state independently."""
    spec = importlib.util.spec_from_file_location("_otel_test", _OTEL_PATH)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


# ---------------------------------------------------------------------------
# No endpoint configured — the expected common case, must be a fast no-op
# ---------------------------------------------------------------------------

def test_emit_with_no_endpoint_configured_is_noop(monkeypatch):
    monkeypatch.delenv("OTEL_EXPORTER_OTLP_ENDPOINT", raising=False)
    otel = _fresh_module()
    otel.emit("test-event", {"status": "pass"})  # must not raise
    assert otel._get_tracer() is None


def test_get_tracer_result_is_cached_across_calls(monkeypatch):
    monkeypatch.delenv("OTEL_EXPORTER_OTLP_ENDPOINT", raising=False)
    otel = _fresh_module()
    assert otel._init_attempted is False
    otel._get_tracer()
    assert otel._init_attempted is True
    # second call must not re-attempt initialization
    otel._get_tracer()
    assert otel._init_attempted is True


# ---------------------------------------------------------------------------
# _stringify_attributes — span attributes must be primitive types
# ---------------------------------------------------------------------------

def test_stringify_attributes_keeps_primitives():
    otel = _fresh_module()
    result = otel._stringify_attributes({"status": "pass", "runs": 3, "ok": True})
    assert result == {"status": "pass", "runs": 3, "ok": True}


def test_stringify_attributes_coerces_other_types():
    otel = _fresh_module()
    result = otel._stringify_attributes({"data": {"nested": 1}, "items": [1, 2]})
    assert result["data"] == "{'nested': 1}"
    assert result["items"] == "[1, 2]"


def test_stringify_attributes_drops_none_values():
    otel = _fresh_module()
    result = otel._stringify_attributes({"status": "pass", "extra": None})
    assert "extra" not in result
    assert result == {"status": "pass"}


# ---------------------------------------------------------------------------
# opentelemetry not installed — must degrade to a no-op, not raise
# ---------------------------------------------------------------------------

def test_missing_opentelemetry_package_is_noop(monkeypatch):
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://127.0.0.1:1")
    otel = _fresh_module()

    import builtins
    real_import = builtins.__import__

    def _fake_import(name, *args, **kwargs):
        if name.startswith("opentelemetry"):
            raise ImportError(f"simulated missing package: {name}")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", _fake_import)
    otel.emit("test-event", {"status": "pass"})  # must not raise
    assert otel._get_tracer() is None


# ---------------------------------------------------------------------------
# Real opentelemetry package, unreachable collector — skipped if not installed
# ---------------------------------------------------------------------------

_HAS_OTEL = importlib.util.find_spec("opentelemetry") is not None


@pytest.mark.skipif(not _HAS_OTEL, reason="opentelemetry packages not installed")
def test_emit_against_unreachable_collector_does_not_raise_or_hang(monkeypatch):
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://127.0.0.1:1")
    otel = _fresh_module()
    # Must complete well under the test's own timeout and not raise.
    otel.emit("test-event", {"status": "pass", "project_type": "web-app"})


def _write_scoped_task(root: Path, task_name: str) -> None:
    (root / ".project-starter.yml").write_text(
        "project_type: web-app\ndocs_path: docs/\n", encoding="utf-8",
    )
    docs = root / "docs"
    docs.mkdir(exist_ok=True)
    (docs / "current-state.md").write_text(f"**Task:** {task_name}\n", encoding="utf-8")


def _memory_exporter_for(otel):
    """Force real (but unreachable) OTLP init, then bolt on an in-memory exporter so
    finished spans can be inspected directly — no real collector needed."""
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

    otel._get_tracer()
    exporter = InMemorySpanExporter()
    otel._provider.add_span_processor(SimpleSpanProcessor(exporter))
    return exporter


# ---------------------------------------------------------------------------
# Trace correlation — spans for the same scoped task must share one trace_id
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not _HAS_OTEL, reason="opentelemetry packages not installed")
def test_spans_for_same_task_share_trace_id(tmp_path, monkeypatch):
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://127.0.0.1:1")
    otel = _fresh_module()
    _write_scoped_task(tmp_path, "Build the order API")
    exporter = _memory_exporter_for(otel)

    otel.emit("validator-a", {"status": "pass"}, cwd=str(tmp_path))
    otel.emit("validator-b", {"status": "fail"}, cwd=str(tmp_path))

    spans = exporter.get_finished_spans()
    names = {s.name for s in spans}
    assert "validator-a" in names
    assert "validator-b" in names
    assert "task: Build the order API" in names, "synthetic root span must be exported too"

    trace_ids = {s.context.trace_id for s in spans}
    assert len(trace_ids) == 1, f"expected one shared trace_id, got {len(trace_ids)}"


@pytest.mark.skipif(not _HAS_OTEL, reason="opentelemetry packages not installed")
def test_child_spans_have_root_as_parent(tmp_path, monkeypatch):
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://127.0.0.1:1")
    otel = _fresh_module()
    _write_scoped_task(tmp_path, "Build the order API")
    exporter = _memory_exporter_for(otel)

    otel.emit("validator-a", {"status": "pass"}, cwd=str(tmp_path))

    spans = {s.name: s for s in exporter.get_finished_spans()}
    root = spans["task: Build the order API"]
    child = spans["validator-a"]
    assert child.parent is not None
    assert child.parent.span_id == root.context.span_id


@pytest.mark.skipif(not _HAS_OTEL, reason="opentelemetry packages not installed")
def test_second_process_reuses_same_root_via_persisted_state(tmp_path, monkeypatch):
    """The whole point: emit() calls from *separate* Python processes for the same task
    must still land in one trace. Simulated here by resetting the module (fresh globals,
    like a new process) between calls, while the persisted state file survives."""
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://127.0.0.1:1")
    _write_scoped_task(tmp_path, "Build the order API")

    otel1 = _fresh_module()
    exporter1 = _memory_exporter_for(otel1)
    otel1.emit("validator-a", {"status": "pass"}, cwd=str(tmp_path))
    trace_id_1 = exporter1.get_finished_spans()[0].context.trace_id

    otel2 = _fresh_module()  # fresh module globals == simulating a new process
    exporter2 = _memory_exporter_for(otel2)
    otel2.emit("validator-b", {"status": "pass"}, cwd=str(tmp_path))
    spans2 = exporter2.get_finished_spans()
    # only the event span is expected here — the root was already created by otel1 and
    # the persisted state should be reused, not recreated
    assert [s.name for s in spans2] == ["validator-b"]
    assert spans2[0].context.trace_id == trace_id_1


@pytest.mark.skipif(not _HAS_OTEL, reason="opentelemetry packages not installed")
def test_different_tasks_get_different_trace_ids(tmp_path, monkeypatch):
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://127.0.0.1:1")
    otel = _fresh_module()

    _write_scoped_task(tmp_path, "Task A")
    exporter = _memory_exporter_for(otel)
    otel.emit("validator-a", {"status": "pass"}, cwd=str(tmp_path))
    trace_id_a = exporter.get_finished_spans()[-1].context.trace_id

    _write_scoped_task(tmp_path, "Task B")
    otel.emit("validator-b", {"status": "pass"}, cwd=str(tmp_path))
    trace_id_b = exporter.get_finished_spans()[-1].context.trace_id

    assert trace_id_a != trace_id_b


@pytest.mark.skipif(not _HAS_OTEL, reason="opentelemetry packages not installed")
def test_no_scoped_task_still_emits_uncorrelated_span(tmp_path, monkeypatch):
    """No current-state.md / no scoped task -- must degrade to the pre-existing
    uncorrelated-span behavior, not raise or silently drop the event."""
    monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://127.0.0.1:1")
    otel = _fresh_module()
    exporter = _memory_exporter_for(otel)

    otel.emit("validator-a", {"status": "pass"}, cwd=str(tmp_path))

    spans = exporter.get_finished_spans()
    assert [s.name for s in spans] == ["validator-a"]
    assert spans[0].parent is None


@pytest.mark.skipif(not _HAS_OTEL, reason="opentelemetry packages not installed")
def test_emit_against_unreachable_collector_prints_no_traceback(monkeypatch):
    """Regression: without suppressing opentelemetry's internal logger, a failed
    export prints a multi-frame traceback to stderr — unacceptable noise for an
    optional, unconfigured-by-default feature. See _otel.py's docstring."""
    code = (
        "import os, sys\n"
        "os.environ['OTEL_EXPORTER_OTLP_ENDPOINT'] = 'http://127.0.0.1:1'\n"
        f"sys.path.insert(0, r'{_OTEL_PATH.parent}')\n"
        "import _otel\n"
        "_otel.emit('test-event', {'status': 'pass'})\n"
        "print('DONE')\n"
    )
    result = subprocess.run(
        [sys.executable, "-c", code],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=15,
    )
    assert "DONE" in result.stdout
    assert "Traceback" not in result.stderr
