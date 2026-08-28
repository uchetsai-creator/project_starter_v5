"""Tests for generate_openapi.py — generates OpenAPI 3.0 from api-contract.md by reusing
WebAPIAdapter.extract_spec() (the same parser verify_spec_code.py already uses), rather
than re-parsing the markdown independently.

Includes a regression test for a real bug found while building this: the shipped
api-contract.md template used a heading format (## `METHOD /path`, level 2 + backticks)
that WebAPIAdapter.extract_spec() cannot parse at all (it requires ### METHOD /path,
level 3, no backticks) — confirmed by comparing against
examples/microservices-web-app/docs/specs/api-contract.md, which happened to already use
the working format. A second, related bug: the Validation Rules / Errors sections used
bold text (**Errors:**) instead of #### headings, so _parse_field_table()'s "read until
next #### heading" boundary had nothing to stop at and pulled unrelated table rows in as
if they were request/response fields. Both are fixed in templates/specs/api-contract.md;
these tests lock the fix in.
"""
import importlib.util
import os
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_SCRIPT_PATH = _REPO_ROOT / "templates" / "script" / "generators" / "generate_openapi.py"
_TEMPLATE_SPEC = _REPO_ROOT / "templates" / "specs" / "api-contract.md"
_EXAMPLE_SPEC = (
    _REPO_ROOT / "examples" / "microservices-web-app" / "docs" / "specs" / "api-contract.md"
)

_spec = importlib.util.spec_from_file_location("generate_openapi", _SCRIPT_PATH)
assert _spec is not None and _spec.loader is not None
go = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(go)

# go's own module-level code already inserted _spec_code_adapters/ into sys.path
# (needed for its `from _capability_web_api import WebAPIAdapter`), so _base is
# importable here too, cleanly, instead of reaching into WebAPIAdapter's module.
from _base import NormalizedEndpoint, NormalizedField  # noqa: E402

# Undo go's own sys.path.insert (see generate_openapi.py) now that both imports above
# are done — leaving it in place would leak _spec_code_adapters/ onto sys.path for the
# rest of this pytest session (loading a script via exec_module, unlike running it as
# its own subprocess, shares this process's sys.path with every other test module —
# see CHANGELOG.md's [Unreleased] "Fixed" entry for the concrete bug this caused).
# extract_spec() (the only go.WebAPIAdapter method this file calls) parses spec
# markdown only — no framework-specific detector dispatch, so it needs no path access
# beyond this import; empirically confirmed by this file's own test run below.
sys.path.remove(os.path.abspath(go._ADAPTER_DIR))

# ---------------------------------------------------------------------------
# _to_openapi_path
# ---------------------------------------------------------------------------

def test_colon_param_converted_to_curly_braces():
    assert go._to_openapi_path("/orders/:id") == "/orders/{id}"


def test_already_curly_brace_path_is_unchanged():
    assert go._to_openapi_path("/orders/{id}") == "/orders/{id}"


def test_multiple_params_all_converted():
    assert go._to_openapi_path("/a/:x/b/:y") == "/a/{x}/b/{y}"


def test_path_with_no_params_is_unchanged():
    assert go._to_openapi_path("/orders") == "/orders"


# ---------------------------------------------------------------------------
# _openapi_type
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("raw,expected", [
    ("string", "string"), ("str", "string"), ("uuid", "string"),
    ("int", "integer"), ("integer", "integer"), ("long", "integer"),
    ("float", "number"), ("double", "number"),
    ("bool", "boolean"), ("boolean", "boolean"),
    ("array", "array"), ("list", "array"),
    ("object", "object"), ("dict", "object"),
])
def test_known_type_aliases_map_correctly(raw, expected):
    otype, original = go._openapi_type(raw)
    assert otype == expected
    assert original is None


def test_unknown_type_falls_back_to_string_with_original_preserved():
    otype, original = go._openapi_type("SomeCustomEnum")
    assert otype == "string"
    assert original == "SomeCustomEnum"


def test_optional_wrapper_is_stripped():
    otype, _ = go._openapi_type("Optional[int]")
    assert otype == "integer"


# ---------------------------------------------------------------------------
# build_openapi — status code defaults, request body inclusion, path conversion
# ---------------------------------------------------------------------------

def _endpoint(method, path, request_fields=None, response_fields=None):
    return NormalizedEndpoint(
        method=method, path=path,
        request_fields=request_fields or [], response_fields=response_fields or [],
    )


