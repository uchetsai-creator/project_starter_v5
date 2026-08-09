"""Tests for the Clarifying Questions Asked guard in .githooks/pre-commit.

AGENTS.md -> "New requirement from the user" says the agent must ask scope/edge-case/
acceptance-criteria questions before implementing a new, unscoped requirement (Learning
Checkpoint B). That rule was previously enforced only by the agent choosing to comply in
conversation — nothing recorded whether it actually happened, and no file distinguished a
compliant session from one that skipped straight to code. current-state.md's Current Task
section now has a Clarifying Questions Asked field (Y / N/A); this guard blocks a commit
that sets a real (non-placeholder) Task while leaving that field unfilled, the same pattern
already used for Closeout completeness in this same script.

Runs the real bash script via subprocess against a minimal isolated git repo, matching
test_pre_commit_test_command.py's approach — skipped if bash isn't on PATH.
"""
import subprocess
from pathlib import Path

import pytest

from tests.conftest import find_posix_bash

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
HOOK = REPO_ROOT / ".githooks" / "pre-commit"

_BASH = find_posix_bash()
pytestmark = pytest.mark.skipif(_BASH is None, reason="bash not found on PATH")


def _make_repo(tmp_path: Path, current_state_body: str | None) -> Path:
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

    if current_state_body is not None:
        docs = repo / "docs"
        docs.mkdir()
        (docs / "current-state.md").write_text(current_state_body, encoding="utf-8")
        subprocess.run(["git", "add", "docs/current-state.md", ".project-starter.yml"],
                        cwd=repo, check=True)
    else:
        subprocess.run(["git", "add", ".project-starter.yml"], cwd=repo, check=True)

    return repo


def _run_hook(repo: Path) -> subprocess.CompletedProcess:
    assert _BASH is not None  # module-level skipif guarantees this by the time we get here
    return subprocess.run(
        [_BASH, str(HOOK)], cwd=repo, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )


_PLACEHOLDER_TASK = "## Current Task\n\n**Task:** [Task name, e.g., BE Order API]\n"

_REAL_TASK_NO_CQA = "## Current Task\n\n**Task:** Build the order API\n"

_REAL_TASK_PLACEHOLDER_CQA = (
    "## Current Task\n\n"
    "**Task:** Build the order API\n\n"
    "**Clarifying Questions Asked:** [Y / N/A — reason]\n"
)

_REAL_TASK_Y = (
    "## Current Task\n\n"
    "**Task:** Build the order API\n\n"
    "**Clarifying Questions Asked:** Y\n"
)

_REAL_TASK_NA = (
    "## Current Task\n\n"
    "**Task:** Build the order API\n\n"
    "**Clarifying Questions Asked:** N/A — pre-scoped in project-plan.md\n"
)


def test_no_current_state_staged_skips_the_guard(tmp_path):
    repo = _make_repo(tmp_path, current_state_body=None)
    result = _run_hook(repo)
    assert "Clarifying Questions Asked" not in result.stdout


def test_placeholder_task_skips_the_guard(tmp_path):
    repo = _make_repo(tmp_path, _PLACEHOLDER_TASK)
    result = _run_hook(repo)
    assert "Clarifying Questions Asked" not in result.stdout
    assert result.returncode == 0


def test_real_task_missing_cqa_field_blocks_commit(tmp_path):
    repo = _make_repo(tmp_path, _REAL_TASK_NO_CQA)
    result = _run_hook(repo)
    assert "Clarifying Questions Asked is missing, still a placeholder, or not Y/N/A" in result.stdout
    assert result.returncode == 1


def test_real_task_placeholder_cqa_blocks_commit(tmp_path):
    repo = _make_repo(tmp_path, _REAL_TASK_PLACEHOLDER_CQA)
    result = _run_hook(repo)
    assert "Clarifying Questions Asked is missing, still a placeholder, or not Y/N/A" in result.stdout
    assert result.returncode == 1


def test_real_task_with_invalid_value_blocks_commit(tmp_path):
    """A presence-only check would accept any text, including an honest "N" (never a
    documented valid value) — the field must actually be Y or N/A, not just non-empty."""
    repo = _make_repo(
        tmp_path,
        "## Current Task\n\n**Task:** Build the order API\n\n"
        "**Clarifying Questions Asked:** N\n",
    )
    result = _run_hook(repo)
    assert "Clarifying Questions Asked is missing, still a placeholder, or not Y/N/A" in result.stdout
    assert result.returncode == 1


def test_real_task_with_y_passes(tmp_path):
    repo = _make_repo(tmp_path, _REAL_TASK_Y)
    result = _run_hook(repo)
    assert "Clarifying Questions Asked" not in result.stdout
    assert result.returncode == 0


def test_real_task_with_na_passes(tmp_path):
    repo = _make_repo(tmp_path, _REAL_TASK_NA)
    result = _run_hook(repo)
    assert "Clarifying Questions Asked" not in result.stdout
    assert result.returncode == 0
