"""End-to-end CLI test for the gin adapter through verify_spec_code.py.

test_gin_detector.py covers GinDetector in isolation; this covers the full chain
(ADAPTER_REGISTRY -> WebAPIAdapter -> GinDetector -> compare()) the same way
test_verify_spec_code_zero_coverage.py does for other adapters — proves the
registry wiring itself, not just the parsing logic.

Skipped when tree-sitter + tree-sitter-go aren't installed, same as test_gin_detector.py.
"""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

_VALIDATORS_DIR = Path(__file__).resolve().parent.parent.parent / "templates/script/validators"
sys.path.insert(0, str(_VALIDATORS_DIR / "_spec_code_adapters"))

try:
    import tree_sitter_go  # noqa: F401
    from tree_sitter import Language, Parser  # noqa: F401
    _TREE_SITTER_AVAILABLE = True
except ImportError:
    _TREE_SITTER_AVAILABLE = False

pytestmark = pytest.mark.skipif(
    not _TREE_SITTER_AVAILABLE, reason="tree-sitter + tree-sitter-go not installed",
)

SCRIPT = _VALIDATORS_DIR / "verify_spec_code.py"

_GO_SOURCE = '''
package main

type OrderRequest struct {
	CustomerID int     `json:"customer_id"`
	Total      float64 `json:"total"`
}

type OrderResponse struct {
	OrderID string `json:"order_id"`
}

func setupRoutes(r *gin.Engine) {
	r.POST("/orders", createOrder)
}

func createOrder(c *gin.Context) {
	var req OrderRequest
	c.ShouldBindJSON(&req)
	resp := OrderResponse{}
	c.JSON(200, resp)
}
'''

_SPEC = """### POST /orders

#### Request Body
| Field | Type | Required | Description |
|---|---|---|---|
| customer_id | int | Yes | customer id |
| discount_code | string | No | promo code, not implemented in code yet |

#### Response Body
| Field | Type | Description |
|---|---|---|
| order_id | string | order id |
"""


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env={**os.environ, "PYTHONUTF8": "1"},
    )


def test_gin_adapter_flags_field_drift_in_both_directions(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "handlers.go").write_text(_GO_SOURCE, encoding="utf-8")
    spec = tmp_path / "api-contract.md"
    spec.write_text(_SPEC, encoding="utf-8")

    result = _run(
        "--project-type", "web-app", "--adapter", "gin",
        "--spec", str(spec), "--src", str(src), "--json",
    )
    assert result.returncode == 0, result.stdout + result.stderr
    payload = json.loads(result.stdout)

    mismatches = {(m["field"], m["issue"]) for m in payload["field_mismatches"]}
    assert ("discount_code", "removed_from_code") in mismatches  # spec-only
    assert ("total", "added_in_code") in mismatches              # code-only


def test_gin_adapter_strict_fails_on_drift(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "handlers.go").write_text(_GO_SOURCE, encoding="utf-8")
    spec = tmp_path / "api-contract.md"
    spec.write_text(_SPEC, encoding="utf-8")

    result = _run(
        "--project-type", "web-app", "--adapter", "gin",
        "--spec", str(spec), "--src", str(src), "--strict",
    )
    assert result.returncode == 1


def test_gin_is_listed_in_list_adapters():
    result = _run("--list-adapters")
    assert "gin" in result.stdout
