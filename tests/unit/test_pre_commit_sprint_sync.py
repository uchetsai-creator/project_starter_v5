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
from pathlib import Path

import pytest

from tests.conftest import find_posix_bash

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
HOOK = REPO_ROOT / ".githooks" / "pre-commit"

_BASH = find_posix_bash()
pytestmark = pytest.mark.skipif(_BASH is None, reason="bash not found on PATH")

_PENDING_ENTRY = "### Task: {n}\n**Status:** Pending documentation synchronization\n---\n\n"
_SYNCED_ENTRY = "### Task: {n}\n**Status:** Documentation synchronized — 2026-08-22\n---\n\n"


def _make_repo(tmp_path: Path, sprint_log_body: str | None) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)

    (repo / ".project-starter.yml").write_text(
        "project_type: web-app\ndocs_path: docs/\n", encoding="utf-8",
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
