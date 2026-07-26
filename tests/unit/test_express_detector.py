import sys
import tempfile
from pathlib import Path

_ADAPTERS_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "templates" / "script" / "validators" / "_spec_code_adapters"
)
sys.path.insert(0, str(_ADAPTERS_DIR))

from express import ExpressDetector  # noqa: E402


def _extract(js_source: str):
    with tempfile.NamedTemporaryFile(suffix=".js", mode="w", delete=False, encoding="utf-8") as f:
        f.write(js_source)
        path = f.name
    try:
        return ExpressDetector().extract([path])
    finally:
        Path(path).unlink()


def test_ignores_axios_get_call():
    src = """
const express = require('express');
const axios = require('axios');
const router = express.Router();

router.get('/orders/:id', async (req, res) => {
  const inventory = await axios.get('/internal/inventory-check');
  res.json({ id: req.params.id });
});
"""
    endpoints = _extract(src)
    paths = {(e.method, e.path) for e in endpoints}
    assert ("GET", "/orders/:id") in paths
    assert not any(p == "/internal/inventory-check" for _, p in paths)
    assert len(paths) == 1


def test_falls_back_to_default_names_when_router_declared_elsewhere():
    src = """
const router = require('./shared-router');

router.get('/status', (req, res) => {
  res.json({ ok: true });
});
"""
    endpoints = _extract(src)
    assert ("GET", "/status") in {(e.method, e.path) for e in endpoints}


def test_recognizes_app_declared_with_express():
    src = """
const express = require('express');
const app = express();

app.post('/orders', (req, res) => {
  res.json({ order_id: 1 });
});
"""
    endpoints = _extract(src)
    assert ("POST", "/orders") in {(e.method, e.path) for e in endpoints}
