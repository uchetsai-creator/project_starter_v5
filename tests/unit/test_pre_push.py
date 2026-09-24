"""Tests for .githooks/pre-push — the requirement gate that runs on `git push`.

Commits stay cheap (a half-finished requirement can be committed freely); pushing to a gated
branch (main/master by default) requires the requirement to be Complete and verified by
verify_acceptance.py --only <Requirement IDs>, or Descoped by the user. Other branches only get a
warning so work in progress can still be backed up. The hook reads current-state.md at the pushed
commit, not the working tree.

Runs the real bash script via subprocess against a minimal isolated git repo (with a copy of the
real validators), matching test_pre_commit_approach_confirmed.py -- skipped if bash isn't on PATH.
"""
import shutil
import subprocess
from pathlib import Path

import pytest

from tests.conftest import find_posix_bash
from tests.unit.test_verify_acceptance_scoped import _ALL_COVERED, _FR_ONLY, _docs

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
HOOK = REPO_ROOT / ".githooks" / "pre-push"
VALIDATORS = REPO_ROOT / "templates" / "script" / "validators"

_BASH = find_posix_bash()
pytestmark = pytest.mark.skipif(_BASH is None, reason="bash not found on PATH")

ZERO = "0" * 40


def _state(status: str, ids: str | None = "FR-012, AC-012", task: str = "Build the export") -> str:
    body = f"## Current Task\n\n**Task:** {task}\n\n"
    if ids is not None:
        body += f"**Requirement IDs:** {ids}\n\n"
    if status is not None:
        body += f"**Requirement Status:** {status}\n"
    return body


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True).stdout.strip()


def _make_repo(tmp_path: Path, current_state: str, scope_rows: str = _ALL_COVERED, config_extra: str = "") -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    (repo / ".project-starter.yml").write_text(
        "project_type: web-app\ndocs_path: docs/\n" + config_extra, encoding="utf-8",
    )
    _docs(repo, scope_rows)
    shutil.copytree(VALIDATORS, repo / "docs" / "script" / "validators",
                    ignore=shutil.ignore_patterns("__pycache__"))
    (repo / "docs" / "current-state.md").write_text(current_state, encoding="utf-8")
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "--no-verify", "-m", "init")
    return repo


def _push(repo: Path, branch: str = "main", env: dict | None = None, sha: str | None = None,
          remote_sha: str = ZERO) -> subprocess.CompletedProcess:
    assert _BASH is not None
    import os
    local_sha = sha or _git(repo, "rev-parse", "HEAD")
    stdin = f"refs/heads/work {local_sha} refs/heads/{branch} {remote_sha}\n"
    return subprocess.run(
        [_BASH, str(HOOK)], cwd=repo, input=stdin, capture_output=True, text=True,
        encoding="utf-8", errors="replace", env={**os.environ, **(env or {})},
    )


def test_in_progress_blocks_push_to_main(tmp_path):
    result = _push(_make_repo(tmp_path, _state("In Progress")))
    assert result.returncode == 1
    assert "Requirement Status is In Progress" in result.stdout


def test_in_progress_only_warns_on_a_work_branch(tmp_path):
    result = _push(_make_repo(tmp_path, _state("In Progress")), branch="wip/export")
    assert result.returncode == 0
    assert "[WARN]" in result.stdout


def test_complete_and_covered_passes_on_main(tmp_path):
    result = _push(_make_repo(tmp_path, _state("Complete")))
    assert result.returncode == 0, result.stdout
    assert "[FAIL]" not in result.stdout


def test_complete_with_uncovered_ac_blocks_push_to_main(tmp_path):
    result = _push(_make_repo(tmp_path, _state("Complete"), scope_rows=_FR_ONLY))
    assert result.returncode == 1
    assert "verify_acceptance.py --only FR-012, AC-012 failed" in result.stdout
    assert "AC-012" in result.stdout


def test_complete_with_undeclared_id_blocks_push(tmp_path):
    result = _push(_make_repo(tmp_path, _state("Complete", ids="FR-099")))
    assert result.returncode == 1
    assert "FR-099" in result.stdout


def test_complete_without_requirement_ids_blocks_push(tmp_path):
    result = _push(_make_repo(tmp_path, _state("Complete", ids="[FR-/AC- ids]")))
    assert result.returncode == 1
    assert "Requirement IDs is empty" in result.stdout


def test_complete_but_uncovered_only_warns_on_a_work_branch(tmp_path):
    result = _push(_make_repo(tmp_path, _state("Complete"), scope_rows=_FR_ONLY), branch="wip/x")
    assert result.returncode == 0
    assert "[WARN]" in result.stdout


def test_descoped_by_user_with_reason_passes(tmp_path):
    result = _push(_make_repo(tmp_path, _state("Descoped — user: customer dropped the export")))
    assert result.returncode == 0, result.stdout


def test_descoped_not_attributed_to_the_user_is_blocked(tmp_path):
    """Only the user may abandon a requirement, the same rule as Clarifications N/A."""
    result = _push(_make_repo(tmp_path, _state("Descoped — not needed")))
    assert result.returncode == 1


def test_descoped_without_reason_is_blocked(tmp_path):
    result = _push(_make_repo(tmp_path, _state("Descoped — user:")))
    assert result.returncode == 1


def test_placeholder_status_is_blocked(tmp_path):
    result = _push(_make_repo(tmp_path, _state("[In Progress / Complete / Descoped — user: reason]")))
    assert result.returncode == 1


def test_field_absent_is_not_covered(tmp_path):
    """current-state.md files that predate the field keep working."""
    result = _push(_make_repo(tmp_path, _state(None, ids=None)))
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_placeholder_task_skips_the_gate(tmp_path):
    result = _push(_make_repo(tmp_path, _state("In Progress", task="[Task name]")))
    assert result.returncode == 0


def test_branch_deletion_is_ignored(tmp_path):
    repo = _make_repo(tmp_path, _state("In Progress"))
    result = _push(repo, sha=ZERO)
    assert result.returncode == 0


def test_reads_current_state_at_the_pushed_commit_not_the_working_tree(tmp_path):
    """Editing the file to 'Complete' without committing must not get an In Progress commit through."""
    repo = _make_repo(tmp_path, _state("In Progress"))
    (repo / "docs" / "current-state.md").write_text(_state("Complete"), encoding="utf-8")
    result = _push(repo)
    assert result.returncode == 1
    assert "In Progress" in result.stdout


def test_push_gate_branches_config_overrides_the_default(tmp_path):
    repo = _make_repo(tmp_path, _state("In Progress"), config_extra="push_gate_branches: release\n")
    assert _push(repo, branch="release").returncode == 1
    assert _push(repo, branch="main").returncode == 0


def test_skip_env_var_bypasses_the_gate_loudly(tmp_path):
    result = _push(_make_repo(tmp_path, _state("In Progress")), env={"PROJECT_STARTER_SKIP_VERIFY": "1"})
    assert result.returncode == 0
    assert "[SKIP]" in result.stdout


def test_unset_project_type_is_not_gated(tmp_path):
    repo = _make_repo(tmp_path, _state("In Progress"))
    (repo / ".project-starter.yml").write_text("project_type: [your-project-type]\n", encoding="utf-8")
    assert _push(repo).returncode == 0
