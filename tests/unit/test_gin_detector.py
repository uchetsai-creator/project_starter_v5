"""Unit tests for GinDetector (Go / Gin) in _spec_code_adapters/gin.py.

Requires the optional tree-sitter + tree-sitter-go packages (pip install tree-sitter
tree-sitter-go) — same opt-in treatment as bandit/eslint-plugin-security in
verify_security.py. Tests that need real Go parsing are individually skipped when
either package is missing, so CI doesn't need Go tooling installed to pass; the
graceful-degradation path itself (no crash, [] returned, install instructions
printed) is tested unconditionally, since that's the one behavior that must hold
in exactly the environment where the packages are absent.
"""
import importlib.util
import sys
from pathlib import Path

import pytest

_ADAPTERS_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "templates" / "script" / "validators" / "_spec_code_adapters"
)
sys.path.insert(0, str(_ADAPTERS_DIR))

_spec = importlib.util.spec_from_file_location("gin", _ADAPTERS_DIR / "gin.py")
assert _spec is not None and _spec.loader is not None
gin = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gin)

_TREE_SITTER_AVAILABLE = gin._get_parser() is not None
# Applied per-test (not as a module-wide pytestmark) so
# test_missing_tree_sitter_returns_empty_not_raises still runs even when tree-sitter
# isn't installed — that's the one test meant to cover exactly that environment.
requires_tree_sitter = pytest.mark.skipif(
    not _TREE_SITTER_AVAILABLE,
    reason="tree-sitter + tree-sitter-go not installed",
)

_ORDER_SOURCE = '''
package main

type OrderRequest struct {
	CustomerID int     `json:"customer_id"`
	Total      float64 `json:"total,omitempty"`
	internal   string  `json:"-"`
	Note       string
}

type OrderResponse struct {
	OrderID string `json:"order_id"`
	Status  string `json:"status"`
}

func setupRoutes(r *gin.Engine) {
	r.GET("/orders/:id", getOrder)
	r.POST("/orders", createOrder)
}

func createOrder(c *gin.Context) {
	var req OrderRequest
	c.ShouldBindJSON(&req)
	resp := OrderResponse{}
	c.JSON(200, resp)
}

func getOrder(c *gin.Context) {
	c.JSON(200, OrderResponse{})
}
'''


def _write_go_file(tmp_path: Path, source: str) -> str:
    f = tmp_path / "handlers.go"
    f.write_text(source, encoding="utf-8")
    return str(f)


@requires_tree_sitter
def test_extracts_both_routes(tmp_path):
    fpath = _write_go_file(tmp_path, _ORDER_SOURCE)
    endpoints = gin.GinDetector().extract([fpath])
    keys = {(e.method, e.path) for e in endpoints}
    assert keys == {("GET", "/orders/:id"), ("POST", "/orders")}


@requires_tree_sitter
def test_request_fields_use_json_tag_names(tmp_path):
    fpath = _write_go_file(tmp_path, _ORDER_SOURCE)
    endpoints = gin.GinDetector().extract([fpath])
    create = next(e for e in endpoints if e.path == "/orders" and e.method == "POST")
    field_names = {f.name for f in create.request_fields}
    assert field_names == {"customer_id", "total", "Note"}  # Note has no tag -> falls back to Go name


@requires_tree_sitter
def test_json_dash_tag_is_excluded(tmp_path):
    fpath = _write_go_file(tmp_path, _ORDER_SOURCE)
    endpoints = gin.GinDetector().extract([fpath])
    create = next(e for e in endpoints if e.path == "/orders" and e.method == "POST")
    field_names = {f.name for f in create.request_fields}
    assert "internal" not in field_names


@requires_tree_sitter
def test_response_fields_from_short_var_composite_literal(tmp_path):
    fpath = _write_go_file(tmp_path, _ORDER_SOURCE)
    endpoints = gin.GinDetector().extract([fpath])
    create = next(e for e in endpoints if e.path == "/orders" and e.method == "POST")
    field_names = {f.name for f in create.response_fields}
    assert field_names == {"order_id", "status"}


@requires_tree_sitter
def test_response_fields_from_inline_composite_literal(tmp_path):
    """c.JSON(200, OrderResponse{}) — no intermediate variable at all."""
    fpath = _write_go_file(tmp_path, _ORDER_SOURCE)
    endpoints = gin.GinDetector().extract([fpath])
    get = next(e for e in endpoints if e.path == "/orders/:id" and e.method == "GET")
    field_names = {f.name for f in get.response_fields}
    assert field_names == {"order_id", "status"}
    assert get.request_fields == []  # no bind call in getOrder


def test_non_gin_files_are_ignored(tmp_path):
    """Filtered out by extension before tree-sitter is even touched — runs unconditionally."""
    f = tmp_path / "app.py"
    f.write_text("def handler(): pass\n", encoding="utf-8")
    assert gin.GinDetector().extract([str(f)]) == []


@requires_tree_sitter
def test_field_type_text_is_captured(tmp_path):
    fpath = _write_go_file(tmp_path, _ORDER_SOURCE)
    endpoints = gin.GinDetector().extract([fpath])
    create = next(e for e in endpoints if e.path == "/orders" and e.method == "POST")
    by_name = {f.name: f.type for f in create.request_fields}
    assert by_name["customer_id"] == "int"
    assert by_name["total"] == "float64"


@requires_tree_sitter
def test_malformed_go_source_does_not_raise(tmp_path):
    f = tmp_path / "broken.go"
    f.write_text("this is not { valid go +++", encoding="utf-8")
    # tree-sitter is error-tolerant by design and returns a best-effort (possibly
    # empty) tree rather than raising — this just confirms extract() survives it.
    assert gin.GinDetector().extract([str(f)]) == []


# ---------------------------------------------------------------------------
# Graceful degradation — must run even when tree-sitter is NOT installed
# ---------------------------------------------------------------------------

def test_missing_tree_sitter_returns_empty_not_raises(tmp_path, monkeypatch):
    monkeypatch.setattr(gin, "_get_parser", lambda: None)
    fpath = _write_go_file(tmp_path, _ORDER_SOURCE)
    assert gin.GinDetector().extract([fpath]) == []
