"""What is LEFT of the Sprint Documentation Sync guard in .githooks/pre-commit.

The Pending-count / stale-age check moved to .githooks/pre-push (see
test_pre_push_sprint_sync.py): a Pending backlog is a handover problem, so it blocks a push to a
gated branch instead of blocking every commit. Two things stay at commit time:

- committing must NOT be blocked by a Pending backlog any more, and
- a malformed sprint_sync_stale_days value still fails fast, so a config typo is caught early
  rather than silently disabling the age-based fallback until the next push.

Runs the real bash script via subprocess against a minimal isolated git repo -- skipped if bash
isn't on PATH.
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


def _make_repo(tmp_path: Path, sprint_log_body: str | None, extra_config: str = "") -> Path:
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
    assert _BASH is not None
    return subprocess.run(
        [_BASH, str(HOOK)], cwd=repo, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )


def test_pending_backlog_no_longer_blocks_a_commit(tmp_path):
    body = "# Sprint Change Log\n\n" + "".join(_PENDING_ENTRY.format(n=n) for n in ("A", "B", "C", "D"))
    result = _run_hook(_make_repo(tmp_path, body))
    assert "Pending documentation synchronization" not in result.stdout
    assert result.returncode == 0


def test_invalid_sprint_sync_stale_days_still_fails_at_commit(tmp_path):
    """A non-numeric value is a config error, not a silent no-op -- must fail fast with
    a clear message, same convention as the spec_code_adapter typo guard."""
    repo = _make_repo(tmp_path, sprint_log_body=None, extra_config="sprint_sync_stale_days: two weeks\n")
    result = _run_hook(repo)
    assert "sprint_sync_stale_days" in result.stdout
    assert "not a positive integer" in result.stdout
    assert result.returncode == 1
