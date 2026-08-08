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