def test_post_gets_201_and_request_body():
    ep = _endpoint("POST", "/orders", request_fields=[NormalizedField(name="customer_id", type="string")])
    doc = go.build_openapi([ep], "T", "1.0.0")
    op = doc["paths"]["/orders"]["post"]
    assert "201" in op["responses"]
    assert op["requestBody"]["content"]["application/json"]["schema"]["properties"]["customer_id"]["type"] == "string"


def test_get_gets_200_and_no_request_body():
    ep = _endpoint("GET", "/orders")
    doc = go.build_openapi([ep], "T", "1.0.0")
    op = doc["paths"]["/orders"]["get"]
    assert "200" in op["responses"]
    assert "requestBody" not in op


def test_delete_gets_204_with_no_content_body_even_if_response_fields_present():
    ep = _endpoint("DELETE", "/orders/:id", response_fields=[NormalizedField(name="id", type="string")])
    doc = go.build_openapi([ep], "T", "1.0.0")
    op = doc["paths"]["/orders/{id}"]["delete"]
    assert op["responses"]["204"] == {"description": "No Content"}


def test_path_param_converted_in_output_paths():
    ep = _endpoint("GET", "/orders/:id")
    doc = go.build_openapi([ep], "T", "1.0.0")
    assert "/orders/{id}" in doc["paths"]
    assert "/orders/:id" not in doc["paths"]


def test_two_methods_same_path_both_present():
    ep1 = _endpoint("GET", "/orders")
    ep2 = _endpoint("POST", "/orders")
    doc = go.build_openapi([ep1, ep2], "T", "1.0.0")
    assert set(doc["paths"]["/orders"].keys()) == {"get", "post"}


def test_openapi_document_has_required_top_level_keys():
    doc = go.build_openapi([], "My API", "2.0.0")
    assert doc["openapi"] == "3.0.3"
    assert doc["info"] == {"title": "My API", "version": "2.0.0"}
    assert doc["paths"] == {}


# ---------------------------------------------------------------------------
# Real files — regression coverage for the heading-format bug
# ---------------------------------------------------------------------------

def test_shipped_template_produces_five_endpoints():
    endpoints = go.WebAPIAdapter().extract_spec(str(_TEMPLATE_SPEC))
    assert len(endpoints) == 5
    methods = sorted((e.method, e.path) for e in endpoints)
    assert ("DELETE", "/[resource]/:id") in methods
    assert ("PATCH", "/[resource]/:id") in methods


def test_shipped_template_post_endpoint_has_real_field_schemas_not_bled_content():
    """Regression: Validation Rules / Errors tables must not leak into request/response
    fields — this was a real bug (HTTP/400/401 rows appearing as response 'fields')."""
    endpoints = go.WebAPIAdapter().extract_spec(str(_TEMPLATE_SPEC))
    post = next(e for e in endpoints if e.method == "POST")
    response_names = {f.name for f in post.response_fields}
    assert response_names == {"id", "[field]", "created_at"}
    assert "HTTP" not in response_names
    assert "400" not in response_names


def test_working_example_produces_two_endpoints_with_real_fields():
    endpoints = go.WebAPIAdapter().extract_spec(str(_EXAMPLE_SPEC))
    assert len(endpoints) == 2
    post = next(e for e in endpoints if e.method == "POST")
    assert {f.name for f in post.request_fields} == {"customer_id", "items"}


# ---------------------------------------------------------------------------
# CLI behavior
# ---------------------------------------------------------------------------

def _run(*args: str) -> subprocess.CompletedProcess:
    import os
    return subprocess.run(
        [sys.executable, str(_SCRIPT_PATH), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env={**os.environ, "PYTHONUTF8": "1"},
    )


def test_cli_missing_spec_file_errors():
    result = _run("--spec", "/does/not/exist.md")
    assert result.returncode == 2


def test_cli_no_endpoints_warns_and_exits_zero(tmp_path):
    spec = tmp_path / "empty.md"
    spec.write_text("# API Contract\n\nNothing here.\n", encoding="utf-8")
    result = _run("--spec", str(spec))
    assert result.returncode == 0
    assert "nothing to generate" in result.stdout


def test_cli_generates_valid_yaml_from_shipped_template(tmp_path):
    output = tmp_path / "openapi.yaml"
    result = _run("--spec", str(_TEMPLATE_SPEC), "--output", str(output), "--title", "T")
    assert result.returncode == 0
    assert output.exists()
    doc = yaml.safe_load(output.read_text(encoding="utf-8"))
    assert doc["openapi"] == "3.0.3"
    assert len(doc["paths"]) == 2  # /[resource] and /[resource]/{id}
