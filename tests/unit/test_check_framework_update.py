"""Tests for adapters/claude/check_framework_update.py -- the SessionStart nudge that
compares .project-starter.yml's framework_commit against project_starter_v5's current
upstream HEAD (see session-start-hook.sh, which invokes this as a subprocess).

Uses a local git repo (via `git init` + `git ls-remote <local-path>`) standing in for the
real GitHub upstream -- `git ls-remote` works identically against a local path, no network
needed, so these tests don't depend on real connectivity to github.com.
"""
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCRIPT = REPO_ROOT / "adapters" / "claude" / "check_framework_update.py"


def _git(*args: str, cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def _make_upstream_repo(tmp_path: Path) -> tuple[Path, str]:
    upstream = tmp_path / "upstream"
    upstream.mkdir()
    _git("init", "-q", "-b", "main", cwd=upstream)
    _git("config", "user.email", "test@example.com", cwd=upstream)
    _git("config", "user.name", "Test", cwd=upstream)
    (upstream / "README.md").write_text("hello\n", encoding="utf-8")
    _git("add", ".", cwd=upstream)
    _git("commit", "-q", "-m", "initial", cwd=upstream)
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=upstream, capture_output=True, text=True, check=True,
    ).stdout.strip()
    return upstream, head


def _run(cwd: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT)], cwd=cwd, capture_output=True, text=True, encoding="utf-8",
    )


def test_no_config_file_produces_no_output(tmp_path):
    result = _run(tmp_path)
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_blank_framework_commit_produces_no_output(tmp_path):
    (tmp_path / ".project-starter.yml").write_text(
        "project_type: web-app\nframework_commit:\n", encoding="utf-8",
    )
    result = _run(tmp_path)
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_up_to_date_commit_produces_no_output(tmp_path):
    upstream, head = _make_upstream_repo(tmp_path)
    (tmp_path / ".project-starter.yml").write_text(
        f"project_type: web-app\nframework_commit: {head}\nframework_repo_url: {upstream}\n",
        encoding="utf-8",
    )
    result = _run(tmp_path)
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_stale_commit_produces_update_nudge(tmp_path):
    upstream, old_head = _make_upstream_repo(tmp_path)
    (upstream / "README.md").write_text("hello again\n", encoding="utf-8")
    _git("add", ".", cwd=upstream)
    _git("commit", "-q", "-m", "second commit", cwd=upstream)
    new_head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=upstream, capture_output=True, text=True, check=True,
    ).stdout.strip()

    (tmp_path / ".project-starter.yml").write_text(
        f"project_type: web-app\nframework_commit: {old_head}\nframework_repo_url: {upstream}\n",
        encoding="utf-8",
    )
    result = _run(tmp_path)
    assert result.returncode == 0
    assert "project_starter_v5" in result.stdout
    assert old_head[:12] in result.stdout
    assert new_head[:12] in result.stdout
    assert "AskUserQuestion" in result.stdout
    assert "retrofit-existing-project" in result.stdout


def test_unreachable_repo_url_produces_no_output(tmp_path):
    (tmp_path / ".project-starter.yml").write_text(
        "project_type: web-app\n"
        "framework_commit: 0000000000000000000000000000000000000\n"
        f"framework_repo_url: {tmp_path / 'does-not-exist'}\n",
        encoding="utf-8",
    )
    result = _run(tmp_path)
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_default_repo_url_used_when_unset(tmp_path):
    """Doesn't hit the network (framework_commit deliberately won't match anything real),
    just confirms the default-URL branch doesn't crash and still exits cleanly."""
    (tmp_path / ".project-starter.yml").write_text(
        "project_type: web-app\nframework_commit: deadbeefdeadbeefdeadbeefdeadbeefdeadbeef\n",
        encoding="utf-8",
    )
    result = _run(tmp_path)
    assert result.returncode == 0
