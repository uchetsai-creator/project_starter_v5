"""Tests for PROJECT_STARTER_DIFF_RANGE in .githooks/pre-commit.

A CI checkout has no "staged" concept -- the working tree already reflects the full
state under test -- so `.githooks/pre-commit`'s default `git diff --cached` (the
local `git commit` case) can never see anything there. Setting
PROJECT_STARTER_DIFF_RANGE (e.g. "origin/main...HEAD") switches the diff source to a
git ref range instead, and file-content reads switch from the staged (index) version
to the current working-tree version -- letting the same script, same checks, run in
CI without a second, separately-maintained implementation.

Runs the real bash script via subprocess against a minimal isolated git repo with two
commits (base, then a commit that introduces a real violation) -- skipped if bash
isn't on PATH.
"""
import os
import subprocess
from pathlib import Path

import pytest

from tests.conftest import find_posix_bash

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
HOOK = REPO_ROOT / ".githooks" / "pre-commit"

_BASH = find_posix_bash()
pytestmark = pytest.mark.skipif(_BASH is None, reason="bash not found on PATH")

_VALID_CS = (
    "**Task:** Build the order API\n\n"
    "**Clarifying Questions Asked:** Y\n\n"
    "**Status:** In Progress\n"
)
_BROKEN_CS = (
    "**Task:** Build the order API\n\n"
    "**Clarifying Questions Asked:** [Y / N/A — reason]\n\n"
    "**Status:** In Progress\n"
)


def _make_repo_with_two_commits(tmp_path: Path) -> tuple[Path, str, str]:
    """base commit: valid current-state.md. head commit: breaks Clarifying Questions
    Asked. Both fully committed -- nothing left staged -- so local (staged-diff) mode
    has nothing to see, while CI (ref-range) mode should still catch the break."""
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)

    (repo / ".project-starter.yml").write_text(
        "project_type: web-app\ndocs_path: docs/\n", encoding="utf-8",
    )
    docs = repo / "docs"
    docs.mkdir()
    (docs / "current-state.md").write_text(_VALID_CS, encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "base"], cwd=repo, check=True)
    base_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True, check=True,
    ).stdout.strip()

    (docs / "current-state.md").write_text(_BROKEN_CS, encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "head: break CQA"], cwd=repo, check=True)
    head_sha = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=repo, capture_output=True, text=True, check=True,
    ).stdout.strip()

    return repo, base_sha, head_sha


def _run_hook(repo: Path, extra_env: dict[str, str] | None = None) -> subprocess.CompletedProcess:
    assert _BASH is not None  # module-level skipif guarantees this by the time we get here
    env = {**os.environ, **(extra_env or {})}
    return subprocess.run(
        [_BASH, str(HOOK)], cwd=repo, capture_output=True, text=True,
        encoding="utf-8", errors="replace", env=env,
    )


def test_local_mode_sees_nothing_once_everything_is_committed(tmp_path):
    """Default (no env var) behaviour is unchanged: with nothing staged, the CQA
    break -- already committed in the head commit -- is invisible to local mode."""
    repo, _base_sha, _head_sha = _make_repo_with_two_commits(tmp_path)
    result = _run_hook(repo)
    assert "Clarifying Questions Asked" not in result.stdout
    assert result.returncode == 0


def test_ci_mode_catches_the_same_break_via_diff_range(tmp_path):
    repo, base_sha, head_sha = _make_repo_with_two_commits(tmp_path)
    result = _run_hook(repo, {"PROJECT_STARTER_DIFF_RANGE": f"{base_sha}...{head_sha}"})
    assert "Clarifying Questions Asked is missing, still a placeholder, or not Y/N/A" in result.stdout
    assert result.returncode == 1


def test_ci_mode_reads_working_tree_not_index(tmp_path):
    """_content_at() in CI mode must read the working-tree file (cat), not attempt an
    index lookup that would find nothing to compare against in a fresh checkout."""
    repo, base_sha, head_sha = _make_repo_with_two_commits(tmp_path)
    # Fix the break in the working tree without committing or staging it -- CI mode
    # should see this (it's reading the working tree directly), local mode never would.
    (repo / "docs" / "current-state.md").write_text(_VALID_CS, encoding="utf-8")
    result = _run_hook(repo, {"PROJECT_STARTER_DIFF_RANGE": f"{base_sha}...{head_sha}"})
    assert "Clarifying Questions Asked" not in result.stdout
    assert result.returncode == 0


def test_ci_mode_with_no_range_set_falls_back_to_staged(tmp_path):
    """Empty/unset PROJECT_STARTER_DIFF_RANGE must behave identically to it never
    having been referenced at all -- no crash from set -u, no accidental CI-mode."""
    repo, _base_sha, _head_sha = _make_repo_with_two_commits(tmp_path)
    result = _run_hook(repo, {"PROJECT_STARTER_DIFF_RANGE": ""})
    assert "Clarifying Questions Asked" not in result.stdout
    assert result.returncode == 0
