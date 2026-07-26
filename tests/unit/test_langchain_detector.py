import sys
import tempfile
from pathlib import Path

_ADAPTERS_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "templates" / "script" / "validators" / "_spec_code_adapters"
)
sys.path.insert(0, str(_ADAPTERS_DIR))

from langchain import LangchainDetector  # noqa: E402


def _extract(source: str):
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False, encoding="utf-8") as f:
        f.write(source)
        path = f.name
    try:
        return LangchainDetector().extract([path])
    finally:
        Path(path).unlink()


def test_bare_tool_decorator_uses_function_name():
    src = """
from langchain_core.tools import tool

@tool
def get_weather(city: str) -> str:
    return city
"""
    tools = _extract(src)
    assert len(tools) == 1
    assert tools[0].name == "get_weather"
    assert {f.name: f.type for f in tools[0].parameters} == {"city": "str"}


def test_tool_decorator_with_string_arg_overrides_name():
    src = """
from langchain_core.tools import tool

@tool("web_search")
def search(query: str):
    return []
"""
    tools = _extract(src)
    assert tools[0].name == "web_search"


def test_function_without_tool_decorator_is_ignored_even_with_type_hints():
    src = """
def helper(x: int) -> int:
    return x
"""
    assert _extract(src) == []


def test_undecorated_helper_next_to_a_real_tool_is_not_detected():
    """Regression check for the precision gap vs. tool_schema.py's blanket
    'any function with type hints' heuristic."""
    src = """
from langchain_core.tools import tool

@tool
def get_weather(city: str) -> str:
    return city

def format_response(data: dict) -> str:
    return str(data)
"""
    tools = _extract(src)
    assert {t.name for t in tools} == {"get_weather"}


def test_module_qualified_tool_decorator_is_recognized():
    src = """
import langchain_core.tools as lc_tools

@lc_tools.tool
def ping(host: str) -> bool:
    return True
"""
    tools = _extract(src)
    assert tools[0].name == "ping"
