"""Tests for the Approach Confirmed guard in .githooks/pre-commit.

Clarifying Questions Asked settles WHAT is being built. Approach Confirmed records that the
proposed task breakdown and implementation approach were then shown to the user and
confirmed or adjusted BEFORE any code was written (AGENTS.md -> New requirement from the
user, Learning Checkpoint B item 2). The guard only applies when current-state.md has the
field, so a current-state.md that predates it is not blocked.

Runs the real bash script via subprocess against a minimal isolated git repo, matching
test_pre_commit_clarifying_questions.py -- skipped if bash isn't on PATH.
"""
import subprocess
from pathlib import Path

import pytest

from tests.conftest import find_posix_bash

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
HOOK = REPO_ROOT / ".githooks" / "pre-commit"

_BASH = find_posix_bash()
pytestmark = pytest.mark.skipif(_BASH is None, reason="bash not found on PATH")

_MESSAGE = "Approach Confirmed is still a placeholder or not Y/N/A"


def _make_repo(tmp_path: Path, current_state_body: str, staged_source: bool = False) -> Path:
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
    to_add = ["docs/current-state.md", ".project-starter.yml"]
    if staged_source:
        (repo / "app.py").write_text("print('hello')\n", encoding="utf-8")
        to_add.append("app.py")
    subprocess.run(["git", "add", *to_add], cwd=repo, check=True)
    return repo


def _run_hook(repo: Path) -> subprocess.CompletedProcess:
    assert _BASH is not None
    return subprocess.run(
        [_BASH, str(HOOK)], cwd=repo, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )


def _state(approach_line: str | None) -> str:
    body = (
        "## Current Task\n\n"
        "**Task:** Build the order API\n\n"
        "**Clarifying Questions Asked:** Y\n"
    )
    if approach_line is not None:
        body += f"\n**Approach Confirmed:** {approach_line}\n"
    return body


def test_field_absent_is_not_blocked(tmp_path):
    """current-state.md files that predate the field keep working."""
    result = _run_hook(_make_repo(tmp_path, _state(None)))
    assert "Approach Confirmed" not in result.stdout
    assert result.returncode == 0


def test_placeholder_blocks_commit(tmp_path):
    result = _run_hook(_make_repo(tmp_path, _state("[Y / N/A — reason]")))
    assert _MESSAGE in result.stdout
    assert result.returncode == 1


def test_invalid_value_blocks_commit(tmp_path):
    result = _run_hook(_make_repo(tmp_path, _state("N")))
    assert _MESSAGE in result.stdout
    assert result.returncode == 1


def test_y_passes(tmp_path):
    result = _run_hook(_make_repo(tmp_path, _state("Y")))
    assert _MESSAGE not in result.stdout
    assert result.returncode == 0


def test_na_with_reason_passes(tmp_path):
    result = _run_hook(_make_repo(tmp_path, _state("N/A — single obvious change")))
    assert _MESSAGE not in result.stdout
    assert result.returncode == 0


def test_placeholder_task_skips_the_guard(tmp_path):
    body = (
        "## Current Task\n\n**Task:** [Task name, e.g., BE Order API]\n\n"
        "**Approach Confirmed:** [Y / N/A — reason]\n"
    )
    result = _run_hook(_make_repo(tmp_path, body))
    assert "Approach Confirmed" not in result.stdout
    assert result.returncode == 0


def test_staged_source_with_unfilled_approach_blocks_commit(tmp_path):
    """The unscoped-source guard also checks the field, so it cannot be skipped by
    leaving current-state.md out of the commit."""
    result = _run_hook(_make_repo(tmp_path, _state("[Y / N/A — reason]"), staged_source=True))
    assert "Source files staged but Approach Confirmed is unfilled" in result.stdout
    assert result.returncode == 1


def test_staged_source_with_confirmed_approach_passes_this_guard(tmp_path):
    result = _run_hook(_make_repo(tmp_path, _state("Y"), staged_source=True))
    assert "Approach Confirmed" not in result.stdout
