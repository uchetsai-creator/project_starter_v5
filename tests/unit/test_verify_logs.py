import sys
from pathlib import Path

import pytest

sys.path.insert(
    0,
    str(Path(__file__).resolve().parent.parent.parent / "templates/script/validators"),
)
from verify_logs import check_logging_spec, check_module_log_file


# ---------------------------------------------------------------------------
# check_logging_spec — N/A types return empty
# ---------------------------------------------------------------------------

def test_check_logging_spec_na_for_library(tmp_path):
    assert check_logging_spec(str(tmp_path), ["library"]) == []


def test_check_logging_spec_na_for_iac(tmp_path):
    assert check_logging_spec(str(tmp_path), ["iac"]) == []


# ---------------------------------------------------------------------------
# check_logging_spec — missing file
# ---------------------------------------------------------------------------

def test_check_logging_spec_missing_file_fails(tmp_path):
    (tmp_path / "specs").mkdir()
    results = check_logging_spec(str(tmp_path), ["web-app"])
    assert any(r["status"] == "fail" and "not found" in r["detail"] for r in results)


# ---------------------------------------------------------------------------
# check_logging_spec — sections and per-type checks
# ---------------------------------------------------------------------------

_GOOD_SPEC = """\
## Log Output Format
structured JSON
level: INFO/ERROR
timestamp: ISO8601

## Required Log Points
app start
request received
error raised

## Module Naming Convention
format: module.submodule
example: auth.login
prefix: app.

trace_id: propagated from X-Trace-ID header
"""


def _write_spec(tmp_path, content):
    specs = tmp_path / "specs"
    specs.mkdir(exist_ok=True)
    (specs / "logging-spec.md").write_text(content, encoding="utf-8")


def test_check_logging_spec_all_sections_pass(tmp_path):
    _write_spec(tmp_path, _GOOD_SPEC)
    results = check_logging_spec(str(tmp_path), ["web-app"])
    statuses = {r["check"]: r["status"] for r in results}
    assert statuses["section filled: Log Output Format"] == "pass"
    assert statuses["section filled: Required Log Points"] == "pass"
    assert statuses["section filled: Module Naming Convention"] == "pass"
    assert statuses["trace_id documented"] == "pass"


def test_check_logging_spec_sparse_section_warns(tmp_path):
    _write_spec(
        tmp_path,
        "## Log Output Format\njson\n\n"
        "## Required Log Points\nstart\nstop\nerror\n\n"
        "## Module Naming Convention\nfoo.bar\nexample: baz\nprefix: x.\n",
    )
    results = check_logging_spec(str(tmp_path), ["web-app"])
    log_fmt = [r for r in results if "Log Output Format" in r["check"]]
    assert any(r["status"] == "warn" for r in log_fmt)


def test_check_logging_spec_pipeline_row_count_warns_when_absent(tmp_path):
    _write_spec(
        tmp_path,
        "## Log Output Format\na\nb\nc\n"
        "## Required Log Points\na\nb\nc\n"
        "## Module Naming Convention\na\nb\nc\n"
        "trace_id: x\n",
    )
    results = check_logging_spec(str(tmp_path), ["data-pipeline"])
    checks = {r["check"]: r["status"] for r in results}
    assert checks["pipeline row count field"] == "warn"


def test_check_logging_spec_pipeline_row_count_passes_when_present(tmp_path):
    _write_spec(
        tmp_path,
        "## Log Output Format\na\nb\nc\n"
        "## Required Log Points\na\nb\nc\n"
        "## Module Naming Convention\na\nb\nc\n"
        "trace_id: x\nrow_count: int\n",
    )
    results = check_logging_spec(str(tmp_path), ["data-pipeline"])
    checks = {r["check"]: r["status"] for r in results}
    assert checks["pipeline row count field"] == "pass"


def test_check_logging_spec_llm_fields_warns_when_absent(tmp_path):
    _write_spec(
        tmp_path,
        "## Log Output Format\na\nb\nc\n"
        "## Required Log Points\na\nb\nc\n"
        "## Module Naming Convention\na\nb\nc\n",
    )
    results = check_logging_spec(str(tmp_path), ["llm-app"])
    checks = {r["check"]: r["status"] for r in results}
    assert checks["LLM call log fields"] == "warn"


def test_check_logging_spec_llm_fields_passes_when_present(tmp_path):
    _write_spec(
        tmp_path,
        "## Log Output Format\na\nb\nc\n"
        "## Required Log Points\na\nb\nc\n"
        "## Module Naming Convention\na\nb\nc\n"
        "model: gpt-4\ntoken: 256\n",
    )
    results = check_logging_spec(str(tmp_path), ["llm-app"])
    checks = {r["check"]: r["status"] for r in results}
    assert checks["LLM call log fields"] == "pass"


# ---------------------------------------------------------------------------
# check_module_log_file
# ---------------------------------------------------------------------------

def test_check_module_log_file_passes_clean_file(tmp_path):
    log = tmp_path / "log-auth.md"
    log.write_text('trace_id: abc\n{"key": "value"}\n', encoding="utf-8")
    results = check_module_log_file(str(log), ["web-app"])
    checks = {r["check"]: r["status"] for r in results}
    assert checks["trace_id"] == "pass"
    assert checks["structured format"] == "pass"
    assert checks["no raw print statements"] == "pass"


def test_check_module_log_file_fails_on_raw_print(tmp_path):
    log = tmp_path / "log-order.md"
    log.write_text('trace_id: abc\njson payload\nprint("hello")\n', encoding="utf-8")
    results = check_module_log_file(str(log), ["web-app"])
    checks = {r["check"]: r["status"] for r in results}
    assert checks["no raw print statements"] == "fail"


def test_check_module_log_file_warns_missing_trace_id(tmp_path):
    log = tmp_path / "log-order.md"
    log.write_text('{"key": "value"}\n', encoding="utf-8")
    results = check_module_log_file(str(log), ["web-app"])
    checks = {r["check"]: r["status"] for r in results}
    assert checks["trace_id"] == "warn"


def test_check_module_log_file_pipeline_row_count_passes(tmp_path):
    log = tmp_path / "log-extract.md"
    log.write_text('trace_id: abc\njson payload\nrow_count: 500\n', encoding="utf-8")
    results = check_module_log_file(str(log), ["data-pipeline"])
    checks = {r["check"]: r["status"] for r in results}
    assert checks["pipeline row count field"] == "pass"


def test_check_module_log_file_llm_fields_passes(tmp_path):
    log = tmp_path / "log-chat.md"
    log.write_text('model: gpt-4\ntoken: 1024\njson payload\n', encoding="utf-8")
    results = check_module_log_file(str(log), ["llm-app"])
    checks = {r["check"]: r["status"] for r in results}
    assert checks["LLM call log fields"] == "pass"
