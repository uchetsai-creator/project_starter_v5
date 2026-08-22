"""Tests for the project_type_confirmed guard in .githooks/pre-commit.

detect_type.py --apply writes project_type_confirmed: false alongside a machine-guessed
project_type — a confidence score passing the --apply threshold is not the same as a
human (or the agent, on the human's behalf) having actually checked the guess is right,
especially for a mixed-signal project where a wrong guess can still score high enough to
pass. This guard blocks a commit while that field is still false, closing the gap a
confidence threshold alone can't: a *high*-confidence-but-wrong guess. See
docs/architecture-analysis.md for the full rationale.

Runs the real bash script via subprocess against a minimal isolated git repo, matching
test_pre_commit_clarifying_questions.py's approach — skipped if bash isn't on PATH.
"""
import subprocess
from pathlib import Path

import pytest

from tests.conftest import find_posix_bash

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
HOOK = REPO_ROOT / ".githooks" / "pre-commit"

_BASH = find_posix_bash()
pytestmark = pytest.mark.skipif(_BASH is None, reason="bash not found on PATH")


def _make_repo(tmp_path: Path, project_starter_yml_body: str) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)

    (repo / ".project-starter.yml").write_text(project_starter_yml_body, encoding="utf-8")
    (repo / "docs").mkdir()
    (repo / "docs" / "current-state.md").write_text("# Current State\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)

    return repo


def _run_hook(repo: Path) -> subprocess.CompletedProcess:
    assert _BASH is not None  # module-level skipif guarantees this by the time we get here
    return subprocess.run(
        [_BASH, str(HOOK)], cwd=repo, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )


def test_unconfirmed_project_type_blocks_commit(tmp_path):
    repo = _make_repo(
        tmp_path,
        "project_type: web-app\nproject_type_confirmed: false\ndocs_path: docs/\n",
    )
    result = _run_hook(repo)
    assert "project_type_confirmed: false" in result.stdout
    assert "hasn't been confirmed yet" in result.stdout
    assert result.returncode == 1


def test_confirmed_project_type_does_not_block(tmp_path):
    repo = _make_repo(
        tmp_path,
        "project_type: web-app\nproject_type_confirmed: true\ndocs_path: docs/\n",
    )
    result = _run_hook(repo)
    assert "project_type_confirmed" not in result.stdout
    assert result.returncode == 0


def test_field_absent_does_not_block(tmp_path):
    """A human hand-writing project_type never goes through detect_type.py --apply, so
    the field never gets added — this must not retroactively block every project that
    predates the feature or was configured by hand."""
    repo = _make_repo(tmp_path, "project_type: web-app\ndocs_path: docs/\n")
    result = _run_hook(repo)
    assert "project_type_confirmed" not in result.stdout
    assert result.returncode == 0


def test_no_project_starter_yml_does_not_crash():
    """.project-starter.yml missing entirely is handled by an earlier, unrelated guard
    (prints a [WARN] and exits 0) — this guard must not itself crash when $CONFIG doesn't
    exist (set -u would turn an unguarded reference into a hard failure)."""
    # Covered implicitly by every other pre-commit test that omits .project-starter.yml;
    # asserted directly here for this guard's own regression coverage.
    import tempfile
    with tempfile.TemporaryDirectory() as tmpdir:
        repo = Path(tmpdir) / "repo"
        repo.mkdir()
        subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
        result = _run_hook(repo)
        assert "project_type_confirmed" not in (result.stdout + result.stderr)
