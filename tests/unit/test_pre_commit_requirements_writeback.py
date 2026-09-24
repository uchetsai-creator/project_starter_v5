"""Tests for the "Clarifications written back to the spec" guard in .githooks/pre-commit.

Answers the user gave during clarification live in current-state.md, which is overwritten at
the next task. At closeout (Status Complete), when current-state.md has a "## Clarifications"
section, the Doc Checklist must contain a CHECKED line naming project-requirements so the answers
reach the spec every later task reads. The check only applies when the section exists, and only
confirms the box was ticked, not that the spec text is right.

Runs the real bash script via subprocess against a minimal isolated git repo, matching
test_pre_commit_doc_checklist.py -- skipped if bash isn't on PATH.
"""
import subprocess
from pathlib import Path

import pytest

from tests.conftest import find_posix_bash

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
HOOK = REPO_ROOT / ".githooks" / "pre-commit"

_BASH = find_posix_bash()
pytestmark = pytest.mark.skipif(_BASH is None, reason="bash not found on PATH")

_MESSAGE = "Doc Checklist has no checked"


def _state(checklist: str, clarifications: bool = True) -> str:
    body = (
        "## Current Task\n\n**Task:** Build the order API\n\n"
        "**Clarifying Questions Asked:** Y\n\n"
        "**Status:** Complete — Pending Sprint Doc Sync\n\n"
    )
    if clarifications:
        body += "## Clarifications\n\n- **Goal & scope:** orders API for staff\n\n"
    body += "## Doc Checklist (this task only)\n\n" + checklist + "\n## Closeout (when done)\n\nDone.\n"
    return body


def _make_repo(tmp_path: Path, current_state_body: str) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    (repo / ".project-starter.yml").write_text(
        "project_type: web-app\ndocs_path: docs/\ntask_type:\n"
        "spec_code_adapter:\nspec_code_spec:\nspec_code_src:\n",
        encoding="utf-8",
    )
    docs = repo / "docs"
    docs.mkdir()
    (docs / "current-state.md").write_text(current_state_body, encoding="utf-8")
    subprocess.run(["git", "add", "docs/current-state.md", ".project-starter.yml"], cwd=repo, check=True)
    return repo


def _run_hook(repo: Path) -> subprocess.CompletedProcess:
    assert _BASH is not None
    return subprocess.run(
        [_BASH, str(HOOK)], cwd=repo, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )


def test_complete_without_requirements_line_is_blocked(tmp_path):
    result = _run_hook(_make_repo(tmp_path, _state("- [x] `docs/architecture/architecture.md` — updated\n")))
    assert _MESSAGE in result.stdout
    assert result.returncode == 1


def test_complete_with_unchecked_requirements_line_is_blocked(tmp_path):
    result = _run_hook(_make_repo(tmp_path, _state("- [ ] `docs/project-requirements.md` — write back\n")))
    assert _MESSAGE in result.stdout
    assert result.returncode == 1


def test_complete_with_checked_requirements_line_passes(tmp_path):
    result = _run_hook(_make_repo(tmp_path, _state("- [x] `docs/project-requirements.md` — AC-001..003 added\n")))
    assert _MESSAGE not in result.stdout
    assert result.returncode == 0


def test_uppercase_x_counts_as_checked(tmp_path):
    result = _run_hook(_make_repo(tmp_path, _state("- [X] `docs/project-requirements.md` — written\n")))
    assert _MESSAGE not in result.stdout
    assert result.returncode == 0


def test_section_absent_is_not_covered(tmp_path):
    """current-state.md files that predate the Clarifications section keep working."""
    body = _state("- [x] `docs/architecture/architecture.md` — updated\n", clarifications=False)
    result = _run_hook(_make_repo(tmp_path, body))
    assert _MESSAGE not in result.stdout
    assert result.returncode == 0


def test_in_progress_task_is_not_checked(tmp_path):
    body = _state("- [ ] `docs/project-requirements.md` — write back\n").replace(
        "Complete — Pending Sprint Doc Sync", "In Progress")
    result = _run_hook(_make_repo(tmp_path, body))
    assert _MESSAGE not in result.stdout
    assert result.returncode == 0
