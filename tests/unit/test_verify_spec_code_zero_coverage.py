"""Regression tests for the zero-coverage warning in verify_spec_code.py.

Bug: when --src points at real code but no detector matches it (wrong --framework
hint, or no detector registered for that language at all), extract_code() returns
[]. If the spec file also declares zero items, compare() finds no mismatches and
the tool printed "[OK] No mismatches — spec and code are in sync." — a false
pass, since nothing was actually compared. If the spec declared items, every one
was reported as "missing in code", which reads as "you forgot to write this" when
the real cause is "no detector can see this language at all" — misleading in a
way that sends someone chasing the wrong fix indefinitely.

zero_coverage now fires whenever code_items is empty but --src contains real
(non-placeholder) files, printing an explicit [WARN] instead of/alongside the
normal report, and failing --strict rather than silently exiting 0.
"""
import os
import subprocess
import sys
from pathlib import Path

_VALIDATORS_DIR = Path(__file__).resolve().parent.parent.parent / "templates/script/validators"
sys.path.insert(0, str(_VALIDATORS_DIR))

import verify_spec_code as vsc  # noqa: E402

SCRIPT = _VALIDATORS_DIR / "verify_spec_code.py"


def _run(*args: str) -> subprocess.CompletedProcess:
    # PYTHONUTF8 forces the child's own stdout/stderr encoding to UTF-8, matching the
    # encoding="utf-8" this decodes with — see golden test helpers for the full rationale.
    # errors="replace" stays as a last-resort safety net, not the primary fix.
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env={**os.environ, "PYTHONUTF8": "1"},
    )


# ---------------------------------------------------------------------------
# _src_has_real_files() — the helper distinguishing "no code yet" from
# "code exists but nothing detected it"
# ---------------------------------------------------------------------------

def test_src_with_real_code_file_is_true(tmp_path):
    (tmp_path / "main.go").write_text("package main\n", encoding="utf-8")
    assert vsc._src_has_real_files(str(tmp_path)) is True


def test_src_with_only_placeholder_files_is_false(tmp_path):
    (tmp_path / ".gitkeep").write_text("", encoding="utf-8")
    (tmp_path / "README.md").write_text("nothing here yet\n", encoding="utf-8")
    assert vsc._src_has_real_files(str(tmp_path)) is False


def test_truly_empty_src_dir_is_false(tmp_path):
    assert vsc._src_has_real_files(str(tmp_path)) is False


def test_real_file_nested_in_subdirectory_is_still_found(tmp_path):
    nested = tmp_path / "internal" / "handlers"
    nested.mkdir(parents=True)
    (nested / "order.go").write_text("package handlers\n", encoding="utf-8")
    assert vsc._src_has_real_files(str(tmp_path)) is True


def test_skip_dirnames_like_node_modules_are_not_counted(tmp_path):
    skipped = tmp_path / "node_modules" / "somepkg"
    skipped.mkdir(parents=True)
    (skipped / "index.js").write_text("module.exports = {};\n", encoding="utf-8")
    assert vsc._src_has_real_files(str(tmp_path)) is False


# ---------------------------------------------------------------------------
# Full CLI behavior — the exact bug scenario, reproduced end-to-end
# ---------------------------------------------------------------------------

def _write_log_spec(path: Path, rows: str) -> None:
    path.write_text(
        "| Function | Operation | State | Level |\n|---|---|---|---|\n" + rows,
        encoding="utf-8",
    )


def test_empty_spec_plus_undetected_code_warns_instead_of_silently_passing(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.go").write_text("package main\nfunc handleOrder() {}\n", encoding="utf-8")
    spec = tmp_path / "log-empty.md"
    _write_log_spec(spec, "")  # zero declared rows

    result = _run(
        "--project-type", "web-app", "--adapter", "logging",
        "--spec", str(spec), "--src", str(src), "--strict",
    )
    assert "[WARN]" in result.stdout
    assert "0 code items extracted" in result.stdout
    assert "No mismatches" not in result.stdout
    assert result.returncode == 1, "zero-coverage must fail --strict, not silently pass"


def test_nonempty_spec_plus_undetected_code_shows_warning_alongside_fail(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.go").write_text("package main\nfunc handleOrder() {}\n", encoding="utf-8")
    spec = tmp_path / "log-order.md"
    _write_log_spec(spec, "| handleOrder | create order | start | info |\n")

    result = _run(
        "--project-type", "web-app", "--adapter", "logging",
        "--spec", str(spec), "--src", str(src), "--strict",
    )
    assert "[WARN]" in result.stdout
    assert "0 code items extracted" in result.stdout
    assert "[FAIL]" in result.stdout
    assert result.returncode == 1


def test_genuinely_empty_src_does_not_trigger_zero_coverage_warning(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    spec = tmp_path / "log-empty.md"
    _write_log_spec(spec, "")

    result = _run(
        "--project-type", "web-app", "--adapter", "logging",
        "--spec", str(spec), "--src", str(src), "--strict",
    )
    assert "[WARN]" not in result.stdout
    assert "No mismatches" in result.stdout
    assert result.returncode == 0


def test_normal_detected_code_is_unaffected_by_the_new_check(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "order.py").write_text(
        'import logging\nlogger = logging.getLogger("ORDER")\n'
        'def handleOrder():\n    logger.info("create order — start")\n',
        encoding="utf-8",
    )
    spec = tmp_path / "log-order.md"
    _write_log_spec(spec, "| handleOrder | create order | start | info |\n")

    result = _run(
        "--project-type", "web-app", "--adapter", "logging",
        "--spec", str(spec), "--src", str(src), "--strict",
    )
    assert "[WARN]  0 code items extracted" not in result.stdout
    assert "No mismatches" in result.stdout
    assert result.returncode == 0


def test_json_output_includes_zero_coverage_field(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.go").write_text("package main\nfunc handleOrder() {}\n", encoding="utf-8")
    spec = tmp_path / "log-empty.md"
    _write_log_spec(spec, "")

    result = _run(
        "--project-type", "web-app", "--adapter", "logging",
        "--spec", str(spec), "--src", str(src), "--json",
    )
    import json
    payload = json.loads(result.stdout)
    assert payload["zero_coverage"] is True
