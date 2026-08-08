"""Golden drift-detection coverage for verify_spec_code.py's framework adapters.

The existing adapter tests (tests/contract/test_adapter_contracts.py) only check the
*interface* contract: extract_spec()/extract_code() never raise and return the right
NormalizedForm subclass. None of them feed a real spec + real code pair through the CLI
and assert that an actual, known drift is reported — the one thing this validator exists
to do. A regex/AST bug in an adapter's extract_spec()/extract_code() (or in compare()'s
handling of a NormalizedForm subclass) could silently stop catching drift and nothing
in the test suite would notice.

Each adapter below gets:
  1. a "clean" case — real spec + matching real code — asserting no false positive, and
  2. one or more drift cases — the same pair with a single known-planted mismatch —
     asserting verify_spec_code.py actually reports it and fails --strict.

Covers the three adapters most likely to see real usage: fastapi (web-api), click
(cli), langchain (llm-app). Follows the subprocess-CLI pattern already used by
tests/unit/test_verify_spec_code_zero_coverage.py.
"""
import os
import subprocess
import sys
from pathlib import Path

_VALIDATORS_DIR = Path(__file__).resolve().parent.parent.parent / "templates/script/validators"
SCRIPT = _VALIDATORS_DIR / "verify_spec_code.py"


def _run(*args: str) -> subprocess.CompletedProcess:
    # PYTHONUTF8 forces the child's own stdout/stderr encoding to UTF-8, matching the
    # encoding="utf-8" this decodes with — see golden test helpers for the full rationale.
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env={**os.environ, "PYTHONUTF8": "1"},
    )


# ---------------------------------------------------------------------------
# FastAPI (web-api)
# ---------------------------------------------------------------------------

_FASTAPI_SPEC = """\
### POST /orders
#### Request Body
| Field | Type | Required | Description |
|---|---|---|---|
| customer_id | int | Yes | Customer ID |
| item_count | int | Yes | Number of items |

#### Response Body
| Field | Type | Description |
|---|---|---|
| order_id | int | Order ID |
| status | string | Order status |
"""

_FASTAPI_CODE_CLEAN = """\
from fastapi import FastAPI

app = FastAPI()


class OrderResponse:
    order_id: int
    status: str


@app.post("/orders")
async def create_order(customer_id: int, item_count: int) -> OrderResponse:
    ...
"""


