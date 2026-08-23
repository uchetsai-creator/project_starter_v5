"""Tests for the Sprint Documentation Sync guard in .githooks/pre-commit.

templates/sprint-sync.md documents a count trigger: as soon as docs/sprint-change-log.md
has 3 entries at "Status: Pending documentation synchronization", Sprint Documentation
Sync (templates/sprint-sync.md) should run before starting the next task. Nothing
previously verified that actually happened -- it was pure convention (AGENTS.md ->
Sprint Documentation Sync + the sprint-doc-sync Skill nudge), so the Pending backlog
could grow indefinitely with no mechanical backstop. This guard closes that gap: once
the count reaches 3, every commit is blocked until sync marks entries "Documentation
synchronized" and the count drops back below 3.

Reads the working-tree file directly (not staged content), like the
project_type_confirmed guard -- what matters is whether the fix has actually landed on
disk, not whether this particular commit is the one that did it.

Runs the real bash script via subprocess against a minimal isolated git repo, matching
test_pre_commit_project_type_confirmed.py's approach -- skipped if bash isn't on PATH.
"""
import subprocess
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from tests.conftest import find_posix_bash

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
HOOK = REPO_ROOT / ".githooks" / "pre-commit"

_BASH = find_posix_bash()
pytestmark = pytest.mark.skipif(_BASH is None, reason="bash not found on PATH")

_PENDING_ENTRY = "### Task: {n}\n**Status:** Pending documentation synchronization\n---\n\n"
_SYNCED_ENTRY = "### Task: {n}\n**Status:** Documentation synchronized — 2026-08-22\n---\n\n"
_PENDING_ENTRY_DATED = (
    "### Task: {n}\n**Date:** {date}\n**Status:** Pending documentation synchronization\n---\n\n"
)


def _make_repo(
    tmp_path: Path, sprint_log_body: str | None, extra_config: str = "",
) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)

    (repo / ".project-starter.yml").write_text(
        "project_type: web-app\ndocs_path: docs/\n" + extra_config, encoding="utf-8",
    )
    docs = repo / "docs"
    docs.mkdir()
    (docs / "current-state.md").write_text("# Current State\n", encoding="utf-8")
    if sprint_log_body is not None:
        (docs / "sprint-change-log.md").write_text(sprint_log_body, encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)

    return repo


def _run_hook(repo: Path) -> subprocess.CompletedProcess:
    assert _BASH is not None  # module-level skipif guarantees this by the time we get here
    return subprocess.run(
        [_BASH, str(HOOK)], cwd=repo, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )


def test_three_pending_entries_blocks_commit(tmp_path):
    body = "# Sprint Change Log\n\n" + "".join(
        _PENDING_ENTRY.format(n=n) for n in ("A", "B", "C")
    )
    repo = _make_repo(tmp_path, body)
    result = _run_hook(repo)
    assert "3 entries at 'Pending documentation synchronization'" in result.stdout
    assert result.returncode == 1


def test_two_pending_entries_does_not_block(tmp_path):
    body = "# Sprint Change Log\n\n" + "".join(
        _PENDING_ENTRY.format(n=n) for n in ("A", "B")
    )
    repo = _make_repo(tmp_path, body)
    result = _run_hook(repo)
    assert "Pending documentation synchronization" not in result.stdout
    assert result.returncode == 0


def test_synced_entries_are_not_counted_as_pending(tmp_path):
    """2 synced + 2 pending -- only the Pending ones count toward the threshold."""
    body = (
        "# Sprint Change Log\n\n"
        + _SYNCED_ENTRY.format(n="A")
        + _SYNCED_ENTRY.format(n="B")
        + _PENDING_ENTRY.format(n="C")
        + _PENDING_ENTRY.format(n="D")
    )
    repo = _make_repo(tmp_path, body)
    result = _run_hook(repo)
    assert "Pending documentation synchronization" not in result.stdout
    assert result.returncode == 0


