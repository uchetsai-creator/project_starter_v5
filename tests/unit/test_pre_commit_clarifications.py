"""Tests for the Clarifications guard in .githooks/pre-commit.

The user, not the agent, decides what is in scope: every category in current-state.md's
"## Clarifications" section must be answered by the user. An `N/A` is accepted only as
`N/A — user: <reason>` (the agent may say a category looks less relevant, but cannot skip it).
The guard only applies when the section exists, so older files are not blocked.

Runs the real bash script via subprocess against a minimal isolated git repo, matching
test_pre_commit_approach_confirmed.py -- skipped if bash isn't on PATH.
"""
import subprocess
from pathlib import Path

import pytest

from tests.conftest import find_posix_bash

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
HOOK = REPO_ROOT / ".githooks" / "pre-commit"

_BASH = find_posix_bash()
pytestmark = pytest.mark.skipif(_BASH is None, reason="bash not found on PATH")

_CATS = [
    "Goal & scope", "Users & permissions", "Data", "Flow & interaction",
    "Edge cases & failure handling",
    "Non-functional (performance, security, reliability, compliance)",
    "Integrations & external dependencies", "Constraints & trade-offs",
    "Terminology & conventions", "Acceptance criteria (done means)",
]
_MESSAGE = "Clarifications has unanswered categories"


def _state(overrides: dict | None = None, section: bool = True, default: str = "user answered") -> str:
    body = (
        "## Current Task\n\n**Task:** Build the order API\n\n"
        "**Clarifying Questions Asked:** Y\n"
    )
    if section:
        lines = [f"- **{c}:** {(overrides or {}).get(c, default)}" for c in _CATS]
        body += "\n## Clarifications\n\n" + "\n".join(lines) + "\n\n## Approach\n"
    return body


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


def test_section_absent_is_not_blocked(tmp_path):
    result = _run_hook(_make_repo(tmp_path, _state(section=False)))
    assert "Clarifications" not in result.stdout
    assert result.returncode == 0


def test_all_answered_passes(tmp_path):
    result = _run_hook(_make_repo(tmp_path, _state()))
    assert _MESSAGE not in result.stdout
    assert result.returncode == 0


def test_placeholder_blocks_commit_and_names_the_category(tmp_path):
    result = _run_hook(_make_repo(tmp_path, _state({"Data": "[ask the user]"})))
    assert _MESSAGE in result.stdout
    assert "Data" in result.stdout
    assert result.returncode == 1


def test_empty_answer_blocks_commit(tmp_path):
    result = _run_hook(_make_repo(tmp_path, _state({"Users & permissions": ""})))
    assert _MESSAGE in result.stdout
    assert result.returncode == 1


def test_agent_written_na_blocks_commit(tmp_path):
    result = _run_hook(_make_repo(tmp_path, _state({"Data": "N/A — not relevant"})))
    assert _MESSAGE in result.stdout
    assert result.returncode == 1


def test_user_na_with_reason_passes(tmp_path):
    result = _run_hook(_make_repo(tmp_path, _state({"Data": "N/A — user: no data is touched"})))
    assert _MESSAGE not in result.stdout
    assert result.returncode == 0


def test_placeholder_task_skips_the_guard(tmp_path):
    body = "## Current Task\n\n**Task:** [Task name]\n\n## Clarifications\n\n- **Data:** [ask the user]\n"
    result = _run_hook(_make_repo(tmp_path, body))
    assert "Clarifications" not in result.stdout
    assert result.returncode == 0


def test_staged_source_with_unanswered_category_blocks_commit(tmp_path):
    """The unscoped-source guard also checks it, so leaving current-state.md out of the
    commit is not a way around asking the user."""
    result = _run_hook(_make_repo(tmp_path, _state({"Data": "[ask the user]"}), staged_source=True))
    assert "Source files staged but Clarifications has unanswered categories" in result.stdout
    assert result.returncode == 1
