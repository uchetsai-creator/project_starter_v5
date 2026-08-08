"""Unit tests for verify_prose.py — the Vale prose-quality wrapper.

Tool invocation (_run_vale / _which) is monkeypatched throughout so these tests never
require Vale to actually be installed in CI. The sample JSON below was captured from a
real `vale --config _prose_style/.vale.ini --output=JSON` run against this framework's
own shipped Custom/WeaselWords.yml + Custom/NaturalLanguagePlaceholders.yml rules, not
hand-written — see test_verify_prose_e2e.py for the (real-Vale, skip-if-absent) run
that captured it.
"""
import importlib.util
import json
import os
import subprocess
import sys
from pathlib import Path

_VP_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "templates" / "script" / "validators" / "verify_prose.py"
)
_spec = importlib.util.spec_from_file_location("verify_prose", _VP_PATH)
vp = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vp)

SCRIPT = _VP_PATH


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env={**os.environ, "PYTHONUTF8": "1"},
    )


# ---------------------------------------------------------------------------
# _find_md_files
# ---------------------------------------------------------------------------

def test_find_md_files_matches_markdown(tmp_path):
    (tmp_path / "quickstart.md").write_text("# hi\n", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("hi\n", encoding="utf-8")
    found = vp._find_md_files(str(tmp_path))
    assert len(found) == 1
    assert found[0].endswith("quickstart.md")


def test_find_md_files_skips_node_modules(tmp_path):
    skipped = tmp_path / "node_modules" / "pkg"
    skipped.mkdir(parents=True)
    (skipped / "readme.md").write_text("hi\n", encoding="utf-8")
    assert vp._find_md_files(str(tmp_path)) == []


def test_find_md_files_on_empty_dir_returns_empty(tmp_path):
    assert vp._find_md_files(str(tmp_path)) == []


# ---------------------------------------------------------------------------
# _parse_vale_json — real shape captured from `vale --output=JSON`
# ---------------------------------------------------------------------------

_VALE_SAMPLE = json.dumps({
    "quickstart.md": [
        {
            "Check": "Custom.WeaselWords",
            "Severity": "warning",
            "Message": "'obviously' is vague — say specifically why/how instead.",
            "Line": 3,
        },
        {
            "Check": "Custom.NaturalLanguagePlaceholders",
            "Severity": "error",
            "Message": "'coming soon' reads as an unfinished placeholder left in prose — fill this in or remove it.",
            "Line": 5,
        },
    ],
})


def test_parse_vale_json_maps_fields():
    findings = vp._parse_vale_json(_VALE_SAMPLE)
    assert len(findings) == 2
    weasel = next(f for f in findings if f["rule"] == "Custom.WeaselWords")
    assert weasel["tool"] == "vale"
    assert weasel["file"] == "quickstart.md"
    assert weasel["line"] == 3
    assert weasel["severity"] == "medium"


def test_parse_vale_json_severity_mapping():
    findings = vp._parse_vale_json(_VALE_SAMPLE)
    by_rule = {f["rule"]: f for f in findings}
    assert by_rule["Custom.WeaselWords"]["severity"] == "medium"       # warning
    assert by_rule["Custom.NaturalLanguagePlaceholders"]["severity"] == "high"  # error


def test_parse_vale_json_empty_object():
    assert vp._parse_vale_json(json.dumps({})) == []


def test_parse_vale_json_blank_input():
    assert vp._parse_vale_json("") == []


def test_parse_vale_json_malformed_input_does_not_raise():
    assert vp._parse_vale_json("not json") == []


# ---------------------------------------------------------------------------
# run_scan — orchestration, with tool calls monkeypatched
# ---------------------------------------------------------------------------

def test_run_scan_no_md_files_runs_nothing(tmp_path):
    (tmp_path / "app.py").write_text("x = 1\n", encoding="utf-8")
    result = vp.run_scan(str(tmp_path))
    assert result["tools_run"] == []
    assert result["tools_skipped"] == []
    assert result["findings"] == []
    assert result["passed"] is True


def test_run_scan_missing_vale_is_skipped_not_failed(tmp_path, monkeypatch):
    (tmp_path / "quickstart.md").write_text("# hi\n", encoding="utf-8")
    monkeypatch.setattr(vp, "_which", lambda tool: None)
    result = vp.run_scan(str(tmp_path))
    assert result["tools_run"] == []
    assert len(result["tools_skipped"]) == 1
    assert result["tools_skipped"][0]["tool"] == "vale"
    assert result["passed"] is True


def test_run_scan_runs_vale_when_available(tmp_path, monkeypatch):
    (tmp_path / "quickstart.md").write_text("# hi\n", encoding="utf-8")
    monkeypatch.setattr(vp, "_which", lambda tool: "/usr/local/bin/vale" if tool == "vale" else None)
    monkeypatch.setattr(vp, "_run_vale", lambda files: (_VALE_SAMPLE, "", 1))
    result = vp.run_scan(str(tmp_path), min_severity="medium")
    assert result["tools_run"] == ["vale"]
    assert len(result["findings"]) == 2
    assert result["blocking_findings"] == 2  # both medium+ at default threshold
    assert result["passed"] is False


def test_run_scan_min_severity_high_ignores_medium_findings(tmp_path, monkeypatch):
    (tmp_path / "quickstart.md").write_text("# hi\n", encoding="utf-8")
    monkeypatch.setattr(vp, "_which", lambda tool: "/usr/local/bin/vale" if tool == "vale" else None)
    monkeypatch.setattr(vp, "_run_vale", lambda files: (_VALE_SAMPLE, "", 1))
    result = vp.run_scan(str(tmp_path), min_severity="high")
    assert result["blocking_findings"] == 1  # only the error-level finding
    assert result["passed"] is False


def test_run_scan_tool_error_returncode_is_skipped_with_reason(tmp_path, monkeypatch):
    (tmp_path / "quickstart.md").write_text("# hi\n", encoding="utf-8")
    monkeypatch.setattr(vp, "_which", lambda tool: "/usr/local/bin/vale" if tool == "vale" else None)
    monkeypatch.setattr(vp, "_run_vale", lambda files: ("", "config error", 2))
    result = vp.run_scan(str(tmp_path))
    assert result["tools_run"] == []
    assert len(result["tools_skipped"]) == 1
    assert "code 2" in result["tools_skipped"][0]["reason"]
    assert result["passed"] is True


# ---------------------------------------------------------------------------
# CLI behavior (no real vale required)
# ---------------------------------------------------------------------------

def test_cli_missing_docs_warns_and_exits_zero():
    result = _run()
    assert "not configured" in result.stdout
    assert result.returncode == 0


def test_cli_nonexistent_docs_errors():
    result = _run("--docs", "/this/path/does/not/exist")
    assert result.returncode == 2


def test_cli_list_tools_exits_zero():
    result = _run("--list-tools")
    assert "vale" in result.stdout
    assert result.returncode == 0


def test_cli_empty_docs_dir_passes(tmp_path):
    result = _run("--docs", str(tmp_path), "--strict")
    assert result.returncode == 0
    assert "nothing to scan" in result.stdout
