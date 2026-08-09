"""Tests for the PROJECT_STARTER_SKIP_VERIFY escape hatch in .githooks/pre-commit.

Before this, the only documented way to bypass a blocking check during a prototype/spike
was `git commit --no-verify` — which skips the hook silently, leaving no trace that
verification was bypassed. PROJECT_STARTER_SKIP_VERIFY=1 is the officially-documented
alternative: it always prints a loud [SKIP] line, so a skipped commit can never be
mistaken for a verified one later. It also appends a row to
logs/telemetry/skip-verify.json — doesn't make the hatch any harder to use, but means
how often a project reaches for it is auditable after the fact instead of only visible
in the terminal at the moment it happened.

Follows the same real-bash-subprocess pattern as test_pre_commit_test_command.py.
"""
import json
import os
import subprocess
from pathlib import Path

import pytest

from tests.conftest import find_posix_bash

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
HOOK = REPO_ROOT / ".githooks" / "pre-commit"

_BASH = find_posix_bash()
pytestmark = pytest.mark.skipif(_BASH is None, reason="bash not found on PATH")


def _make_repo_with_blocking_config(tmp_path: Path) -> Path:
    """A minimal repo whose .project-starter.yml is guaranteed to fail pre-commit
    (unrecognized spec_code_adapter name) — proves the skip hatch bypasses a real
    blocking condition, not just a check that happened to be unconfigured."""
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    (repo / ".project-starter.yml").write_text(
        "project_type: web-app\n"
        "docs_path: docs/\n"
        "task_type:\n"
        "spec_code_adapter: not-a-real-adapter\n"
        "spec_code_spec:\n"
        "spec_code_src:\n",
        encoding="utf-8",
    )
    return repo


def _run_hook(repo: Path, extra_env: dict | None = None) -> subprocess.CompletedProcess:
    assert _BASH is not None  # module-level skipif guarantees this by the time we get here
    env = {**os.environ, **(extra_env or {})}
    return subprocess.run(
        [_BASH, str(HOOK)], cwd=repo, capture_output=True, text=True,
        encoding="utf-8", errors="replace", env=env,
    )


def test_blocking_condition_fails_without_the_env_var(tmp_path):
    repo = _make_repo_with_blocking_config(tmp_path)
    result = _run_hook(repo)
    assert result.returncode == 1
    assert "not a recognised adapter" in result.stdout


def test_skip_verify_env_var_bypasses_the_same_blocking_condition(tmp_path):
    repo = _make_repo_with_blocking_config(tmp_path)
    result = _run_hook(repo, {"PROJECT_STARTER_SKIP_VERIFY": "1"})
    assert result.returncode == 0
    assert "[SKIP]" in result.stdout
    assert "not a recognised adapter" not in result.stdout


def test_empty_skip_verify_env_var_does_not_trigger_skip(tmp_path):
    """An empty (but set) env var must not accidentally skip — only a non-empty value does."""
    repo = _make_repo_with_blocking_config(tmp_path)
    result = _run_hook(repo, {"PROJECT_STARTER_SKIP_VERIFY": ""})
    assert result.returncode == 1
    assert "[SKIP]" not in result.stdout


def test_skip_verify_appends_telemetry_row(tmp_path):
    repo = _make_repo_with_blocking_config(tmp_path)
    result = _run_hook(repo, {"PROJECT_STARTER_SKIP_VERIFY": "1"})
    assert result.returncode == 0

    log_path = repo / "logs" / "telemetry" / "skip-verify.json"
    assert log_path.exists()
    rows = json.loads(log_path.read_text(encoding="utf-8"))
    assert len(rows) == 1
    assert "ts" in rows[0]
    assert "staged_files" in rows[0]


def test_skip_verify_telemetry_appends_not_overwrites(tmp_path):
    repo = _make_repo_with_blocking_config(tmp_path)
    _run_hook(repo, {"PROJECT_STARTER_SKIP_VERIFY": "1"})
    _run_hook(repo, {"PROJECT_STARTER_SKIP_VERIFY": "1"})

    log_path = repo / "logs" / "telemetry" / "skip-verify.json"
    rows = json.loads(log_path.read_text(encoding="utf-8"))
    assert len(rows) == 2


def test_no_skip_used_means_no_telemetry_file(tmp_path):
    repo = _make_repo_with_blocking_config(tmp_path)
    _run_hook(repo)  # blocked, no skip
    log_path = repo / "logs" / "telemetry" / "skip-verify.json"
    assert not log_path.exists()
