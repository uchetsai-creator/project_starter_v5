"""Tests for the test_command gate in .githooks/pre-commit.

Before this, the only pre-commit check touching "tests" was verify_tests.py, which
checks that docs/specs/test-report.md has non-placeholder numbers — it never runs
anything, so a fabricated "42 passed" line would satisfy it. test_command (set in
.project-starter.yml) closes that gap: pre-commit actually executes the configured
command and blocks the commit on a real failure.

.githooks/pre-commit itself has no existing test coverage (confirmed by grep before
writing this file) — these run the real bash script via subprocess against a minimal
isolated git repo, skipped if bash isn't on PATH.
"""
import subprocess
from pathlib import Path

import pytest

from tests.conftest import find_posix_bash

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
HOOK = REPO_ROOT / ".githooks" / "pre-commit"

_BASH = find_posix_bash()
pytestmark = pytest.mark.skipif(_BASH is None, reason="bash not found on PATH")


def _make_repo(tmp_path: Path, test_command: str | None) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)

    lines = [
        "project_type: web-app",
        "docs_path: docs/",
        "task_type:",
        "spec_code_adapter:",
        "spec_code_spec:",
        "spec_code_src:",
    ]
    lines.append(f"test_command: {test_command}" if test_command is not None else "test_command:")
    (repo / ".project-starter.yml").write_text("\n".join(lines) + "\n", encoding="utf-8")
    return repo


def _run_hook(repo: Path) -> subprocess.CompletedProcess:
    assert _BASH is not None  # module-level skipif guarantees this by the time we get here
    # encoding must be explicit: the hook's own output uses UTF-8 punctuation (—, etc.)
    # that the default locale codec on a non-UTF-8 Windows machine cannot decode.
    return subprocess.run(
        [_BASH, str(HOOK)], cwd=repo, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )


def test_no_test_command_configured_skips_the_gate(tmp_path):
    repo = _make_repo(tmp_path, test_command=None)
    result = _run_hook(repo)
    assert result.returncode == 0
    assert "running test suite" not in result.stdout


def test_passing_test_command_does_not_block_commit(tmp_path):
    repo = _make_repo(tmp_path, test_command='python3 -c "exit(0)"')
    result = _run_hook(repo)
    assert result.returncode == 0
    assert "[OK] test suite passed" in result.stdout


def test_failing_test_command_blocks_commit(tmp_path):
    repo = _make_repo(tmp_path, test_command='python3 -c "exit(1)"')
    result = _run_hook(repo)
    assert result.returncode == 1
    assert "[FAIL] test suite failed" in result.stdout
    assert "commit blocked" in result.stdout


def test_nonexistent_command_blocks_commit_not_silently_passes(tmp_path):
    repo = _make_repo(tmp_path, test_command="totally-nonexistent-command-xyz")
    result = _run_hook(repo)
    assert result.returncode == 1
    assert "[FAIL] test suite failed" in result.stdout


def test_command_with_embedded_quotes_is_not_corrupted_by_config_parsing(tmp_path):
    """Regression: an earlier version stripped a trailing quote character off the
    raw config value assuming it was YAML wrapping quotes, which broke any command
    ending in a quote (e.g. `python3 -c "...")`) by leaving an unbalanced quote."""
    repo = _make_repo(tmp_path, test_command='python3 -c "print(1); exit(0)"')
    result = _run_hook(repo)
    assert result.returncode == 0, result.stdout
    assert "[OK] test suite passed" in result.stdout


def test_multi_word_command_with_flags_is_preserved(tmp_path):
    repo = _make_repo(tmp_path, test_command="python3 -c pass")
    result = _run_hook(repo)
    assert result.returncode == 0, result.stdout
