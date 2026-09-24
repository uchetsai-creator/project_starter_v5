"""Tests for the Sprint Documentation Sync check in .githooks/pre-push.

templates/sprint-sync.md documents a count trigger: as soon as docs/sprint-change-log.md has 3
entries at "Status: Pending documentation synchronization", Sprint Documentation Sync should
run before the next task. Nothing verified that happened, so a backlog could grow forever. The
check lives at push time (moved from pre-commit): a push to a gated branch (main/master by
default) is blocked while the backlog is at the threshold or, when sprint_sync_stale_days is
set, while the OLDEST Pending entry is that old. Other branches only get a warning. The log is
read at the pushed commit, not the working tree.

Runs the real bash script via subprocess against a minimal isolated git repo -- skipped if bash
isn't on PATH.
"""
import os
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from tests.conftest import find_posix_bash

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
HOOK = REPO_ROOT / ".githooks" / "pre-push"

_BASH = find_posix_bash()
pytestmark = pytest.mark.skipif(_BASH is None, reason="bash not found on PATH")

ZERO = "0" * 40
_PENDING = "### Task: {n}\n**Status:** Pending documentation synchronization\n---\n\n"
_SYNCED = "### Task: {n}\n**Status:** Documentation synchronized — 2026-08-22\n---\n\n"
_PENDING_DATED = "### Task: {n}\n**Date:** {date}\n**Status:** Pending documentation synchronization\n---\n\n"


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True).stdout.strip()


def _make_repo(tmp_path: Path, log_body: str | None, extra_config: str = "") -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    (repo / ".project-starter.yml").write_text(
        "project_type: web-app\ndocs_path: docs/\n" + extra_config, encoding="utf-8",
    )
    docs = repo / "docs"
    docs.mkdir()
    (docs / "current-state.md").write_text("# Current State\n", encoding="utf-8")
    if log_body is not None:
        (docs / "sprint-change-log.md").write_text(log_body, encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "--no-verify", "-m", "init")
    return repo


def _push(repo: Path, branch: str = "main") -> subprocess.CompletedProcess:
    assert _BASH is not None
    sha = _git(repo, "rev-parse", "HEAD")
    return subprocess.run(
        [_BASH, str(HOOK)], cwd=repo, input=f"refs/heads/work {sha} refs/heads/{branch} {ZERO}\n",
        capture_output=True, text=True, encoding="utf-8", errors="replace", env=dict(os.environ),
    )


def _log(*entries: str) -> str:
    return "# Sprint Change Log\n\n" + "".join(entries)


def _days_ago(n: int) -> str:
    return (datetime.now() - timedelta(days=n)).strftime("%Y-%m-%d")


def test_three_pending_entries_block_push_to_main(tmp_path):
    result = _push(_make_repo(tmp_path, _log(*(_PENDING.format(n=n) for n in "ABC"))))
    assert result.returncode == 1
    assert "3 entries at 'Pending documentation synchronization'" in result.stdout


def test_four_pending_entries_still_block(tmp_path):
    """>= 3, not == 3."""
    result = _push(_make_repo(tmp_path, _log(*(_PENDING.format(n=n) for n in "ABCD"))))
    assert result.returncode == 1
    assert "4 entries at 'Pending documentation synchronization'" in result.stdout


def test_two_pending_entries_do_not_block(tmp_path):
    result = _push(_make_repo(tmp_path, _log(*(_PENDING.format(n=n) for n in "AB"))))
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_synced_entries_are_not_counted(tmp_path):
    body = _log(_SYNCED.format(n="A"), _SYNCED.format(n="B"), _PENDING.format(n="C"), _PENDING.format(n="D"))
    assert _push(_make_repo(tmp_path, body)).returncode == 0


def test_backlog_only_warns_on_a_work_branch(tmp_path):
    result = _push(_make_repo(tmp_path, _log(*(_PENDING.format(n=n) for n in "ABC"))), branch="wip/x")
    assert result.returncode == 0
    assert "[WARN]" in result.stdout


def test_no_sprint_change_log_does_not_block(tmp_path):
    assert _push(_make_repo(tmp_path, None)).returncode == 0


def test_backlog_is_read_at_the_pushed_commit_not_the_working_tree(tmp_path):
    """Marking entries synced on disk without committing must not let a backlogged commit through."""
    repo = _make_repo(tmp_path, _log(*(_PENDING.format(n=n) for n in "ABC")))
    (repo / "docs" / "sprint-change-log.md").write_text(_log(_SYNCED.format(n="A")), encoding="utf-8")
    assert _push(repo).returncode == 1


# ── Age-based fallback (sprint_sync_stale_days) ─────────────────────────────────

def test_stale_single_entry_blocks_when_configured(tmp_path):
    old = _days_ago(30)
    repo = _make_repo(tmp_path, _log(_PENDING_DATED.format(n="A", date=old)), "sprint_sync_stale_days: 14\n")
    result = _push(repo)
    assert result.returncode == 1
    assert "entry(ies)" in result.stdout and old in result.stdout


def test_recent_single_entry_does_not_block_when_configured(tmp_path):
    repo = _make_repo(tmp_path, _log(_PENDING_DATED.format(n="A", date=_days_ago(0))), "sprint_sync_stale_days: 14\n")
    assert _push(repo).returncode == 0


def test_stale_entry_does_not_block_without_config(tmp_path):
    repo = _make_repo(tmp_path, _log(_PENDING_DATED.format(n="A", date=_days_ago(30))))
    assert _push(repo).returncode == 0


def test_oldest_of_multiple_entries_is_used(tmp_path):
    older, newer = _days_ago(20), _days_ago(2)
    body = _log(_PENDING_DATED.format(n="A", date=older), _PENDING_DATED.format(n="B", date=newer))
    result = _push(_make_repo(tmp_path, body, "sprint_sync_stale_days: 14\n"))
    assert result.returncode == 1
    assert older in result.stdout and newer not in result.stdout


def test_invalid_stale_days_value_is_reported_at_push(tmp_path):
    repo = _make_repo(tmp_path, _log(_PENDING.format(n="A")), "sprint_sync_stale_days: two weeks\n")
    result = _push(repo)
    assert result.returncode == 1
    assert "not a positive integer" in result.stdout
