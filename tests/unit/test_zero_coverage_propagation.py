"""Regression tests: the "0 vs 0 silently reads as a pass" bug found in
verify_spec_code.py also existed one level up the module-doc coverage chain —
scan_codebase.py and verify_module_docs.py --src both used `total == 0` (or
`results == []`) as an implicit "everything's fine" signal, with no way to tell
"genuinely no code yet" apart from "real code exists but nothing recognized it"
(flat files with no subfolders, wrong --depth, everything misclassified as
Shared/Infrastructure). The second case previously reported 100% coverage
(scan_codebase.py) or exited 0 under --strict (verify_module_docs.py) even
though nothing was actually audited — this defeats the --src --strict check
templates/module-completion.md relies on to confirm a "complete" module actually
has doc coverage.

_src_has_real_files() (now shared in _verify_common.py, used by both scripts and
by verify_spec_code.py) distinguishes the two cases.
"""
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCAN_SCRIPT = REPO_ROOT / "templates/script/scanners/scan_codebase.py"
MODULE_DOCS_SCRIPT = REPO_ROOT / "templates/script/validators/verify_module_docs.py"


def _run(script: Path, *args: str) -> subprocess.CompletedProcess:
    # PYTHONUTF8 forces the child's own stdout/stderr encoding to UTF-8, matching the
    # encoding="utf-8" this decodes with — see golden test helpers for the full rationale.
    # errors="replace" stays as a last-resort safety net, not the primary fix.
    return subprocess.run(
        [sys.executable, str(script), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env={**os.environ, "PYTHONUTF8": "1"},
    )


def _flat_src(tmp_path: Path) -> Path:
    """A src/ with real code but no subfolders — scan_codebase.py's
    find_source_folders() only collects directories, so this always yields 0
    non-shared modules regardless of how much real code is here."""
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.py").write_text("def handle_order():\n    pass\n", encoding="utf-8")
    return src


# ---------------------------------------------------------------------------
# scan_codebase.py
# ---------------------------------------------------------------------------

def test_scan_codebase_warns_on_flat_src_with_real_code(tmp_path):
    src = _flat_src(tmp_path)
    result = _run(SCAN_SCRIPT, str(src), "--project-type", "web-app", "--coverage")
    assert result.returncode == 0, result.stderr
    assert "Coverage: 0/0 feature modules documented (100%)" in result.stdout
    assert "[WARN]" in result.stdout
    assert "not a real pass" in result.stdout


def test_scan_codebase_json_includes_zero_coverage_flag(tmp_path):
    src = _flat_src(tmp_path)
    result = _run(SCAN_SCRIPT, str(src), "--project-type", "web-app", "--format", "json")
    import json
    payload = json.loads(result.stdout)
    assert payload["summary"]["zero_coverage"] is True


def test_scan_codebase_does_not_warn_on_genuinely_empty_src(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    result = _run(SCAN_SCRIPT, str(src), "--project-type", "web-app", "--coverage")
    assert result.returncode == 0, result.stderr
    assert "[WARN]" not in result.stdout


def test_scan_codebase_does_not_warn_when_modules_are_genuinely_found(tmp_path):
    src = tmp_path / "src" / "order"
    src.mkdir(parents=True)
    (src / "handler.py").write_text("def handle():\n    pass\n", encoding="utf-8")
    result = _run(SCAN_SCRIPT, str(tmp_path / "src"), "--project-type", "web-app", "--coverage")
    assert result.returncode == 0, result.stderr
    assert "0 feature modules found, but real file" not in result.stdout


# ---------------------------------------------------------------------------
# verify_module_docs.py --src (delegates to scan_codebase.py internally)
# ---------------------------------------------------------------------------

def test_module_docs_fails_strict_on_flat_src_with_real_code(tmp_path):
    src = _flat_src(tmp_path)
    docs = tmp_path / "docs"
    docs.mkdir()
    result = _run(
        MODULE_DOCS_SCRIPT, "--project-type", "web-app",
        "--docs", str(docs), "--src", str(src), "--strict",
    )
    assert "NOT a confirmed pass" in result.stdout
    assert result.returncode == 1, "zero-coverage must fail --strict, not silently exit 0"


def test_module_docs_passes_strict_on_genuinely_empty_src(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    docs = tmp_path / "docs"
    docs.mkdir()
    result = _run(
        MODULE_DOCS_SCRIPT, "--project-type", "web-app",
        "--docs", str(docs), "--src", str(src), "--strict",
    )
    assert result.returncode == 0


def test_module_docs_without_src_flag_is_unaffected(tmp_path):
    """No --src at all means docs/modules/-only audit mode — a project with no
    documented modules yet is a pre-existing, separate case (no source cross-
    reference happens at all), not the zero_coverage bug this file targets."""
    docs = tmp_path / "docs"
    docs.mkdir()
    result = _run(MODULE_DOCS_SCRIPT, "--project-type", "web-app", "--docs", str(docs), "--strict")
    assert result.returncode == 0


def test_module_docs_json_includes_zero_coverage_flag(tmp_path):
    src = _flat_src(tmp_path)
    docs = tmp_path / "docs"
    docs.mkdir()
    result = _run(
        MODULE_DOCS_SCRIPT, "--project-type", "web-app",
        "--docs", str(docs), "--src", str(src), "--json",
    )
    import json
    payload = json.loads(result.stdout)
    assert payload["zero_coverage"] is True


def test_module_docs_zero_coverage_is_recorded_in_telemetry(tmp_path):
    """Regression: the 'no modules found' branch used to return before the
    --telemetry block ever ran, so a zero-coverage run — exactly the kind of
    silent gap worth a permanent record of — left no telemetry trace at all."""
    src = _flat_src(tmp_path)
    docs = tmp_path / "docs"
    docs.mkdir()
    subprocess.run(
        [sys.executable, str(MODULE_DOCS_SCRIPT), "--project-type", "web-app",
         "--docs", str(docs), "--src", str(src), "--telemetry"],
        capture_output=True, text=True, encoding="utf-8", cwd=str(tmp_path),
        env={**os.environ, "PYTHONUTF8": "1"},
    )
    import json
    telemetry_file = tmp_path / ".ai" / "telemetry" / "validation-result.json"
    assert telemetry_file.exists()
    rows = json.loads(telemetry_file.read_text())
    assert rows[-1]["validator"] == "verify_module_docs.py"
    assert rows[-1]["level"] == "fail"