def test_four_pending_entries_still_blocks(tmp_path):
    """>= 3, not == 3 -- the backlog growing past the threshold must still block."""
    body = "# Sprint Change Log\n\n" + "".join(
        _PENDING_ENTRY.format(n=n) for n in ("A", "B", "C", "D")
    )
    repo = _make_repo(tmp_path, body)
    result = _run_hook(repo)
    assert "4 entries at 'Pending documentation synchronization'" in result.stdout
    assert result.returncode == 1


def test_no_sprint_change_log_does_not_block(tmp_path):
    """A fresh project (or one with no completed tasks yet) has no sprint-change-log.md
    at all -- must not crash or false-positive."""
    repo = _make_repo(tmp_path, sprint_log_body=None)
    result = _run_hook(repo)
    assert "Pending documentation synchronization" not in result.stdout
    assert result.returncode == 0


# ── Age-based fallback (sprint_sync_stale_days) ─────────────────────────────────
# Closes the gap above these tests: a low-volume/solo project that never accumulates
# 3 Pending entries never trips the count guard, so the backlog can sit indefinitely
# with no mechanical backstop. sprint_sync_stale_days is opt-in (blank = count-only,
# matching all tests above) -- these tests cover it explicitly configured.

def test_stale_single_pending_entry_blocks_when_configured(tmp_path):
    old_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    body = "# Sprint Change Log\n\n" + _PENDING_ENTRY_DATED.format(n="A", date=old_date)
    repo = _make_repo(tmp_path, body, extra_config="sprint_sync_stale_days: 14\n")
    result = _run_hook(repo)
    assert "entry(ies) pending" in result.stdout
    assert old_date in result.stdout
    assert result.returncode == 1


def test_recent_single_pending_entry_does_not_block_when_configured(tmp_path):
    today = datetime.now().strftime("%Y-%m-%d")
    body = "# Sprint Change Log\n\n" + _PENDING_ENTRY_DATED.format(n="A", date=today)
    repo = _make_repo(tmp_path, body, extra_config="sprint_sync_stale_days: 14\n")
    result = _run_hook(repo)
    assert "entry(ies) pending" not in result.stdout
    assert result.returncode == 0


def test_stale_pending_entry_does_not_block_without_config(tmp_path):
    """Same stale entry as the blocking test above, but sprint_sync_stale_days is left
    unset -- default behavior must stay count-only, unchanged from before this fallback
    existed."""
    old_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
    body = "# Sprint Change Log\n\n" + _PENDING_ENTRY_DATED.format(n="A", date=old_date)
    repo = _make_repo(tmp_path, body)
    result = _run_hook(repo)
    assert "entry(ies) pending" not in result.stdout
    assert result.returncode == 0


def test_oldest_of_multiple_pending_entries_is_used(tmp_path):
    """2 Pending entries (below the count threshold of 3) -- the OLDER date should be
    the one that trips the fallback, since entries are chronological (oldest first)."""
    older = (datetime.now() - timedelta(days=20)).strftime("%Y-%m-%d")
    newer = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
    body = (
        "# Sprint Change Log\n\n"
        + _PENDING_ENTRY_DATED.format(n="A", date=older)
        + _PENDING_ENTRY_DATED.format(n="B", date=newer)
    )
    repo = _make_repo(tmp_path, body, extra_config="sprint_sync_stale_days: 14\n")
    result = _run_hook(repo)
    assert older in result.stdout
    assert newer not in result.stdout
    assert result.returncode == 1


def test_invalid_sprint_sync_stale_days_fails_clearly(tmp_path):
    """A non-numeric value is a config error, not a silent no-op -- must fail fast with
    a clear message, same convention as the spec_code_adapter typo guard."""
    repo = _make_repo(tmp_path, sprint_log_body=None, extra_config="sprint_sync_stale_days: two weeks\n")
    result = _run_hook(repo)
    assert "sprint_sync_stale_days" in result.stdout
    assert "not a positive integer" in result.stdout
    assert result.returncode == 1
