"""Unit tests for verify_security.py — the bandit / eslint-plugin-security / semgrep
SAST wrapper.

Tool invocation (_run_bandit / _run_eslint / _run_semgrep / _which) is monkeypatched
throughout so these tests never require bandit, eslint, or semgrep to actually be
installed in CI.
"""
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

_VS_PATH = (
    Path(__file__).resolve().parent.parent.parent
    / "templates" / "script" / "validators" / "verify_security.py"
)
_spec = importlib.util.spec_from_file_location("verify_security", _VS_PATH)
assert _spec is not None and _spec.loader is not None
vs = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(vs)

SCRIPT = _VS_PATH


def _run(*args: str) -> subprocess.CompletedProcess:
    import os
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env={**os.environ, "PYTHONUTF8": "1"},
    )


# ---------------------------------------------------------------------------
# _find_files — language file discovery
# ---------------------------------------------------------------------------

def test_find_files_matches_python_extension(tmp_path):
    (tmp_path / "app.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "readme.md").write_text("hi\n", encoding="utf-8")
    found = vs._find_files(str(tmp_path), vs._PY_EXT)
    assert len(found) == 1
    assert found[0].endswith("app.py")


def test_find_files_matches_js_ts_extensions(tmp_path):
    (tmp_path / "a.js").write_text("", encoding="utf-8")
    (tmp_path / "b.ts").write_text("", encoding="utf-8")
    (tmp_path / "c.jsx").write_text("", encoding="utf-8")
    (tmp_path / "d.py").write_text("", encoding="utf-8")
    found = vs._find_files(str(tmp_path), vs._JS_EXT)
    assert len(found) == 3


def test_find_files_skips_node_modules(tmp_path):
    skipped = tmp_path / "node_modules" / "pkg"
    skipped.mkdir(parents=True)
    (skipped / "index.js").write_text("", encoding="utf-8")
    found = vs._find_files(str(tmp_path), vs._JS_EXT)
    assert found == []


def test_find_files_on_empty_dir_returns_empty(tmp_path):
    assert vs._find_files(str(tmp_path), vs._PY_EXT) == []


# ---------------------------------------------------------------------------
# _parse_bandit_json
# ---------------------------------------------------------------------------

_BANDIT_SAMPLE = json.dumps({
    "results": [
        {
            "filename": "app.py",
            "line_number": 12,
            "issue_severity": "HIGH",
            "test_id": "B602",
            "issue_text": "subprocess call with shell=True identified.",
        },
        {
            "filename": "app.py",
            "line_number": 30,
            "issue_severity": "LOW",
            "test_id": "B101",
            "issue_text": "Use of assert detected.",
        },
    ]
})


def test_parse_bandit_json_maps_fields():
    findings = vs._parse_bandit_json(_BANDIT_SAMPLE)
    assert len(findings) == 2
    high = findings[0]
    assert high["tool"] == "bandit"
    assert high["file"] == "app.py"
    assert high["line"] == 12
    assert high["severity"] == "high"
    assert high["rule"] == "B602"
    assert "shell=True" in high["message"]


def test_parse_bandit_json_empty_results():
    assert vs._parse_bandit_json(json.dumps({"results": []})) == []


def test_parse_bandit_json_blank_input():
    assert vs._parse_bandit_json("") == []


def test_parse_bandit_json_malformed_input_does_not_raise():
    assert vs._parse_bandit_json("not json") == []


# ---------------------------------------------------------------------------
# _parse_eslint_json
# ---------------------------------------------------------------------------

_ESLINT_SAMPLE = json.dumps([
    {
        "filePath": "src/app.js",
        "messages": [
            {"ruleId": "security/detect-eval-with-expression", "severity": 2,
             "message": "eval with argument involving a variable.", "line": 5},
            {"ruleId": "security/detect-object-injection", "severity": 1,
             "message": "Generic Object Injection Sink.", "line": 9},
            {"ruleId": "no-unused-vars", "severity": 2,
             "message": "unrelated style rule.", "line": 1},
        ],
    }
])


def test_parse_eslint_json_filters_to_security_rules_only():
    findings = vs._parse_eslint_json(_ESLINT_SAMPLE)
    assert len(findings) == 2
    assert all(f["rule"].startswith("security/") for f in findings)


def test_parse_eslint_json_severity_mapping():
    findings = vs._parse_eslint_json(_ESLINT_SAMPLE)
    by_rule = {f["rule"]: f for f in findings}
    assert by_rule["security/detect-eval-with-expression"]["severity"] == "high"
    assert by_rule["security/detect-object-injection"]["severity"] == "medium"


def test_parse_eslint_json_blank_input():
    assert vs._parse_eslint_json("") == []


def test_parse_eslint_json_malformed_input_does_not_raise():
    assert vs._parse_eslint_json("not json") == []


# ---------------------------------------------------------------------------
# _parse_semgrep_json — real shape captured from a live `semgrep scan --json` run
# against a Go file with exec.Command(sh, -c, userInput) (see gin.py test fixtures
# for the Go grammar side; this is the SAST side, unrelated to spec<->code drift)
# ---------------------------------------------------------------------------

_SEMGREP_SAMPLE = json.dumps({
    "results": [
        {
            "check_id": "go.lang.security.audit.dangerous-exec-command.dangerous-exec-command",
            "path": "main.go",
            "start": {"line": 9, "col": 9},
            "end": {"line": 9, "col": 44},
            "extra": {
                "severity": "ERROR",
                "message": "Detected non-static command inside Command. Audit the input.",
            },
        },
        {
            "check_id": "generic.secrets.security.detected-generic-api-key",
            "path": "config.rb",
            "start": {"line": 3, "col": 1},
            "end": {"line": 3, "col": 40},
            "extra": {
                "severity": "WARNING",
                "message": "Possible hardcoded API key.",
            },
        },
    ],
})


def test_parse_semgrep_json_maps_fields():
    findings = vs._parse_semgrep_json(_SEMGREP_SAMPLE)
    assert len(findings) == 2
    first = findings[0]
    assert first["tool"] == "semgrep"
    assert first["file"] == "main.go"
    assert first["line"] == 9
    assert first["severity"] == "high"
    assert first["rule"] == "go.lang.security.audit.dangerous-exec-command.dangerous-exec-command"


def test_parse_semgrep_json_severity_mapping():
    findings = vs._parse_semgrep_json(_SEMGREP_SAMPLE)
    by_file = {f["file"]: f for f in findings}
    assert by_file["main.go"]["severity"] == "high"      # ERROR
    assert by_file["config.rb"]["severity"] == "medium"  # WARNING


def test_parse_semgrep_json_empty_results():
    assert vs._parse_semgrep_json(json.dumps({"results": []})) == []


def test_parse_semgrep_json_blank_input():
    assert vs._parse_semgrep_json("") == []


def test_parse_semgrep_json_malformed_input_does_not_raise():
    assert vs._parse_semgrep_json("not json") == []


# ---------------------------------------------------------------------------
# run_scan — orchestration, with tool calls monkeypatched
# ---------------------------------------------------------------------------

def test_run_scan_no_matching_files_runs_nothing(tmp_path, monkeypatch):
    (tmp_path / "readme.md").write_text("hi\n", encoding="utf-8")
    result = vs.run_scan(str(tmp_path))
    assert result["tools_run"] == []
    assert result["tools_skipped"] == []
    assert result["findings"] == []
    assert result["passed"] is True


def test_run_scan_missing_bandit_is_skipped_not_failed(tmp_path, monkeypatch):
    (tmp_path / "app.py").write_text("x = 1\n", encoding="utf-8")
    monkeypatch.setattr(vs, "_which", lambda tool: None)
    result = vs.run_scan(str(tmp_path))
    assert result["tools_run"] == []
    assert len(result["tools_skipped"]) == 1
    assert result["tools_skipped"][0]["tool"] == "bandit"
    assert result["findings"] == []
    assert result["passed"] is True  # missing tool never fails the gate


def test_run_scan_runs_bandit_when_available(tmp_path, monkeypatch):
    (tmp_path / "app.py").write_text("x = 1\n", encoding="utf-8")
    monkeypatch.setattr(vs, "_which", lambda tool: "/usr/bin/bandit" if tool == "bandit" else None)
    monkeypatch.setattr(vs, "_run_bandit", lambda exe, src: (_BANDIT_SAMPLE, "", 1))
    result = vs.run_scan(str(tmp_path), min_severity="medium")
    assert result["tools_run"] == ["bandit"]
    assert len(result["findings"]) == 2
    # HIGH counts toward blocking at min_severity=medium; the LOW finding doesn't.
    assert result["blocking_findings"] == 1
    assert result["passed"] is False


def test_run_scan_min_severity_high_ignores_medium_findings(tmp_path, monkeypatch):
    (tmp_path / "app.js").write_text("", encoding="utf-8")
    monkeypatch.setattr(vs, "_which", lambda tool: "/usr/bin/eslint" if tool == "eslint" else None)
    monkeypatch.setattr(vs, "_run_eslint", lambda exe, src: (_ESLINT_SAMPLE, "", 1))
    result = vs.run_scan(str(tmp_path), min_severity="high")
    # one high + one medium finding; only the high one should block at min_severity=high
    assert result["blocking_findings"] == 1
    assert result["passed"] is False


def test_run_scan_tool_error_returncode_is_skipped_with_reason(tmp_path, monkeypatch):
    (tmp_path / "app.py").write_text("x = 1\n", encoding="utf-8")
    monkeypatch.setattr(vs, "_which", lambda tool: "/usr/bin/bandit" if tool == "bandit" else None)
    monkeypatch.setattr(vs, "_run_bandit", lambda exe, src: ("", "traceback: boom", 2))
    result = vs.run_scan(str(tmp_path))
    assert result["tools_run"] == []
    assert len(result["tools_skipped"]) == 1
    assert "code 2" in result["tools_skipped"][0]["reason"]
    assert result["passed"] is True


def test_run_scan_routes_go_files_to_semgrep(tmp_path, monkeypatch):
    (tmp_path / "main.go").write_text("package main\n", encoding="utf-8")
    monkeypatch.setattr(vs, "_which", lambda tool: "/usr/bin/semgrep" if tool == "semgrep" else None)
    monkeypatch.setattr(vs, "_run_semgrep", lambda exe, files: (_SEMGREP_SAMPLE, "", 0))
    result = vs.run_scan(str(tmp_path))
    assert result["tools_run"] == ["semgrep"]
    assert len(result["findings"]) == 2


def test_run_scan_does_not_route_python_or_js_files_to_semgrep(tmp_path, monkeypatch):
    """bandit/eslint already cover these languages — semgrep must not double-report them."""
    (tmp_path / "app.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "app.js").write_text("var x = 1;\n", encoding="utf-8")
    semgrep_called = []
    monkeypatch.setattr(vs, "_which", lambda tool: None)  # nothing installed
    monkeypatch.setattr(vs, "_run_semgrep", lambda exe, files: semgrep_called.append(files) or ("", "", 0))
    vs.run_scan(str(tmp_path))
    assert semgrep_called == []  # never invoked — no .go/.rb/.java/.php/.kt/.vue files present


def test_run_scan_missing_semgrep_is_skipped_not_failed(tmp_path, monkeypatch):
    (tmp_path / "main.go").write_text("package main\n", encoding="utf-8")
    monkeypatch.setattr(vs, "_which", lambda tool: None)
    result = vs.run_scan(str(tmp_path))
    assert result["tools_run"] == []
    assert len(result["tools_skipped"]) == 1
    assert result["tools_skipped"][0]["tool"] == "semgrep"
    assert result["passed"] is True


# ---------------------------------------------------------------------------
# CLI behavior (no real bandit/eslint required)
# ---------------------------------------------------------------------------

def test_cli_missing_src_warns_and_exits_zero():
    result = _run()
    assert "not configured" in result.stdout
    assert result.returncode == 0


def test_cli_nonexistent_src_errors():
    result = _run("--src", "/this/path/does/not/exist")
    assert result.returncode == 2


def test_cli_list_tools_exits_zero():
    result = _run("--list-tools")
    assert "bandit" in result.stdout
    assert "eslint" in result.stdout
    assert result.returncode == 0


def test_cli_empty_src_dir_passes(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    result = _run("--src", str(src), "--strict")
    assert result.returncode == 0
    assert "nothing to scan" in result.stdout


# ---------------------------------------------------------------------------
# print_report — --llm-review coverage tip
#
# A SAST rule match only means a known-unsafe *pattern* was found, not that it's
# exploitable in context -- the tip nudges toward --llm-review's context-aware pass
# for exactly the findings worth a second look, reusing severity this scan already
# computed rather than inventing a new heuristic to decide when to suggest it.
# ---------------------------------------------------------------------------

def _result(findings: list[dict]) -> dict:
    return {
        "src": "src/", "tools_run": ["bandit"], "tools_skipped": [],
        "findings": findings, "blocking_findings": 0, "passed": True,
    }


def test_medium_finding_triggers_llm_review_tip(capsys):
    vs.print_report(_result([
        {"tool": "bandit", "file": "app.py", "line": 3, "severity": "medium", "rule": "B101", "message": "x"},
    ]), "medium")
    out = capsys.readouterr().out
    assert "[TIP]" in out
    assert "--llm-review" in out
    assert "1 medium+" in out


def test_high_finding_also_triggers_llm_review_tip(capsys):
    vs.print_report(_result([
        {"tool": "bandit", "file": "app.py", "line": 3, "severity": "high", "rule": "B602", "message": "x"},
    ]), "medium")
    assert "[TIP]" in capsys.readouterr().out


def test_low_only_finding_does_not_trigger_llm_review_tip(capsys):
    vs.print_report(_result([
        {"tool": "bandit", "file": "app.py", "line": 3, "severity": "low", "rule": "B101", "message": "x"},
    ]), "medium")
    assert "--llm-review" not in capsys.readouterr().out


def test_no_findings_does_not_trigger_llm_review_tip(capsys):
    vs.print_report(_result([]), "medium")
    assert "--llm-review" not in capsys.readouterr().out


def test_llm_review_already_run_suppresses_the_tip(capsys):
    """No point suggesting --llm-review again when this same invocation already ran it."""
    vs.print_report(
        _result([
            {"tool": "bandit", "file": "app.py", "line": 3, "severity": "high", "rule": "B602", "message": "x"},
        ]),
        "medium", llm_review_run=True,
    )
    assert "[TIP]" not in capsys.readouterr().out


def test_multiple_medium_plus_findings_counted_together(capsys):
    vs.print_report(_result([
        {"tool": "bandit", "file": "a.py", "line": 1, "severity": "medium", "rule": "B101", "message": "x"},
        {"tool": "bandit", "file": "b.py", "line": 2, "severity": "high", "rule": "B602", "message": "y"},
        {"tool": "bandit", "file": "c.py", "line": 3, "severity": "low", "rule": "B404", "message": "z"},
    ]), "medium")
    assert "2 medium+" in capsys.readouterr().out


# ---------------------------------------------------------------------------
# Telemetry — regression coverage for the dict/positional schema drift: this validator
# used to call _append_telemetry() with the positional-args convention ('script'/'status'
# keys), diverging from the 'validator'/'level' schema every other validator writes and
# README.md's validation-result.json documents. Fixed to use the dict convention; this
# test guards it from silently reverting.
# ---------------------------------------------------------------------------

def test_telemetry_uses_validator_and_level_keys_not_script_and_status(tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "app.py").write_text("def safe():\n    return 1\n", encoding="utf-8")
    result = subprocess.run(
        [sys.executable, str(SCRIPT), "--src", str(src), "--project-type", "cli-tool"],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        cwd=str(tmp_path),
    )
    assert result.returncode == 0, result.stdout + result.stderr
    telemetry_file = tmp_path / ".ai" / "telemetry" / "validation-result.json"
    assert telemetry_file.exists()
    rows = json.loads(telemetry_file.read_text(encoding="utf-8"))
    assert len(rows) == 1
    row = rows[0]
    assert row["validator"] == "verify_security.py"
    assert row["level"] in ("pass", "fail")
    assert row["project_type"] == "cli-tool"
    assert "script" not in row
    assert "status" not in row
