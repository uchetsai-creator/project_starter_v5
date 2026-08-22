"""Tests for the --semantic coverage tip in verify_spec_code.py.

A structural pass from compare() only means no field was added, removed, or retyped --
it says nothing about whether the code behind an unchanged field's signature still
does what the spec describes (behavior can change inside a function body without
touching its signature at all). print_report() now suggests --semantic when a
structural pass coincides with a large change under --src since HEAD -- a purely
quantitative signal (git diff --numstat line count), deliberately not a fuzzy
name/type similarity heuristic, which risked either spamming false suggestions or
silently missing real drift (see docs/architecture-analysis.md for the full
rationale).

_changed_lines_in_src() is tested against a real git repo (it shells out to `git
diff`); print_report()'s tip logic is tested with that function monkeypatched, to
isolate "does the tip fire on the right report shape" from "does the git plumbing
work" -- matching test_verify_spec_code_zero_coverage.py's direct-import style.
"""
import subprocess
import sys
from pathlib import Path

_VALIDATORS_DIR = Path(__file__).resolve().parent.parent.parent / "templates/script/validators"
sys.path.insert(0, str(_VALIDATORS_DIR))

import verify_spec_code as vsc  # noqa: E402

_CLEAN_REPORT: dict = {
    'missing_in_code': [], 'extra_in_code': [], 'field_mismatches': [],
}
_MISMATCH_REPORT: dict = {
    'missing_in_code': ['Order.total'], 'extra_in_code': [], 'field_mismatches': [],
}


def _make_git_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    return repo


# ---------------------------------------------------------------------------
# _changed_lines_in_src — real git repo
# ---------------------------------------------------------------------------

def test_changed_lines_counts_added_and_removed(tmp_path):
    repo = _make_git_repo(tmp_path)
    src = repo / "app.py"
    src.write_text("line1\nline2\nline3\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "base"], cwd=repo, check=True)

    src.write_text("line1\nCHANGED2\nCHANGED3\nline4\n", encoding="utf-8")

    # cwd matters for `git diff` -- run from inside the repo like the real caller would.
    import os
    old_cwd = os.getcwd()
    try:
        os.chdir(repo)
        result = vsc._changed_lines_in_src(str(src.relative_to(repo)))
    finally:
        os.chdir(old_cwd)
    assert result is not None
    assert result > 0


def test_changed_lines_zero_for_unmodified_file(tmp_path):
    import os
    repo = _make_git_repo(tmp_path)
    src = repo / "app.py"
    src.write_text("line1\nline2\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "base"], cwd=repo, check=True)

    old_cwd = os.getcwd()
    try:
        os.chdir(repo)
        result = vsc._changed_lines_in_src(str(src.relative_to(repo)))
    finally:
        os.chdir(old_cwd)
    assert result == 0


def test_changed_lines_returns_none_outside_a_git_repo(tmp_path):
    import os
    not_a_repo = tmp_path / "not_a_repo"
    not_a_repo.mkdir()
    (not_a_repo / "app.py").write_text("x\n", encoding="utf-8")

    old_cwd = os.getcwd()
    try:
        os.chdir(not_a_repo)
        result = vsc._changed_lines_in_src("app.py")
    finally:
        os.chdir(old_cwd)
    assert result is None


# ---------------------------------------------------------------------------
# print_report — tip logic (with _changed_lines_in_src monkeypatched)
# ---------------------------------------------------------------------------

def test_clean_pass_with_large_change_triggers_tip(monkeypatch, capsys):
    monkeypatch.setattr(vsc, "_changed_lines_in_src", lambda src: 25)
    vsc.print_report(_CLEAN_REPORT, "spec.md", "src/", "fastapi")
    out = capsys.readouterr().out
    assert "[TIP]" in out
    assert "--semantic" in out
    assert "25 line(s)" in out


def test_clean_pass_with_small_change_does_not_trigger_tip(monkeypatch, capsys):
    monkeypatch.setattr(vsc, "_changed_lines_in_src", lambda src: 3)
    vsc.print_report(_CLEAN_REPORT, "spec.md", "src/", "fastapi")
    assert "--semantic" not in capsys.readouterr().out


def test_clean_pass_at_exact_threshold_triggers_tip(monkeypatch, capsys):
    monkeypatch.setattr(vsc, "_changed_lines_in_src", lambda src: vsc._SEMANTIC_TIP_LINE_THRESHOLD)
    vsc.print_report(_CLEAN_REPORT, "spec.md", "src/", "fastapi")
    assert "[TIP]" in capsys.readouterr().out


def test_git_unavailable_does_not_trigger_tip(monkeypatch, capsys):
    monkeypatch.setattr(vsc, "_changed_lines_in_src", lambda src: None)
    vsc.print_report(_CLEAN_REPORT, "spec.md", "src/", "fastapi")
    assert "--semantic" not in capsys.readouterr().out


def test_semantic_already_run_suppresses_the_tip(monkeypatch, capsys):
    monkeypatch.setattr(vsc, "_changed_lines_in_src", lambda src: 999)
    vsc.print_report(_CLEAN_REPORT, "spec.md", "src/", "fastapi", semantic_run=True)
    assert "[TIP]" not in capsys.readouterr().out


def test_report_with_mismatches_does_not_trigger_the_tip(monkeypatch, capsys):
    """The tip is specifically for a *clean structural pass* alongside a large
    change -- if mismatches were already found, --semantic wouldn't be adding
    coverage the deterministic pass is missing; it's addressing a different gap."""
    monkeypatch.setattr(vsc, "_changed_lines_in_src", lambda src: 999)
    vsc.print_report(_MISMATCH_REPORT, "spec.md", "src/", "fastapi")
    assert "--semantic" not in capsys.readouterr().out
