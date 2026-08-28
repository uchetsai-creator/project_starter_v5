import sys
import tempfile
from pathlib import Path

import pytest

_ADAPTERS_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "templates" / "script" / "validators" / "_spec_code_adapters"
)
sys.path.insert(0, str(_ADAPTERS_DIR))

from javascript_logging import JavaScriptLoggingDetector  # noqa: E402

sys.path.remove(str(_ADAPTERS_DIR))  # don't leak onto sys.path — see test_ansible_detector.py


def _extract(source: str, suffix=".ts"):
    with tempfile.NamedTemporaryFile(suffix=suffix, mode="w", delete=False, encoding="utf-8") as f:
        f.write(source)
        path = f.name
    try:
        return JavaScriptLoggingDetector().extract([path])
    finally:
        Path(path).unlink()


def test_function_declaration_plain_string():
    src = '''
function createOrder(userId) {
    logger.info("create order — start");
}
'''
    points = _extract(src)
    assert len(points) == 1
    p = points[0]
    assert (p.function, p.operation, p.state, p.level) == ("createOrder", "create order", "start", "info")


def test_arrow_function_const_assignment():
    src = '''
const createOrder = (userId) => {
    logger.info("create order — start");
};
'''
    points = _extract(src)
    assert len(points) == 1
    assert points[0].function == "createOrder"


def test_typescript_class_method_with_modifiers_and_return_type():
    src = '''
class OrderService {
    private async createOrder(userId: string): Promise<void> {
        logger.info("create order — start");
    }
}
'''
    points = _extract(src)
    assert len(points) == 1
    assert points[0].function == "createOrder"


def test_warn_and_warning_methods_normalize_to_canonical_warn():
    src = '''
function deductStock() {
    logger.warning("deduct stock — warning: low inventory");
}
'''
    points = _extract(src)
    assert points[0].level == "warn"


def test_template_literal_with_interpolation_still_matches_static_prefix():
    src = '''
function createOrder() {
    const reason = "insufficient stock";
    logger.error(`create order — failed: ${reason}`);
}
'''
    points = _extract(src)
    assert len(points) == 1
    assert points[0].state.startswith("failed:")
    assert points[0].level == "error"


def test_anonymous_callback_attributes_to_enclosing_named_function():
    src = '''
function HomeScreen() {
    useEffect(() => {
        logger.info("home screen — start");
    }, []);
}
'''
    points = _extract(src, suffix=".tsx")
    assert len(points) == 1
    assert points[0].function == "HomeScreen"


def test_module_level_call_is_ignored():
    src = '''
logger.info("startup — start");
'''
    assert _extract(src) == []


def test_control_flow_block_is_not_treated_as_a_function():
    src = '''
function createOrder(itemCount) {
    if (itemCount > 0) {
        logger.info("create order — start");
    }
}
'''
    points = _extract(src)
    assert len(points) == 1
    assert points[0].function == "createOrder"


def test_message_not_matching_convention_is_skipped():
    src = '''
function helper() {
    logger.info("just a plain message with no convention");
}
'''
    assert _extract(src) == []


@pytest.mark.parametrize("suffix", [".js", ".jsx", ".ts", ".tsx"])
def test_all_supported_extensions_are_parsed(suffix):
    src = '''
function createOrder() {
    logger.info("create order — start");
}
'''
    points = _extract(src, suffix=suffix)
    assert len(points) == 1
