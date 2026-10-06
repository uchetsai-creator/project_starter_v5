"""verify_logs accepts request_id as the request-tracing correlation id (alias of trace_id)."""

import sys
from pathlib import Path

_VALIDATORS_DIR = Path(__file__).resolve().parent.parent.parent / "templates" / "script" / "validators"
sys.path.insert(0, str(_VALIDATORS_DIR))

import verify_logs  # noqa: E402

sys.path.remove(str(_VALIDATORS_DIR))


def _spec_with_tracing(tracing_word: str) -> str:
    return (
        "# Logging Spec\n\n"
        "## Log Output Format\n\nJSON structured logging.\n"
        "Fields: `{\"level\": \"info\", \"event\": \"x\"}`\n\n"
        "## Required Log Points\n\n- request received\n- request completed\n- error\n\n"
        "## Module Naming Convention\n\nNUDD  NUDD cases\n\n"
        f"## Request Tracing\n\nEvery request carries a {tracing_word} in each log line.\n"
    )


def _check_tracing_status(tmp_path, text):
    specs = tmp_path / "specs"
    specs.mkdir()
    (specs / "logging-spec.md").write_text(text, encoding="utf-8")
    results = verify_logs.check_logging_spec(str(tmp_path), ["web-app"])
    matched = [r for r in results if r["check"] == "trace_id documented"]
    assert matched, "tracing check did not run for web-app"
    return matched[0]["status"]


def test_trace_id_passes(tmp_path):
    assert _check_tracing_status(tmp_path, _spec_with_tracing("trace_id")) == "pass"


def test_request_id_passes(tmp_path):
    assert _check_tracing_status(tmp_path, _spec_with_tracing("request_id")) == "pass"


def test_no_correlation_id_fails(tmp_path):
    assert _check_tracing_status(tmp_path, _spec_with_tracing("session cookie")) == "fail"