def test_fastapi_clean_spec_and_code_report_no_mismatches(tmp_path):
    spec = tmp_path / "api-contract.md"
    spec.write_text(_FASTAPI_SPEC, encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    (src / "orders.py").write_text(_FASTAPI_CODE_CLEAN, encoding="utf-8")

    result = _run("--adapter", "fastapi", "--spec", str(spec), "--src", str(src), "--strict")
    assert "No mismatches" in result.stdout, result.stdout
    assert result.returncode == 0


def test_fastapi_missing_request_field_is_caught(tmp_path):
    spec = tmp_path / "api-contract.md"
    spec.write_text(_FASTAPI_SPEC, encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    # Drift: item_count dropped from the handler's parameters.
    code = _FASTAPI_CODE_CLEAN.replace(", item_count: int", "")
    (src / "orders.py").write_text(code, encoding="utf-8")

    result = _run("--adapter", "fastapi", "--spec", str(spec), "--src", str(src), "--strict")
    assert "[FAIL]" in result.stdout, result.stdout
    assert "item_count" in result.stdout, result.stdout
    assert result.returncode == 1


def test_fastapi_response_field_type_change_is_caught(tmp_path):
    spec = tmp_path / "api-contract.md"
    spec.write_text(_FASTAPI_SPEC, encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    # Drift: status changed from str to int, contradicting the spec's "string".
    code = _FASTAPI_CODE_CLEAN.replace("status: str", "status: int")
    (src / "orders.py").write_text(code, encoding="utf-8")

    result = _run("--adapter", "fastapi", "--spec", str(spec), "--src", str(src), "--strict")
    assert "[FAIL]" in result.stdout, result.stdout
    assert "status" in result.stdout, result.stdout
    assert result.returncode == 1


# ---------------------------------------------------------------------------
# Click (cli)
# ---------------------------------------------------------------------------

_CLICK_SPEC = """\
### `mytool build`
#### Flags
| Flag | Short | Type | Default | Description |
|---|---|---|---|---|
| `--output` | `-o` | string | stdout | Output path |
| `--verbose` | `-v` | bool | false | Verbose output |
"""

_CLICK_CODE_CLEAN = """\
import click


@click.command()
@click.option('--output', '-o', type=str)
@click.option('--verbose', '-v', is_flag=True)
def build(output, verbose):
    ...
"""


def test_click_clean_spec_and_code_report_no_mismatches(tmp_path):
    spec = tmp_path / "cli-contract.md"
    spec.write_text(_CLICK_SPEC, encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    (src / "cli.py").write_text(_CLICK_CODE_CLEAN, encoding="utf-8")

    result = _run("--adapter", "click", "--spec", str(spec), "--src", str(src), "--strict")
    assert "No mismatches" in result.stdout, result.stdout
    assert result.returncode == 0


def test_click_missing_flag_is_caught(tmp_path):
    spec = tmp_path / "cli-contract.md"
    spec.write_text(_CLICK_SPEC, encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    # Drift: --verbose dropped from the command entirely.
    code = _CLICK_CODE_CLEAN.replace("@click.option('--verbose', '-v', is_flag=True)\n", "")
    code = code.replace("def build(output, verbose):", "def build(output):")
    (src / "cli.py").write_text(code, encoding="utf-8")

    result = _run("--adapter", "click", "--spec", str(spec), "--src", str(src), "--strict")
    assert "[FAIL]" in result.stdout, result.stdout
    assert "verbose" in result.stdout, result.stdout
    assert result.returncode == 1


def test_click_flag_type_change_is_caught(tmp_path):
    spec = tmp_path / "cli-contract.md"
    spec.write_text(_CLICK_SPEC, encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    # Drift: --output changed from a string type to an int type, contradicting the spec.
    code = _CLICK_CODE_CLEAN.replace("type=str", "type=int")
    (src / "cli.py").write_text(code, encoding="utf-8")

    result = _run("--adapter", "click", "--spec", str(spec), "--src", str(src), "--strict")
    assert "[FAIL]" in result.stdout, result.stdout
    assert "output" in result.stdout, result.stdout
    assert result.returncode == 1


# ---------------------------------------------------------------------------
# LangChain (llm-app)
# ---------------------------------------------------------------------------

_LANGCHAIN_SPEC = """\
### get_weather
#### Parameters
| Name | Type | Required | Description |
|---|---|---|---|
| city | string | Yes | City name |
"""

_LANGCHAIN_CODE_CLEAN = """\
from langchain_core.tools import tool


@tool
def get_weather(city: str) -> str:
    \"\"\"Get the current weather for a city.\"\"\"
    return f"Weather in {city}"
"""


def test_langchain_clean_spec_and_code_report_no_mismatches(tmp_path):
    spec = tmp_path / "llm-contract.md"
    spec.write_text(_LANGCHAIN_SPEC, encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    (src / "tools.py").write_text(_LANGCHAIN_CODE_CLEAN, encoding="utf-8")

    result = _run("--adapter", "langchain", "--spec", str(spec), "--src", str(src), "--strict")
    assert "No mismatches" in result.stdout, result.stdout
    assert result.returncode == 0


def test_langchain_renamed_parameter_is_caught_both_ways(tmp_path):
    spec = tmp_path / "llm-contract.md"
    spec.write_text(_LANGCHAIN_SPEC, encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    # Drift: the spec's "city" parameter was renamed to "location" in code only —
    # this must surface as both a removed field (city) and an added field (location),
    # not silently cancel out.
    code = _LANGCHAIN_CODE_CLEAN.replace("city", "location")
    (src / "tools.py").write_text(code, encoding="utf-8")

    result = _run("--adapter", "langchain", "--spec", str(spec), "--src", str(src), "--strict")
    assert "[FAIL]" in result.stdout, result.stdout
    assert "city" in result.stdout, result.stdout
    assert "location" in result.stdout, result.stdout
    assert result.returncode == 1
