"""Golden drift-detection coverage for python_library and tool_schema (langchain is
covered in tests/unit/test_adapter_drift_detection.py). See that file for the full
rationale.
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


# ---------------------------------------------------------------------------
# python_library
# ---------------------------------------------------------------------------

_LIBRARY_SPEC = """\
### parse_config
#### Parameters
| Name | Type | Description |
|---|---|---|
| path | str | Config file path |

#### Returns
| Type | Description |
|---|---|
| dict | Parsed configuration |
"""

_LIBRARY_CODE_CLEAN = """\
__all__ = ["parse_config"]


def parse_config(path: str) -> dict:
    ...


def _internal_helper(path: str) -> dict:
    ...
"""


def test_python_library_clean_spec_and_code_report_no_mismatches(tmp_path):
    spec = tmp_path / "public-api.md"
    spec.write_text(_LIBRARY_SPEC, encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    (src / "config.py").write_text(_LIBRARY_CODE_CLEAN, encoding="utf-8")

    result = _run("--adapter", "python_library", "--spec", str(spec), "--src", str(src), "--strict")
    assert "No mismatches" in result.stdout, result.stdout
    assert result.returncode == 0


def test_python_library_missing_param_is_caught(tmp_path):
    spec = tmp_path / "public-api.md"
    spec.write_text(_LIBRARY_SPEC, encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    code = _LIBRARY_CODE_CLEAN.replace("def parse_config(path: str) -> dict:", "def parse_config() -> dict:")
    (src / "config.py").write_text(code, encoding="utf-8")

    result = _run("--adapter", "python_library", "--spec", str(spec), "--src", str(src), "--strict")
    assert "[FAIL]" in result.stdout, result.stdout
    assert "path" in result.stdout, result.stdout
    assert result.returncode == 1


def test_python_library_return_type_change_is_caught(tmp_path):
    spec = tmp_path / "public-api.md"
    spec.write_text(_LIBRARY_SPEC, encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    code = _LIBRARY_CODE_CLEAN.replace("-> dict:", "-> str:")
    (src / "config.py").write_text(code, encoding="utf-8")

    result = _run("--adapter", "python_library", "--spec", str(spec), "--src", str(src), "--strict")
    assert "[FAIL]" in result.stdout, result.stdout
    assert "return" in result.stdout, result.stdout
    assert result.returncode == 1


def test_python_library_function_not_in_all_is_not_detected(tmp_path):
    """A function present in code but left out of a non-empty __all__ is private by
    this detector's convention — proves __all__ actually gates detection rather than
    every def being treated as public. (Note: an *empty* __all__ = [] is falsy and
    falls back to "no __all__ declared" behavior — every non-underscore-prefixed
    function counts as public — so this test uses a non-empty __all__ that simply
    omits parse_config, the only way to actually exercise the gate.)"""
    spec = tmp_path / "public-api.md"
    spec.write_text(_LIBRARY_SPEC, encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    # Drift: parse_config silently dropped from __all__ (still defined, now "private").
    code = _LIBRARY_CODE_CLEAN.replace('__all__ = ["parse_config"]', '__all__ = ["other_function"]')
    (src / "config.py").write_text(code, encoding="utf-8")

    result = _run("--adapter", "python_library", "--spec", str(spec), "--src", str(src), "--strict")
    assert "[FAIL]" in result.stdout, result.stdout
    assert "parse_config" in result.stdout, result.stdout
    assert result.returncode == 1


# ---------------------------------------------------------------------------
# tool_schema
# ---------------------------------------------------------------------------

_TOOL_SCHEMA_SPEC = """\
### get_weather
#### Parameters
| Name | Type | Required | Description |
|---|---|---|---|
| city | string | Yes | City name |
"""

_TOOL_SCHEMA_CODE_CLEAN = """\
def get_weather(city: str) -> str:
    return f"Weather in {city}"
"""


def test_tool_schema_clean_python_spec_and_code_report_no_mismatches(tmp_path):
    spec = tmp_path / "llm-contract.md"
    spec.write_text(_TOOL_SCHEMA_SPEC, encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    (src / "tools.py").write_text(_TOOL_SCHEMA_CODE_CLEAN, encoding="utf-8")

    result = _run("--adapter", "tool_schema", "--spec", str(spec), "--src", str(src), "--strict")
    assert "No mismatches" in result.stdout, result.stdout
    assert result.returncode == 0


def test_tool_schema_renamed_python_param_is_caught(tmp_path):
    spec = tmp_path / "llm-contract.md"
    spec.write_text(_TOOL_SCHEMA_SPEC, encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    code = _TOOL_SCHEMA_CODE_CLEAN.replace("city", "location")
    (src / "tools.py").write_text(code, encoding="utf-8")

    result = _run("--adapter", "tool_schema", "--spec", str(spec), "--src", str(src), "--strict")
    assert "[FAIL]" in result.stdout, result.stdout
    assert "city" in result.stdout, result.stdout
    assert result.returncode == 1


def test_tool_schema_clean_json_spec_and_code_report_no_mismatches(tmp_path):
    spec = tmp_path / "llm-contract.md"
    spec.write_text(_TOOL_SCHEMA_SPEC, encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    (src / "tools.json").write_text(
        '[{"name": "get_weather", "parameters": {"properties": '
        '{"city": {"type": "string"}}}}]',
        encoding="utf-8",
    )

    result = _run("--adapter", "tool_schema", "--spec", str(spec), "--src", str(src), "--strict")
    assert "No mismatches" in result.stdout, result.stdout
    assert result.returncode == 0


def test_tool_schema_json_missing_param_is_caught(tmp_path):
    spec = tmp_path / "llm-contract.md"
    spec.write_text(_TOOL_SCHEMA_SPEC, encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    (src / "tools.json").write_text(
        '[{"name": "get_weather", "parameters": {"properties": {}}}]',
        encoding="utf-8",
    )

    result = _run("--adapter", "tool_schema", "--spec", str(spec), "--src", str(src), "--strict")
    assert "[FAIL]" in result.stdout, result.stdout
    assert "city" in result.stdout, result.stdout
    assert result.returncode == 1
