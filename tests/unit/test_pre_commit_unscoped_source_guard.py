"""Tests for the Unscoped source-change guard in .githooks/pre-commit.

The pre-existing "Clarifying Questions Asked guard" only runs when docs/current-state.md
is itself part of the staged set for a commit -- an agent that implements a new, unscoped
requirement and simply never stages current-state.md sails through untouched. This guard
closes that gap: it fires whenever staged files look like application source (not docs/,
guidance/, or known framework root files) and the current-state.md that would actually be
in the repo after the commit (staged version if staged, else the committed HEAD version)
has no real Task or no filled Clarifying Questions Asked field.

Runs the real bash script via subprocess against a minimal isolated git repo, matching
test_pre_commit_clarifying_questions.py's approach -- skipped if bash isn't on PATH.
"""
import subprocess
from pathlib import Path

import pytest

from tests.conftest import find_posix_bash

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
HOOK = REPO_ROOT / ".githooks" / "pre-commit"

_BASH = find_posix_bash()
pytestmark = pytest.mark.skipif(_BASH is None, reason="bash not found on PATH")


def _init_repo(tmp_path: Path) -> Path:
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
    subprocess.run(["git", "add", ".project-starter.yml"], cwd=repo, check=True)
    return repo


def _write_current_state(repo: Path, body: str) -> None:
    docs = repo / "docs"
    docs.mkdir(exist_ok=True)
    (docs / "current-state.md").write_text(body, encoding="utf-8")


def _run_hook(repo: Path) -> subprocess.CompletedProcess:
    assert _BASH is not None  # module-level skipif guarantees this by the time we get here
    return subprocess.run(
        [_BASH, str(HOOK)], cwd=repo, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )


_REAL_TASK_Y = (
    "## Current Task\n\n**Task:** Build the order API\n\n"
    "**Clarifying Questions Asked:** Y\n"
)


def test_source_file_staged_with_no_current_state_file_at_all_is_blocked(tmp_path):
    """The core bypass: an agent that implements code and never creates/stages
    current-state.md must not be able to commit silently."""
    repo = _init_repo(tmp_path)
    (repo / "src").mkdir()
    (repo / "src" / "login.js").write_text("function login() {}\n", encoding="utf-8")
    subprocess.run(["git", "add", "src/login.js"], cwd=repo, check=True)

    result = _run_hook(repo)
    assert result.returncode == 1
    assert "no scoped Current Task" in result.stdout


def test_source_file_staged_with_placeholder_task_is_blocked(tmp_path):
    repo = _init_repo(tmp_path)
    _write_current_state(repo, "## Current Task\n\n**Task:** [Task name, e.g., BE Order API]\n")
    subprocess.run(["git", "add", "docs/current-state.md"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "scaffold"], cwd=repo, check=True,
                    env={"PROJECT_STARTER_SKIP_VERIFY": "1", **_env()})

    (repo / "src.py").write_text("x = 1\n", encoding="utf-8")
    subprocess.run(["git", "add", "src.py"], cwd=repo, check=True)
    result = _run_hook(repo)
    assert result.returncode == 1
    assert "no scoped Current Task" in result.stdout


def test_source_file_staged_with_scoped_task_but_no_cqa_is_blocked(tmp_path):
    repo = _init_repo(tmp_path)
    _write_current_state(repo, "## Current Task\n\n**Task:** Build the order API\n")
    subprocess.run(["git", "add", "docs/current-state.md"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "scaffold"], cwd=repo, check=True,
                    env={"PROJECT_STARTER_SKIP_VERIFY": "1", **_env()})

    (repo / "src.py").write_text("x = 1\n", encoding="utf-8")
    subprocess.run(["git", "add", "src.py"], cwd=repo, check=True)
    result = _run_hook(repo)
    assert result.returncode == 1
    assert "Clarifying Questions Asked is unfilled or not Y/N/A" in result.stdout


def test_source_file_staged_with_fully_scoped_committed_task_passes(tmp_path):
    """Once a task has been scoped and committed, later commits that only touch source
    (without re-staging current-state.md) must not be re-blocked."""
    repo = _init_repo(tmp_path)
    _write_current_state(repo, _REAL_TASK_Y)
    subprocess.run(["git", "add", "docs/current-state.md"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "scaffold"], cwd=repo, check=True,
                    env={"PROJECT_STARTER_SKIP_VERIFY": "1", **_env()})

    (repo / "src.py").write_text("x = 1\n", encoding="utf-8")
    subprocess.run(["git", "add", "src.py"], cwd=repo, check=True)
    result = _run_hook(repo)
    assert "no scoped Current Task" not in result.stdout
    assert "Clarifying Questions Asked is unfilled" not in result.stdout


def test_source_file_staged_with_invalid_cqa_value_is_blocked(tmp_path):
    """An honest "N" (never a documented valid value) must not satisfy the gate any
    more than an unfilled field would."""
    repo = _init_repo(tmp_path)
    _write_current_state(
        repo,
        "## Current Task\n\n**Task:** Build the order API\n\n"
        "**Clarifying Questions Asked:** N\n",
    )
    subprocess.run(["git", "add", "docs/current-state.md"], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-m", "scaffold"], cwd=repo, check=True,
                    env={"PROJECT_STARTER_SKIP_VERIFY": "1", **_env()})

    (repo / "src.py").write_text("x = 1\n", encoding="utf-8")
    subprocess.run(["git", "add", "src.py"], cwd=repo, check=True)
    result = _run_hook(repo)
    assert result.returncode == 1
    assert "Clarifying Questions Asked is unfilled or not Y/N/A" in result.stdout


def test_docs_only_change_does_not_trigger_the_guard(tmp_path):
    """A commit that only touches docs/, guidance/, or framework root files is not
    'source' -- the guard must stay silent even with no current-state.md at all."""
    repo = _init_repo(tmp_path)
    (repo / "guidance").mkdir()
    (repo / "guidance" / "note.md").write_text("note\n", encoding="utf-8")
    subprocess.run(["git", "add", "guidance/note.md"], cwd=repo, check=True)

    result = _run_hook(repo)
    assert "no scoped Current Task" not in result.stdout


def _env():
    import os
    return dict(os.environ)
