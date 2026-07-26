import sys
import tempfile
from pathlib import Path

_ADAPTERS_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "templates" / "script" / "validators" / "_spec_code_adapters"
)
sys.path.insert(0, str(_ADAPTERS_DIR))

from typescript import TypescriptDetector  # noqa: E402


def _extract(source: str):
    with tempfile.NamedTemporaryFile(suffix=".ts", mode="w", delete=False, encoding="utf-8") as f:
        f.write(source)
        path = f.name
    try:
        return TypescriptDetector().extract([path])
    finally:
        Path(path).unlink()


def test_export_function_declaration():
    src = """
export function add(a: number, b: number): number {
  return a + b;
}
"""
    functions = _extract(src)
    assert len(functions) == 1
    assert functions[0].name == "add"
    assert {f.name: f.type for f in functions[0].params} == {"a": "number", "b": "number"}
    assert functions[0].return_type == "number"


def test_export_const_arrow_function():
    src = """
export const greet = (name: string, loud?: boolean): string => {
  return name;
};
"""
    functions = _extract(src)
    assert functions[0].name == "greet"
    assert {f.name: f.type for f in functions[0].params} == {"name": "string", "loud": "boolean"}


def test_arrow_function_with_direct_expression_body_no_braces():
    src = """
export const double = (x: number): number => x * 2;
"""
    functions = _extract(src)
    assert functions[0].name == "double"
    assert functions[0].return_type == "number"


def test_barrel_reexport_with_alias_uses_the_public_alias_name():
    src = """
function internalMultiply(a: number, b: number): number {
  return a * b;
}

export { internalMultiply as multiply };
"""
    functions = _extract(src)
    names = {f.name for f in functions}
    assert "multiply" in names
    assert "internalMultiply" not in names


def test_function_not_exported_and_not_in_barrel_is_ignored():
    src = """
function helper(x: number): number {
  return x;
}
"""
    assert _extract(src) == []


def test_nested_generic_and_callback_parameter_types_do_not_break_param_split():
    src = """
export function process(items: Array<string>, cb: (x: number) => void): void {
}
"""
    functions = _extract(src)
    params = {f.name: f.type for f in functions[0].params}
    assert params["items"] == "Array<string>"
    assert params["cb"] == "(x: number) => void"


def test_default_value_after_type_is_stripped_correctly():
    src = """
export function connect(host: string = "localhost", port: number = 8080): void {
}
"""
    functions = _extract(src)
    params = {f.name: f.type for f in functions[0].params}
    assert params == {"host": "string", "port": "number"}
