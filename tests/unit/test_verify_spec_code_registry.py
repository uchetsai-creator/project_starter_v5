import sys
import tempfile
from pathlib import Path

_VALIDATORS_DIR = Path(__file__).resolve().parent.parent.parent / "templates/script/validators"
sys.path.insert(0, str(_VALIDATORS_DIR))

import verify_spec_code as vsc  # noqa: E402


def test_logging_adapter_registry_entry_has_no_framework_hint():
    # Every other capability (web-api, cli, data-pipeline, ...) has a bare capability-name
    # entry with a None hint that unions all its detectors — 'logging' must follow the same
    # pattern, not just the python_logging / javascript_logging per-language aliases.
    assert 'logging' in vsc.ADAPTER_REGISTRY
    module_name, class_name, hint = vsc.ADAPTER_REGISTRY['logging']
    assert hint is None
    assert class_name == 'LoggingAdapter'


def test_logging_adapter_without_hint_unions_python_and_javascript_detectors():
    adapter = vsc._load_adapter('logging')

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        (tmp_path / "order.py").write_text(
            'import logging\n'
            'logger = logging.getLogger("ORDER")\n'
            'def create_order():\n'
            '    logger.info("create order — start")\n',
            encoding='utf-8',
        )
        (tmp_path / "cart.tsx").write_text(
            'function renderCart() {\n'
            '    logger.info("render cart — start");\n'
            '}\n',
            encoding='utf-8',
        )
        results = adapter.extract_code(str(tmp_path))

    functions = {r.function for r in results}
    assert functions == {'create_order', 'renderCart'}
