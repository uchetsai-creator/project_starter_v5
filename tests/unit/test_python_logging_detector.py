import sys
import tempfile
from pathlib import Path

_ADAPTERS_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "templates" / "script" / "validators" / "_spec_code_adapters"
)
sys.path.insert(0, str(_ADAPTERS_DIR))

from python_logging import PythonLoggingDetector  # noqa: E402

sys.path.remove(str(_ADAPTERS_DIR))  # don't leak onto sys.path — see test_ansible_detector.py


def _extract(source: str):
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False, encoding="utf-8") as f:
        f.write(source)
        path = f.name
    try:
        return PythonLoggingDetector().extract([path])
    finally:
        Path(path).unlink()


def test_plain_string_log_call_is_extracted_with_canonical_level():
    src = '''
import logging
logger = logging.getLogger("ORDER")

def create_order():
    logger.info("create order — start")
'''
    points = _extract(src)
    assert len(points) == 1
    p = points[0]
    assert (p.function, p.operation, p.state, p.level) == ("create_order", "create order", "start", "info")


def test_warning_method_normalizes_to_canonical_warn_level():
    src = '''
def deduct_stock():
    logger.warning("deduct stock — warning: low inventory")
'''
    points = _extract(src)
    assert points[0].level == "warn"


def test_fstring_with_dynamic_reason_still_matches_static_prefix():
    src = '''
def create_order():
    reason = "insufficient stock"
    logger.error(f"create order — failed: {reason}")
'''
    points = _extract(src)
    assert len(points) == 1
    assert points[0].state.startswith("failed:")
    assert points[0].level == "error"


def test_call_outside_any_function_is_ignored():
    src = '''
logger.info("startup — start")
'''
    assert _extract(src) == []


def test_message_not_matching_operation_dash_state_convention_is_skipped():
    src = '''
def helper():
    logger.info("just a plain message with no convention")
'''
    assert _extract(src) == []


def test_multiple_functions_keep_log_points_attributed_correctly():
    src = '''
def create_order():
    logger.info("create order — start")

def cancel_order():
    logger.info("cancel order — start")
'''
    points = _extract(src)
    by_function = {p.function: p for p in points}
    assert set(by_function) == {"create_order", "cancel_order"}
