"""Golden drift-detection coverage for the logging adapters: python_logging,
javascript_logging. See tests/unit/test_adapter_drift_detection.py for the full
rationale. tests/unit/test_verify_spec_code_zero_coverage.py already covers the
zero-coverage edge case for the 'logging' capability adapter — this file covers the
actual drift-catching behavior of each language detector.
"""
import os
import subprocess
import sys
from pathlib import Path

_VALIDATORS_DIR = Path(__file__).resolve().parent.parent.parent / "templates/script/validators"
SCRIPT = _VALIDATORS_DIR / "verify_spec_code.py"


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env={**os.environ, "PYTHONUTF8": "1"},
    )


_LOG_SPEC = """\
| Function | Operation | State | Level |
|---|---|---|---|
| create_order | create order | start | info |
| create_order | create order | end: success | info |
"""


# ---------------------------------------------------------------------------
# python_logging
# ---------------------------------------------------------------------------

_PY_LOG_CODE_CLEAN = """\
import logging

logger = logging.getLogger("ORDERS")


def create_order():
    logger.info("create order — start")
    logger.info("create order — end: success")
"""


def test_python_logging_clean_spec_and_code_report_no_mismatches(tmp_path):
    spec = tmp_path / "log-orders.md"
    spec.write_text(_LOG_SPEC, encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    (src / "orders.py").write_text(_PY_LOG_CODE_CLEAN, encoding="utf-8")

    result = _run("--adapter", "python_logging", "--spec", str(spec), "--src", str(src), "--strict")
    assert "No mismatches" in result.stdout, result.stdout
    assert result.returncode == 0


def test_python_logging_missing_log_point_is_caught(tmp_path):
    spec = tmp_path / "log-orders.md"
    spec.write_text(_LOG_SPEC, encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    code = _PY_LOG_CODE_CLEAN.replace('    logger.info("create order — start")\n', "")
    (src / "orders.py").write_text(code, encoding="utf-8")

    result = _run("--adapter", "python_logging", "--spec", str(spec), "--src", str(src), "--strict")
    assert "[FAIL]" in result.stdout, result.stdout
    assert result.returncode == 1


def test_python_logging_level_change_is_caught(tmp_path):
    spec = tmp_path / "log-orders.md"
    spec.write_text(_LOG_SPEC, encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    # Drift: the "start" log point downgraded from .info() to .warning() in code,
    # contradicting the spec's declared "info" level.
    code = _PY_LOG_CODE_CLEAN.replace(
        'logger.info("create order — start")', 'logger.warning("create order — start")'
    )
    (src / "orders.py").write_text(code, encoding="utf-8")

    result = _run("--adapter", "python_logging", "--spec", str(spec), "--src", str(src), "--strict")
    assert "[FAIL]" in result.stdout, result.stdout
    assert "info" in result.stdout, result.stdout
    assert "warn" in result.stdout, result.stdout
    assert result.returncode == 1


def test_python_logging_message_not_matching_convention_is_not_detected(tmp_path):
    """A log call whose message doesn't follow '<operation> — <state>' is silently
    skipped (see python_logging.py docstring) — proves off-convention calls don't
    get fabricated into false log points."""
    spec = tmp_path / "log-orders.md"
    spec.write_text(_LOG_SPEC, encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    (src / "orders.py").write_text(
        'import logging\nlogger = logging.getLogger("ORDERS")\n\n\n'
        'def create_order():\n    logger.info("just a plain message")\n',
        encoding="utf-8",
    )

    result = _run("--adapter", "python_logging", "--spec", str(spec), "--src", str(src), "--strict")
    assert "[FAIL]" in result.stdout, result.stdout  # both spec log points report missing


# ---------------------------------------------------------------------------
# javascript_logging
# ---------------------------------------------------------------------------

_JS_LOG_CODE_CLEAN = """\
function createOrder() {
  logger.info("create order — start");
  logger.info("create order — end: success");
}
"""


def test_javascript_logging_clean_spec_and_code_report_no_mismatches(tmp_path):
    spec = tmp_path / "log-orders.md"
    spec.write_text(_LOG_SPEC.replace("create_order", "createOrder"), encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    (src / "orders.js").write_text(_JS_LOG_CODE_CLEAN, encoding="utf-8")

    result = _run("--adapter", "javascript_logging", "--spec", str(spec), "--src", str(src), "--strict")
    assert "No mismatches" in result.stdout, result.stdout
    assert result.returncode == 0


def test_javascript_logging_missing_log_point_is_caught(tmp_path):
    spec = tmp_path / "log-orders.md"
    spec.write_text(_LOG_SPEC.replace("create_order", "createOrder"), encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    code = _JS_LOG_CODE_CLEAN.replace('  logger.info("create order — start");\n', "")
    (src / "orders.js").write_text(code, encoding="utf-8")

    result = _run("--adapter", "javascript_logging", "--spec", str(spec), "--src", str(src), "--strict")
    assert "[FAIL]" in result.stdout, result.stdout
    assert result.returncode == 1


def test_javascript_logging_level_change_is_caught(tmp_path):
    spec = tmp_path / "log-orders.md"
    spec.write_text(_LOG_SPEC.replace("create_order", "createOrder"), encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    code = _JS_LOG_CODE_CLEAN.replace(
        'logger.info("create order — start");', 'logger.error("create order — start");'
    )
    (src / "orders.js").write_text(code, encoding="utf-8")

    result = _run("--adapter", "javascript_logging", "--spec", str(spec), "--src", str(src), "--strict")
    assert "[FAIL]" in result.stdout, result.stdout
    assert "info" in result.stdout, result.stdout
    assert "error" in result.stdout, result.stdout
    assert result.returncode == 1


def test_javascript_logging_arrow_function_scope_is_attributed_correctly(tmp_path):
    """A named arrow-function const is a valid scope declaration alongside
    `function name() {}` — proves the scope scanner recognizes both styles rather
    than only classic function declarations."""
    spec = tmp_path / "log-orders.md"
    spec.write_text(_LOG_SPEC.replace("create_order", "createOrder"), encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    (src / "orders.js").write_text(
        "const createOrder = () => {\n"
        '  logger.info("create order — start");\n'
        '  logger.info("create order — end: success");\n'
        "};\n",
        encoding="utf-8",
    )

    result = _run("--adapter", "javascript_logging", "--spec", str(spec), "--src", str(src), "--strict")
    assert "No mismatches" in result.stdout, result.stdout
    assert result.returncode == 0
