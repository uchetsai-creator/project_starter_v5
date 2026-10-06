"""--docs-aware registry lookup for validators whose constants are built at import time."""
import importlib.util
import sys

from tests.conftest import REPO_ROOT

_REG = REPO_ROOT / "templates/script/validators/_registry.py"


def _load():
    spec = importlib.util.spec_from_file_location("_registry_under_test", _REG)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


reg = _load()


def test_docs_dir_from_argv_reads_both_forms(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["verify_docs.py", "--project-type", "web-app", "--docs", "docs/isbg"])
    assert reg.docs_dir_from_argv() == "docs/isbg"
    monkeypatch.setattr(sys, "argv", ["verify_docs.py", "--docs=x/y"])
    assert reg.docs_dir_from_argv() == "x/y"
    monkeypatch.setattr(sys, "argv", ["verify_docs.py"])
    assert reg.docs_dir_from_argv("docs") == "docs"


def test_load_registry_for_docs_prefers_registry_next_to_docs(tmp_path):
    (tmp_path / "document-registry.yaml").write_text(
        "documents:\n  demo-doc:\n    file: demo.md\n    path: demo.md\n    required_for: [web-app]\n",
        encoding="utf-8")
    loaded = reg.load_registry_for_docs(str(tmp_path))
    assert "demo-doc" in loaded
