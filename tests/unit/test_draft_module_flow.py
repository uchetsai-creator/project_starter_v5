"""Tests for draft_module_flow.py — the scout-style module-flow draft generator.

Unlike scan_codebase.py --scaffold (a blank template), this script parses the
module's actual source (ast for Python, regex+brace-depth for JS/TS) and
pre-fills real class/function names. These tests check that: (1) detected
structure is factual and complete, (2) the format chosen matches module type,
(3) no call-sequence content is fabricated, and (4) skip/--force behavior
matches scaffold_stubs()'s existing convention.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = REPO_ROOT / "templates/script/generators/draft_module_flow.py"


def _run(*args: str) -> subprocess.CompletedProcess:
    # PYTHONUTF8 forces the child's own stdout/stderr encoding to UTF-8, matching the
    # encoding="utf-8" this decodes with — see golden test helpers for the full rationale.
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True, encoding="utf-8",
        env={**os.environ, "PYTHONUTF8": "1"},
    )


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _draft_path(tmp_path: Path, module_name: str) -> Path:
    return tmp_path / "docs" / "modules" / module_name / f"{module_name}-module-data-flow.md"


# ---------------------------------------------------------------------------
# Python extraction
# ---------------------------------------------------------------------------

def test_python_module_detects_class_methods_and_functions(tmp_path):
    module_dir = tmp_path / "src" / "order"
    _write(module_dir / "order.py", (
        "class OrderController:\n"
        "    def create_order(self, req):\n"
        "        pass\n"
        "    def _internal(self):\n"
        "        pass\n\n"
        "def handle_create_order(req):\n"
        "    pass\n"
    ))

    result = _run(str(module_dir), "--project-type", "web-app", "--docs", str(tmp_path / "docs"))
    assert result.returncode == 0, result.stderr

    draft = _draft_path(tmp_path, "order").read_text(encoding="utf-8")
    assert "OrderController" in draft
    assert "create_order()" in draft
    assert "handle_create_order()" in draft
    assert "Classified as: Feature" in result.stdout


def test_private_python_method_gets_minus_visibility_in_class_block(tmp_path):
    module_dir = tmp_path / "src" / "order"
    _write(module_dir / "order.py", (
        "class OrderController:\n"
        "    def create_order(self):\n"
        "        pass\n"
        "    def _internal(self):\n"
        "        pass\n"
    ))
    _run(str(module_dir), "--project-type", "web-app", "--docs", str(tmp_path / "docs"))
    draft = _draft_path(tmp_path, "order").read_text(encoding="utf-8")
    assert "+create_order()" in draft
    assert "-_internal()" in draft


def test_dunder_methods_excluded_from_python_class_methods(tmp_path):
    module_dir = tmp_path / "src" / "order"
    _write(module_dir / "order.py", (
        "class Order:\n"
        "    def __init__(self):\n"
        "        pass\n"
        "    def total(self):\n"
        "        pass\n"
    ))
    _run(str(module_dir), "--project-type", "web-app", "--docs", str(tmp_path / "docs"))
    draft = _draft_path(tmp_path, "order").read_text(encoding="utf-8")
    assert "__init__" not in draft
    assert "total()" in draft


# ---------------------------------------------------------------------------
# JS/TS extraction
# ---------------------------------------------------------------------------

def test_js_module_detects_class_methods_and_top_level_functions(tmp_path):
    module_dir = tmp_path / "src" / "order-consumer"
    _write(module_dir / "consumer.js", (
        "class OrderConsumer {\n"
        "  async handleMessage(msg) {\n"
        "    return true;\n"
        "  }\n"
        "}\n\n"
        "function processQueueEvent(evt) {\n"
        "  return null;\n"
        "}\n\n"
        "const runWorker = () => {\n"
        "  return null;\n"
        "};\n"
    ))
    result = _run(str(module_dir), "--project-type", "web-app", "--docs", str(tmp_path / "docs"))
    assert result.returncode == 0, result.stderr

    draft = _draft_path(tmp_path, "order-consumer").read_text(encoding="utf-8")
    assert "OrderConsumer" in draft
    assert "handleMessage()" in draft
    assert "processQueueEvent()" in draft
    assert "runWorker()" in draft
    assert "Classified as: Background Job" in result.stdout


# ---------------------------------------------------------------------------
# Format selection by module type
# ---------------------------------------------------------------------------

def test_shared_utility_uses_format_c_no_flow_section(tmp_path):
    module_dir = tmp_path / "src" / "utils"
    _write(module_dir / "email.py", "class EmailSender:\n    def send(self):\n        pass\n")
    _run(str(module_dir), "--project-type", "web-app", "--docs", str(tmp_path / "docs"))
    draft = _draft_path(tmp_path, "utils").read_text(encoding="utf-8")
    assert "Shared Utility" in draft
    assert "Used by:" in draft
    assert "### Flow Format" not in draft


def test_pipeline_stage_type_uses_format_d(tmp_path):
    module_dir = tmp_path / "src" / "extract"
    _write(module_dir / "run_extract.py", "def run_extract():\n    pass\n")
    _run(str(module_dir), "--project-type", "data-pipeline", "--docs", str(tmp_path / "docs"))
    draft = _draft_path(tmp_path, "extract").read_text(encoding="utf-8")
    assert "Pipeline Stage" in draft
    assert "Format D" in draft


@pytest.mark.parametrize("project_type,expected_label", [
    ("cli-tool", "Command"),
    ("library", "Namespace"),
    ("microservices", "Service"),
    ("mobile-app", "Screen"),
])
def test_format_a_types_beyond_web_app_resolve_correctly(tmp_path, project_type, expected_label):
    """web-app's 'Feature' isn't the only label that maps to Format A — cli-tool,
    library, microservices, and mobile-app each get their own scan_codebase.py
    vocabulary but still use the Feature flow format. Covered separately from
    test_python_module_detects_class_methods_and_functions (web-app only) so a
    regression that special-cases 'Feature' instead of the full label set is caught."""
    module_dir = tmp_path / "src" / "thing"
    _write(module_dir / "thing.py", "def do_thing():\n    pass\n")
    result = _run(str(module_dir), "--project-type", project_type, "--docs", str(tmp_path / "docs"))
    assert result.returncode == 0, result.stderr
    draft = _draft_path(tmp_path, "thing").read_text(encoding="utf-8")
    assert f"classified this folder as: {expected_label}" in draft
    assert "Format A" in draft


def test_ml_pipeline_type_also_uses_format_d(tmp_path):
    """data-pipeline is covered by test_pipeline_stage_type_uses_format_d — ml-pipeline
    shares the same 'Pipeline Stage' vocabulary in scan_codebase.py and must resolve
    the same way, not fall back to UNKNOWN because only one of the two was wired in."""
    module_dir = tmp_path / "src" / "train"
    _write(module_dir / "run_train.py", "def run_train():\n    pass\n")
    result = _run(str(module_dir), "--project-type", "ml-pipeline", "--docs", str(tmp_path / "docs"))
    assert result.returncode == 0, result.stderr
    draft = _draft_path(tmp_path, "train").read_text(encoding="utf-8")
    assert "Format D" in draft


def test_unmapped_module_type_falls_back_honestly_instead_of_guessing(tmp_path):
    """Resource Group (IaC) has no matching format in module-data-flow.md — the
    draft must say so explicitly rather than silently forcing it into Format A."""
    module_dir = tmp_path / "src2" / "modules" / "networking"
    _write(module_dir / "main.tf", 'resource "aws_vpc" "main" {}\n')
    _run(str(module_dir), "--project-type", "iac", "--docs", str(tmp_path / "docs"))
    draft = _draft_path(tmp_path, "networking").read_text(encoding="utf-8")
    assert "No module-data-flow.md format matches" in draft


# ---------------------------------------------------------------------------
# Honesty: no fabricated call sequence
# ---------------------------------------------------------------------------

def test_entry_point_is_a_hint_not_an_asserted_fact(tmp_path):
    module_dir = tmp_path / "src" / "order"
    _write(module_dir / "order.py", "def handle_create_order(req):\n    pass\n")
    _run(str(module_dir), "--project-type", "web-app", "--docs", str(tmp_path / "docs"))
    draft = _draft_path(tmp_path, "order").read_text(encoding="utf-8")
    assert "candidates detected by name, confirm which applies" in draft
    assert "[Description of what this module does — not auto-derivable, fill in]" in draft


def test_no_functions_or_classes_produces_explicit_warning_not_silent_empty_draft(tmp_path):
    module_dir = tmp_path / "src2" / "modules" / "networking"
    _write(module_dir / "main.tf", 'resource "aws_vpc" "main" {}\n')
    result = _run(str(module_dir), "--project-type", "iac", "--docs", str(tmp_path / "docs"))
    assert "No classes or functions detected" in (
        _draft_path(tmp_path, "networking").read_text(encoding="utf-8")
    )
    assert "[WARN] No Python or JS/TS structure detected" in result.stdout


# ---------------------------------------------------------------------------
# Skip / --force, mirroring scan_codebase.py's scaffold_stubs() convention
# ---------------------------------------------------------------------------

def test_existing_draft_is_skipped_without_force(tmp_path):
    module_dir = tmp_path / "src" / "order"
    _write(module_dir / "order.py", "def run():\n    pass\n")
    _run(str(module_dir), "--project-type", "web-app", "--docs", str(tmp_path / "docs"))

    draft_path = _draft_path(tmp_path, "order")
    draft_path.write_text("hand-written content", encoding="utf-8")

    result = _run(str(module_dir), "--project-type", "web-app", "--docs", str(tmp_path / "docs"))
    assert "Skipped" in result.stdout
    assert draft_path.read_text(encoding="utf-8") == "hand-written content"


def test_force_overwrites_existing_draft(tmp_path):
    module_dir = tmp_path / "src" / "order"
    _write(module_dir / "order.py", "def run():\n    pass\n")
    draft_path = _draft_path(tmp_path, "order")
    draft_path.parent.mkdir(parents=True, exist_ok=True)
    draft_path.write_text("stale content", encoding="utf-8")

    result = _run(
        str(module_dir), "--project-type", "web-app", "--docs", str(tmp_path / "docs"), "--force",
    )
    assert result.returncode == 0, result.stderr
    assert "run()" in draft_path.read_text(encoding="utf-8")


# ---------------------------------------------------------------------------
# CLI validation
# ---------------------------------------------------------------------------

def test_nonexistent_module_dir_errors_clearly(tmp_path):
    result = _run(str(tmp_path / "does-not-exist"), "--project-type", "web-app")
    assert result.returncode == 2
    assert "not a directory" in result.stderr
