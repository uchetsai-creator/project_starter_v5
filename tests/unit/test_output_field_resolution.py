import ast
import sys
from pathlib import Path

_ADAPTERS_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "templates" / "script" / "validators" / "_spec_code_adapters"
)
sys.path.insert(0, str(_ADAPTERS_DIR))

from _utils import _resolve_output_fields  # noqa: E402

sys.path.remove(str(_ADAPTERS_DIR))  # don't leak onto sys.path — see test_ansible_detector.py


def _fields(source: str, func_name: str = "handler"):
    tree = ast.parse(source)
    func_node = next(
        n for n in ast.walk(tree)
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n.name == func_name
    )
    return {f.name: f.type for f in _resolve_output_fields(tree, func_node)}


def test_resolves_class_defined_in_same_file():
    src = '''
class HealthResponse:
    status: str
    code: int

def handler() -> HealthResponse:
    return HealthResponse(status="ok", code=200)
'''
    assert _fields(src) == {"status": "str", "code": "int"}


def test_resolves_bare_dict_literal_when_no_class_matches():
    src = '''
def handler() -> dict:
    return {"status": "ok", "count": 3}
'''
    assert _fields(src) == {"status": "str", "count": "int"}


def test_resolves_jsonify_wrapped_dict():
    src = '''
def handler():
    return jsonify({"status": "ok"})
'''
    assert _fields(src) == {"status": "str"}


def test_resolves_tuple_status_code_pattern():
    src = '''
def handler():
    return {"status": "ok"}, 200
'''
    assert _fields(src) == {"status": "str"}


def test_resolves_constructor_call_without_class_definition_in_file():
    """A Pydantic model imported from elsewhere (not defined in this file) should
    still resolve via its constructor's keyword arguments."""
    src = '''
def handler() -> HealthResponse:
    return HealthResponse(status="ok")
'''
    assert _fields(src) == {"status": "str"}


def test_bare_scalar_return_resolves_to_no_fields():
    src = '''
def handler() -> float:
    return 1.5
'''
    assert _fields(src) == {}


def test_no_return_statement_resolves_to_no_fields():
    src = '''
def handler() -> None:
    pass
'''
    assert _fields(src) == {}
