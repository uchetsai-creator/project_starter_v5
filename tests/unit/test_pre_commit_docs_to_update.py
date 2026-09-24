"""Tests for the Approach -> Docs to update guard in .githooks/pre-commit.

When the breakdown is proposed, the docs each task updates are agreed with the user and written to
"- **Docs to update:**" in current-state.md's Approach section. It must be filled and name
project-requirements.md (always on the list). Only applies when the line exists, so older files
are not blocked. Runs the real bash script against a minimal isolated git repo.
"""
import subprocess
from pathlib import Path

import pytest

from tests.conftest import find_posix_bash

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
HOOK = REPO_ROOT / ".githooks" / "pre-commit"

_BASH = find_posix_bash()
pytestmark = pytest.mark.skipif(_BASH is None, reason="bash not found on PATH")

_MESSAGE = "Docs to update is unfilled or does not list project-requirements.md"


def _state(value: str | None, task: str = "Build the order API") -> str:
    body = (
        f"## Current Task\n\n**Task:** {task}\n\n**Clarifying Questions Asked:** Y\n\n"
        "## Approach\n\n- **Breakdown:** 3 tasks\n"
    )
    if value is not None:
        body += f"- **Docs to update:** {value}\n"
    return body


def _make_repo(tmp_path: Path, body: str, staged_source: bool = False) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    (repo / ".project-starter.yml").write_text(
        "project_type: web-app\ndocs_path: docs/\ntask_type:\n"
        "spec_code_adapter:\nspec_code_spec:\nspec_code_src:\n", encoding="utf-8",
    )
    (repo / "docs").mkdir()
    (repo / "docs" / "current-state.md").write_text(body, encoding="utf-8")
    to_add = ["docs/current-state.md", ".project-starter.yml"]
    if staged_source:
        (repo / "app.py").write_text("print(1)\n", encoding="utf-8")
        to_add.append("app.py")
    subprocess.run(["git", "add", *to_add], cwd=repo, check=True)
    return repo


def _run_hook(repo: Path) -> subprocess.CompletedProcess:
    assert _BASH is not None
    return subprocess.run([_BASH, str(HOOK)], cwd=repo, capture_output=True, text=True,
                          encoding="utf-8", errors="replace")


def test_line_absent_is_not_blocked(tmp_path):
    result = _run_hook(_make_repo(tmp_path, _state(None)))
    assert "Docs to update" not in result.stdout
    assert result.returncode == 0


def test_placeholder_blocks_commit(tmp_path):
    result = _run_hook(_make_repo(tmp_path, _state("[Per task: which spec docs change and why]")))
    assert _MESSAGE in result.stdout
    assert result.returncode == 1


def test_empty_value_blocks_commit(tmp_path):
    result = _run_hook(_make_repo(tmp_path, _state("")))
    assert _MESSAGE in result.stdout
    assert result.returncode == 1


def test_missing_project_requirements_blocks_commit(tmp_path):
    result = _run_hook(_make_repo(tmp_path, _state("api-contract.md")))
    assert _MESSAGE in result.stdout
    assert result.returncode == 1


def test_filled_list_passes(tmp_path):
    result = _run_hook(_make_repo(tmp_path, _state("task 1: project-requirements.md, api-contract.md")))
    assert _MESSAGE not in result.stdout
    assert result.returncode == 0


def test_placeholder_task_skips_the_guard(tmp_path):
    result = _run_hook(_make_repo(tmp_path, _state("[placeholder]", task="[Task name]")))
    assert "Docs to update" not in result.stdout
    assert result.returncode == 0


def test_staged_source_with_unfilled_list_blocks_commit(tmp_path):
    """The unscoped-source guard also checks it, so leaving current-state.md out of the
    commit is not a way around agreeing the docs with the user."""
    result = _run_hook(_make_repo(tmp_path, _state("[placeholder]"), staged_source=True))
    assert "Source files staged but Approach -> Docs to update is unfilled" in result.stdout
    assert result.returncode == 1
