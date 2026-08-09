"""Tests for adapters/claude/learning_log_nudge.py -- the SessionStart nudge that
surfaces when docs/task-log.md was closed out more recently than learning-log.md was
last touched. Never a gate (see the module docstring for why) -- these tests confirm
it stays silent whenever the signal is missing or ambiguous, and only speaks up in the
one unambiguous case: a committed task-log.md entry with no learning-log.md commit since.
"""
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "adapters" / "claude"))

import learning_log_nudge as nudge  # noqa: E402


def _git(cwd: Path, *args: str, ts: int | None = None) -> None:
    env = None
    if ts is not None:
        import os
        env = {**os.environ, "GIT_AUTHOR_DATE": f"{ts} +0000", "GIT_COMMITTER_DATE": f"{ts} +0000"}
    subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True,
        text=True, encoding="utf-8", errors="replace", env=env,
    )


def _init_repo(tmp_path: Path) -> None:
    _git(tmp_path, "init", "-q")
    _git(tmp_path, "config", "user.email", "a@b.c")
    _git(tmp_path, "config", "user.name", "test")


def test_no_learning_log_file_is_silent(tmp_path):
    assert nudge.decide(str(tmp_path)) is None


def test_no_committed_task_log_is_silent(tmp_path):
    (tmp_path / "learning-log.md").write_text("# Learning Log\n", encoding="utf-8")
    _init_repo(tmp_path)
    assert nudge.decide(str(tmp_path)) is None  # nothing closed out yet -- nothing to compare


def test_task_log_committed_after_learning_log_produces_reminder(tmp_path):
    (tmp_path / "learning-log.md").write_text("# Learning Log\n", encoding="utf-8")
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "task-log.md").write_text("# Task Log\n", encoding="utf-8")
    _init_repo(tmp_path)
    _git(tmp_path, "add", "learning-log.md")
    _git(tmp_path, "commit", "-q", "-m", "learning log", ts=1_700_000_000)
    _git(tmp_path, "add", "docs/task-log.md")
    _git(tmp_path, "commit", "-q", "-m", "task closeout", ts=1_700_000_100)

    msg = nudge.decide(str(tmp_path))
    assert msg is not None
    assert "learning-log.md" in msg


def test_learning_log_committed_after_task_log_is_silent(tmp_path):
    (tmp_path / "learning-log.md").write_text("# Learning Log\n", encoding="utf-8")
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "task-log.md").write_text("# Task Log\n", encoding="utf-8")
    _init_repo(tmp_path)
    _git(tmp_path, "add", "docs/task-log.md")
    _git(tmp_path, "commit", "-q", "-m", "task closeout", ts=1_700_000_000)
    _git(tmp_path, "add", "learning-log.md")
    _git(tmp_path, "commit", "-q", "-m", "learning log", ts=1_700_000_100)

    assert nudge.decide(str(tmp_path)) is None


def test_not_a_git_repo_is_silent(tmp_path):
    (tmp_path / "learning-log.md").write_text("# Learning Log\n", encoding="utf-8")
    (tmp_path / "docs").mkdir()
    (tmp_path / "docs" / "task-log.md").write_text("# Task Log\n", encoding="utf-8")
    assert nudge.decide(str(tmp_path)) is None
