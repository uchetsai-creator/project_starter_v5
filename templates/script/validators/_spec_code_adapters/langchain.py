"""
langchain.py — LangchainDetector for project_starter_v5.

Extracts NormalizedTool objects from LangChain tool code:
  - Code: functions decorated with `@tool` (bare) or `@tool("name", ...)`
    (langchain_core.tools.tool / langchain.tools.tool). Only decorated
    functions count. This is a real precision improvement over
    tool_schema.py's approach (any type-annotated, non-underscore-prefixed
    function in the file is treated as a tool) — LangChain has an explicit
    decorator marking a function as agent-callable, so a plain helper
    function sitting next to a tool in the same file should not be reported
    as one just because it also has type hints.
  - `@tool("custom_name")`'s positional string argument overrides the tool's
    exposed name, the same way Typer's `typer.Option("--flag")` overrides a
    derived CLI flag name — the decorator's own explicit name always wins
    over the function's Python identifier.
  - Spec: llm-contract.md — shared llm-app format, parsed by LLMAdapter, not here.
"""
from __future__ import annotations

import ast

from _base import Detector, NormalizedField, NormalizedTool
from _utils import _annotation_str

_SKIP_PARAMS = frozenset({'self', 'cls', 'kwargs', 'args'})


def _is_tool_decorator(dec) -> bool:
    if isinstance(dec, ast.Name):
        return dec.id == 'tool'
    if isinstance(dec, ast.Attribute):
        return dec.attr == 'tool'
    if isinstance(dec, ast.Call):
        return _is_tool_decorator(dec.func)
    return False


class LangchainDetector(Detector):
    """
    Framework detector for LangChain tools (llm-app).
    Receives pre-discovered .py files from LLMAdapter. Must not perform file discovery.
    """

    def extract(self, files: list[str]) -> list[NormalizedTool]:
        tools: list[NormalizedTool] = []
        for fpath in files:
            if fpath.endswith('.py'):
                tools.extend(self._parse_file(fpath))
        return tools

    def _parse_file(self, fpath: str) -> list[NormalizedTool]:
        try:
            with open(fpath, encoding='utf-8') as f:
                source = f.read()
            tree = ast.parse(source, filename=fpath)
        except (OSError, SyntaxError):
            return []

        tools: list[NormalizedTool] = []
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue

            tool_dec = next((d for d in node.decorator_list if _is_tool_decorator(d)), None)
            if tool_dec is None:
                continue

            tool_name = node.name
            if isinstance(tool_dec, ast.Call) and tool_dec.args:
                first = tool_dec.args[0]
                if isinstance(first, ast.Constant) and isinstance(first.value, str):
                    tool_name = first.value

            params = [
                NormalizedField(name=a.arg, type=_annotation_str(a.annotation))
                for a in node.args.args
                if a.arg not in _SKIP_PARAMS
            ]

            tools.append(NormalizedTool(name=tool_name, parameters=params))

        return tools


if __name__ == '__main__':
    import tempfile
    from pathlib import Path

    src = '''
from langchain_core.tools import tool

@tool
def get_weather(city: str) -> str:
    """Get the current weather for a city."""
    return f"Weather in {city}"

@tool("web_search")
def search(query: str, max_results: int = 5) -> list:
    """Search the web."""
    return []

def helper_not_a_tool(x: int) -> int:
    """Has type hints, but no @tool decorator — must not be detected."""
    return x
'''

    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False, encoding="utf-8") as f:
        f.write(src)
        path = f.name

    try:
        detector = LangchainDetector()
        assert detector.extract([]) == [], "extract([]) must return an empty list"

        tools = detector.extract([path])
        by_name = {t.name: t for t in tools}

        assert "get_weather" in by_name, tools
        assert "web_search" in by_name, tools          # @tool("web_search") overrides def search
        assert "search" not in by_name, tools
        assert "helper_not_a_tool" not in by_name, tools

        assert {f.name: f.type for f in by_name["get_weather"].parameters} == {"city": "str"}
        search_params = {f.name: f.type for f in by_name["web_search"].parameters}
        assert search_params == {"query": "str", "max_results": "int"}
        assert len(tools) == 2
    finally:
        Path(path).unlink()

    print("[OK] langchain.py self-test passed")
