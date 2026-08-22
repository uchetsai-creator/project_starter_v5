"""Tests for the Doc Checklist completeness guard in .githooks/pre-commit.

current-state.md's "Closing out a task" convention (AGENTS.md) says: at task setup, copy
build-context.py's filtered doc list into the Doc Checklist section; at closeout, apply
each item and check it off. Nothing previously verified that actually happened — a task
could be marked Status: Complete with every Doc Checklist item still unchecked (or the
raw, never-customized template placeholder still in place) and nothing would block the
commit. This guard closes that gap, reusing the checklist's own `- [ ]` / `- [x]` state
directly rather than adding a separate summary field that could just as easily say "done"
without the underlying items being checked off.

Same trigger condition as the existing (untested until now) Closeout completeness guard
in this same script: current-state.md staged with Status containing "Complete".

Runs the real bash script via subprocess against a minimal isolated git repo, matching
test_pre_commit_project_type_confirmed.py's approach — skipped if bash isn't on PATH.
"""
import subprocess
from pathlib import Path

import pytest

from tests.conftest import find_posix_bash

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
HOOK = REPO_ROOT / ".githooks" / "pre-commit"

_BASH = find_posix_bash()
pytestmark = pytest.mark.skipif(_BASH is None, reason="bash not found on PATH")

_HEADER = (
    "## Current Task\n\n"
    "**Task:** Build the order API\n\n"
    "**Clarifying Questions Asked:** Y\n\n"
)

_CLOSEOUT_FOOTER = "\n## Closeout (when all Steps and Verify are done)\n\n- Everything done: yes\n"


def _make_repo(tmp_path: Path, current_state_body: str) -> Path:
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
    (docs / "current-state.md").write_text(current_state_body, encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)

    return repo


def _run_hook(repo: Path) -> subprocess.CompletedProcess:
    assert _BASH is not None  # module-level skipif guarantees this by the time we get here
    return subprocess.run(
        [_BASH, str(HOOK)], cwd=repo, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )


def test_complete_with_unchecked_item_blocks_commit(tmp_path):
    body = (
        _HEADER + "**Status:** Complete — Pending Sprint Doc Sync\n\n"
        "## Doc Checklist (this task only)\n\n"
        "- [x] `docs/specs/api-contract.md` — endpoint added\n"
        "- [ ] `docs/architecture/architecture.md` — check if diagram needs updating\n"
        + _CLOSEOUT_FOOTER
    )
    repo = _make_repo(tmp_path, body)
    result = _run_hook(repo)
    assert "Doc Checklist has an unchecked item" in result.stdout
    assert result.returncode == 1


def test_complete_with_raw_template_placeholder_blocks_commit(tmp_path):
    body = (
        _HEADER + "**Status:** Complete — Pending Sprint Doc Sync\n\n"
        "## Doc Checklist (this task only)\n\n"
        "- [ ] `docs/[relevant spec]` — [what to check / update]\n"
        + _CLOSEOUT_FOOTER
    )
    repo = _make_repo(tmp_path, body)
    result = _run_hook(repo)
    assert "Doc Checklist has an unchecked item" in result.stdout
    assert result.returncode == 1


def test_complete_with_all_items_checked_does_not_block(tmp_path):
    body = (
        _HEADER + "**Status:** Complete — Pending Sprint Doc Sync\n\n"
        "## Doc Checklist (this task only)\n\n"
        "- [x] `docs/specs/api-contract.md` — endpoint added\n"
        "- [x] `docs/architecture/architecture.md` — no changes needed\n"
        + _CLOSEOUT_FOOTER
    )
    repo = _make_repo(tmp_path, body)
    result = _run_hook(repo)
    assert "Doc Checklist" not in result.stdout
    assert result.returncode == 0


def test_in_progress_status_does_not_trigger_the_guard(tmp_path):
    """An unchecked item is completely normal mid-task -- the guard must only fire once
    the task claims to be Complete, not for every task that hasn't finished yet."""
    body = (
        _HEADER + "**Status:** In Progress\n\n"
        "## Doc Checklist (this task only)\n\n"
        "- [ ] `docs/[relevant spec]` — [what to check / update]\n"
        "\n## Closeout (when all Steps and Verify are done)\n\n- Everything done: no\n"
    )
    repo = _make_repo(tmp_path, body)
    result = _run_hook(repo)
    assert "Doc Checklist" not in result.stdout
    assert result.returncode == 0


def test_current_state_not_staged_does_not_crash():
    """Covered implicitly by every pre-commit test that omits current-state.md changes;
    asserted directly here for this guard's own regression coverage (set -u would turn an
    unguarded reference into a hard failure if this weren't handled)."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = Path(tmpdir) / "repo"
        repo.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        result = _run_hook(repo)
        assert "Doc Checklist" not in (result.stdout + result.stderr)
