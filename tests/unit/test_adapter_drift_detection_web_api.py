"""Golden drift-detection coverage for the remaining web-api adapters: flask, django,
express. See tests/unit/test_adapter_drift_detection.py for fastapi/click/langchain and
the full rationale — this file follows the same clean-pair + planted-drift pattern.
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
# Flask
# ---------------------------------------------------------------------------

_FLASK_SPEC = """\
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

_FLASK_CODE_CLEAN = """\
from flask import Flask

app = Flask(__name__)


class OrderResponse:
    order_id: int
    status: str


@app.route("/orders", methods=["POST"])
def create_order(customer_id: int, item_count: int) -> OrderResponse:
    ...
"""


def test_flask_clean_spec_and_code_report_no_mismatches(tmp_path):
    spec = tmp_path / "api-contract.md"
    spec.write_text(_FLASK_SPEC, encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    (src / "orders.py").write_text(_FLASK_CODE_CLEAN, encoding="utf-8")

    result = _run("--adapter", "flask", "--spec", str(spec), "--src", str(src), "--strict")
    assert "No mismatches" in result.stdout, result.stdout
    assert result.returncode == 0


def test_flask_missing_request_field_is_caught(tmp_path):
    spec = tmp_path / "api-contract.md"
    spec.write_text(_FLASK_SPEC, encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    code = _FLASK_CODE_CLEAN.replace(", item_count: int", "")
    (src / "orders.py").write_text(code, encoding="utf-8")

    result = _run("--adapter", "flask", "--spec", str(spec), "--src", str(src), "--strict")
    assert "[FAIL]" in result.stdout, result.stdout
    assert "item_count" in result.stdout, result.stdout
    assert result.returncode == 1


def test_flask_missing_route_entirely_is_caught(tmp_path):
    spec = tmp_path / "api-contract.md"
    spec.write_text(_FLASK_SPEC, encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    (src / "orders.py").write_text("from flask import Flask\napp = Flask(__name__)\n", encoding="utf-8")

    result = _run("--adapter", "flask", "--spec", str(spec), "--src", str(src), "--strict")
    assert "[FAIL]" in result.stdout, result.stdout
    assert "POST /orders" in result.stdout, result.stdout
    assert result.returncode == 1


# ---------------------------------------------------------------------------
# Django (REST Framework)
# ---------------------------------------------------------------------------

_DJANGO_SPEC = """\
### GET /orders/{order_id}/
#### Request Body
| Field | Type | Required | Description |
|---|---|---|---|
| order_id | int | Yes | Order ID (path parameter) |

#### Response Body
| Field | Type | Description |
|---|---|---|
| id | int | Order ID |
"""

_DJANGO_VIEWS_CLEAN = """\
from rest_framework.decorators import api_view
from rest_framework.response import Response


@api_view(["GET"])
def get_order(request, order_id: int):
    return Response({"id": order_id})
"""

_DJANGO_URLS = """\
from django.urls import path
from . import views

urlpatterns = [
    path("orders/<int:order_id>/", views.get_order),
]
"""


def test_django_clean_spec_and_code_report_no_mismatches(tmp_path):
    spec = tmp_path / "api-contract.md"
    spec.write_text(_DJANGO_SPEC, encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    (src / "views.py").write_text(_DJANGO_VIEWS_CLEAN, encoding="utf-8")
    (src / "urls.py").write_text(_DJANGO_URLS, encoding="utf-8")

    result = _run("--adapter", "django", "--spec", str(spec), "--src", str(src), "--strict")
    assert "No mismatches" in result.stdout, result.stdout
    assert result.returncode == 0


def test_django_response_field_removed_is_caught(tmp_path):
    spec = tmp_path / "api-contract.md"
    spec.write_text(_DJANGO_SPEC, encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    # Drift: response no longer includes "id".
    code = _DJANGO_VIEWS_CLEAN.replace('return Response({"id": order_id})', 'return Response({})')
    (src / "views.py").write_text(code, encoding="utf-8")
    (src / "urls.py").write_text(_DJANGO_URLS, encoding="utf-8")

    result = _run("--adapter", "django", "--spec", str(spec), "--src", str(src), "--strict")
    assert "[FAIL]" in result.stdout, result.stdout
    assert result.returncode == 1


def test_django_view_not_wired_to_urls_is_reported_missing(tmp_path):
    """A view that exists but was never wired into urlpatterns is invisible to the
    detector by design (no path to compare against) — the spec's endpoint is then
    reported as missing entirely, which is the correct signal here."""
    spec = tmp_path / "api-contract.md"
    spec.write_text(_DJANGO_SPEC, encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    (src / "views.py").write_text(_DJANGO_VIEWS_CLEAN, encoding="utf-8")
    (src / "urls.py").write_text("urlpatterns = []\n", encoding="utf-8")

    result = _run("--adapter", "django", "--spec", str(spec), "--src", str(src), "--strict")
    assert "[FAIL]" in result.stdout, result.stdout
    assert "GET /orders/{order_id}/" in result.stdout, result.stdout
    assert result.returncode == 1


# ---------------------------------------------------------------------------
# Express — ExpressDetector never extracts request/response fields (route path +
# method only), so its drift coverage is endpoint-presence only, not field-level.
# ---------------------------------------------------------------------------

_EXPRESS_SPEC = """\
### POST /orders

### GET /orders/{id}
"""

_EXPRESS_CODE_CLEAN = """\
const express = require('express');
const app = express();

app.post('/orders', (req, res) => { res.json({}); });
app.get('/orders/:id', (req, res) => { res.json({}); });
"""


def test_express_clean_spec_and_code_report_no_mismatches(tmp_path):
    spec = tmp_path / "api-contract.md"
    spec.write_text(_EXPRESS_SPEC, encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    (src / "server.js").write_text(_EXPRESS_CODE_CLEAN, encoding="utf-8")

    result = _run("--adapter", "express", "--spec", str(spec), "--src", str(src), "--strict")
    assert "No mismatches" in result.stdout, result.stdout
    assert result.returncode == 0


def test_express_missing_route_is_caught(tmp_path):
    spec = tmp_path / "api-contract.md"
    spec.write_text(_EXPRESS_SPEC, encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    # Drift: the GET /orders/:id route was dropped entirely.
    code = _EXPRESS_CODE_CLEAN.replace(
        "app.get('/orders/:id', (req, res) => { res.json({}); });\n", ""
    )
    (src / "server.js").write_text(code, encoding="utf-8")

    result = _run("--adapter", "express", "--spec", str(spec), "--src", str(src), "--strict")
    assert "[FAIL]" in result.stdout, result.stdout
    assert "GET /orders/{id}" in result.stdout, result.stdout
    assert result.returncode == 1


def test_express_extra_undeclared_route_is_warned(tmp_path):
    spec = tmp_path / "api-contract.md"
    spec.write_text(_EXPRESS_SPEC, encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    # Drift: an extra DELETE route exists in code but was never declared in the spec.
    code = _EXPRESS_CODE_CLEAN + "app.delete('/orders/:id', (req, res) => { res.json({}); });\n"
    (src / "server.js").write_text(code, encoding="utf-8")

    result = _run("--adapter", "express", "--spec", str(spec), "--src", str(src), "--strict")
    assert "[WARN]" in result.stdout, result.stdout
    assert "DELETE /orders/:id" in result.stdout, result.stdout
