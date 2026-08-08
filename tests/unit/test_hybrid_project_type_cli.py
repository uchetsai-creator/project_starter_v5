"""Regression tests: scan_codebase.py and verify_spec_code.py must accept hybrid
project types (e.g. 'data-pipeline+web-app'), not just the 9 single types — both
scripts previously used argparse `choices=VALID_TYPES`, which rejected any '+'
combination outright, unlike every other validator in this framework
(verify_docs.py, verify_content.py, etc.), which all use `parse_types()`.
"""
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCAN_SCRIPT = REPO_ROOT / "templates/script/scanners/scan_codebase.py"
SPEC_CODE_SCRIPT = REPO_ROOT / "templates/script/validators/verify_spec_code.py"


def _run(script: Path, *args: str) -> subprocess.CompletedProcess:
    # PYTHONUTF8 forces the child's own stdout/stderr encoding to UTF-8, matching the
    # encoding="utf-8" this decodes with — see golden test helpers for the full rationale.
    return subprocess.run(
        [sys.executable, str(script), *args],
        capture_output=True, text=True, encoding="utf-8",
        env={**os.environ, "PYTHONUTF8": "1"},
    )


# ---------------------------------------------------------------------------
# scan_codebase.py
# ---------------------------------------------------------------------------

def test_scan_codebase_accepts_hybrid_project_type(tmp_path):
    src = tmp_path / "src" / "order_stage"
    src.mkdir(parents=True)
    (src / "run.py").write_text("def run(): pass\n", encoding="utf-8")

    result = _run(SCAN_SCRIPT, str(tmp_path / "src"), "--project-type", "data-pipeline+web-app")
    assert result.returncode == 0, result.stderr
    assert "invalid choice" not in result.stderr


def test_scan_codebase_uses_first_hybrid_type_for_classification(tmp_path):
    src = tmp_path / "src" / "order_stage"
    src.mkdir(parents=True)
    (src / "run.py").write_text("def run(): pass\n", encoding="utf-8")

    result = _run(SCAN_SCRIPT, str(tmp_path / "src"), "--project-type", "data-pipeline+web-app")
    # 'data-pipeline' is listed first, so Pipeline Stage vocabulary should be used,
    # not the web-app-default 'Feature' label.
    assert "Pipeline Stage" in result.stdout


def test_scan_codebase_still_rejects_unknown_type(tmp_path):
    (tmp_path / "src").mkdir()
    result = _run(SCAN_SCRIPT, str(tmp_path / "src"), "--project-type", "totally-bogus")
    assert result.returncode == 2
    assert "unknown project type" in result.stderr


# ---------------------------------------------------------------------------
# verify_spec_code.py
# ---------------------------------------------------------------------------

def test_verify_spec_code_accepts_hybrid_project_type(tmp_path):
    spec = tmp_path / "log-order.md"
    spec.write_text(
        "| Function | Operation | State | Level |\n"
        "|---|---|---|---|\n"
        "| create_order | create order | start | info |\n",
        encoding="utf-8",
    )
    src = tmp_path / "src"
    src.mkdir()
    (src / "order.py").write_text(
        'import logging\nlogger = logging.getLogger("ORDER")\n'
        'def create_order():\n    logger.info("create order — start")\n',
        encoding="utf-8",
    )

    result = _run(
        SPEC_CODE_SCRIPT,
        "--project-type", "data-pipeline+web-app",
        "--adapter", "logging", "--spec", str(spec), "--src", str(src),
    )
    assert result.returncode == 0, result.stderr
    assert "invalid choice" not in result.stderr
    assert "No mismatches" in result.stdout


def test_verify_spec_code_still_rejects_unknown_type(tmp_path):
    result = _run(
        SPEC_CODE_SCRIPT,
        "--project-type", "totally-bogus",
        "--adapter", "logging", "--spec", str(tmp_path), "--src", str(tmp_path),
    )
    assert result.returncode == 2
    assert "unknown project type" in result.stderr
