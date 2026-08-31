"""Tests for adapters/claude/session-start-hook.sh — the SessionStart nudge.

This is the mechanical follow-through on AGENTS.md -> Constitution -> "Unscoped New
Requirement": the rule only helps if the agent actually has it in front of mind each
session, not just somewhere in a file it may or may not have read closely. The hook
re-surfaces the current-state.md scoping state as SessionStart hookSpecificOutput.
additionalContext every session, instead of relying on CLAUDE.md's `@AGENTS.md` load
having put that specific section in attention.

Never blocks (always exits 0) — it's a reminder, not a gate; the actual gate is the
Clarifying Questions Asked check in .githooks/pre-commit (see
test_pre_commit_clarifying_questions.py).

Runs the real script via subprocess, matching the pre-commit test suite's approach.
"""
import json
import subprocess
import sys
import time
from pathlib import Path

import pytest

from tests.conftest import find_posix_bash

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
HOOK = REPO_ROOT / "adapters" / "claude" / "session-start-hook.sh"

sys.path.insert(0, str(REPO_ROOT / "adapters" / "claude"))
import checkpoint_session_state as cps  # noqa: E402

_BASH = find_posix_bash()
pytestmark = pytest.mark.skipif(_BASH is None, reason="bash not found on PATH")


def _run(cwd: Path, stdin: str = "{}") -> subprocess.CompletedProcess:
    assert _BASH is not None  # module-level skipif guarantees this by the time we get here
    return subprocess.run(
        [_BASH, str(HOOK)], cwd=cwd, capture_output=True, text=True,
        encoding="utf-8", errors="replace", input=stdin,
    )


def test_missing_current_state_produces_no_output(tmp_path):
    result = _run(tmp_path)
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_placeholder_task_produces_reminder(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "current-state.md").write_text(
        "**Task:** [Task name, e.g., BE Order API]\n", encoding="utf-8",
    )
    result = _run(tmp_path)
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    ctx = payload["hookSpecificOutput"]["additionalContext"]
    assert payload["hookSpecificOutput"]["hookEventName"] == "SessionStart"
    assert "no scoped Current Task" in ctx


def test_real_task_missing_cqa_produces_reminder(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "current-state.md").write_text(
        "**Task:** Build the order API\n", encoding="utf-8",
    )
    result = _run(tmp_path)
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    ctx = payload["hookSpecificOutput"]["additionalContext"]
    assert "Clarifying Questions Asked is unfilled" in ctx


def test_real_task_with_cqa_filled_is_silent(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "current-state.md").write_text(
        "**Task:** Build the order API\n\n**Clarifying Questions Asked:** Y\n",
        encoding="utf-8",
    )
    result = _run(tmp_path)
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_real_task_with_na_cqa_is_silent(tmp_path):
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "current-state.md").write_text(
        "**Task:** Build the order API\n\n"
        "**Clarifying Questions Asked:** N/A -- pre-scoped in project-plan.md\n",
        encoding="utf-8",
    )
    result = _run(tmp_path)
    assert result.returncode == 0
    assert result.stdout.strip() == ""


# ---------------------------------------------------------------------------
# Brand-new-project nudge: placeholder Task + research.md with no real Decision —
# both signals together, not either alone, mark a project as brand-new and undiscussed.
# ---------------------------------------------------------------------------

def _write_placeholder_task(tmp_path: Path) -> Path:
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "current-state.md").write_text(
        "**Task:** [Task name, e.g., BE Order API]\n", encoding="utf-8",
    )
    return docs


def test_placeholder_task_no_research_file_omits_research_nudge(tmp_path):
    _write_placeholder_task(tmp_path)
    result = _run(tmp_path)
    payload = json.loads(result.stdout)
    ctx = payload["hookSpecificOutput"]["additionalContext"]
    assert "research-decision-log" not in ctx


def test_placeholder_task_placeholder_research_adds_research_nudge(tmp_path):
    docs = _write_placeholder_task(tmp_path)
    specs = docs / "specs"
    specs.mkdir()
    (specs / "research.md").write_text(
        "## [Decision Name, e.g., Message Queue]\n"
        "**Decision:** [Final choice, e.g., AWS SQS]\n",
        encoding="utf-8",
    )
    result = _run(tmp_path)
    payload = json.loads(result.stdout)
    ctx = payload["hookSpecificOutput"]["additionalContext"]
    assert "brand-new project" in ctx
    assert "research-decision-log" in ctx


def test_placeholder_task_real_research_omits_research_nudge(tmp_path):
    docs = _write_placeholder_task(tmp_path)
    specs = docs / "specs"
    specs.mkdir()
    (specs / "research.md").write_text(
        "## Message Queue\n**Decision:** AWS SQS\n", encoding="utf-8",
    )
    result = _run(tmp_path)
    payload = json.loads(result.stdout)
    ctx = payload["hookSpecificOutput"]["additionalContext"]
    assert "brand-new project" not in ctx
    assert "research-decision-log" not in ctx


def test_real_task_never_gets_research_nudge_regardless_of_research_state(tmp_path):
    """A task-in-progress project with an empty research.md doesn't need this nudge every
    session -- only the very first, unscoped-task session does."""
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "current-state.md").write_text(
        "**Task:** Build the order API\n\n**Clarifying Questions Asked:** Y\n",
        encoding="utf-8",
    )
    specs = docs / "specs"
    specs.mkdir()
    (specs / "research.md").write_text(
        "## [Decision Name, e.g., Message Queue]\n"
        "**Decision:** [Final choice, e.g., AWS SQS]\n",
        encoding="utf-8",
    )
    result = _run(tmp_path)
    assert result.returncode == 0
    assert result.stdout.strip() == ""


# ---------------------------------------------------------------------------
# Spec drift since last touch: a Required Context file committed more recently than
# current-state.md itself may mean the Steps here were planned against an older spec.
# Pure git-log timestamp comparison (same mechanism as learning_log_nudge.py) -- these
# fixtures need a real git repo with real commits, unlike the plain-directory fixtures
# above (git log fails gracefully outside a repo, so this code path never runs there).
# ---------------------------------------------------------------------------

def _git(*args: str, cwd: Path) -> None:
    subprocess.run(["git", *args], cwd=cwd, check=True, capture_output=True)


def _make_git_repo_with_required_context(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    docs = repo / "docs" / "specs"
    docs.mkdir(parents=True)
    _git("init", "-q", "-b", "main", cwd=repo)
    _git("config", "user.email", "test@example.com", cwd=repo)
    _git("config", "user.name", "Test", cwd=repo)

    (docs / "api-contract.md").write_text("## GET /orders/{id}\n", encoding="utf-8")
    (repo / "docs" / "current-state.md").write_text(
        "**Task:** Build the order API\n\n"
        "**Clarifying Questions Asked:** Y\n\n"
        "## Required Context\n\n"
        "* `docs/specs/api-contract.md`\n",
        encoding="utf-8",
    )
    _git("add", ".", cwd=repo)
    _git("commit", "-q", "-m", "base", cwd=repo)
    return repo


def test_spec_changed_after_current_state_triggers_drift_nudge(tmp_path):
    repo = _make_git_repo_with_required_context(tmp_path)
    time.sleep(1.1)  # git commit timestamps have 1-second resolution
    (repo / "docs" / "specs" / "api-contract.md").write_text(
        "## GET /orders/{id}\n## POST /orders\n", encoding="utf-8",
    )
    _git("add", ".", cwd=repo)
    _git("commit", "-q", "-m", "spec changed after current-state.md", cwd=repo)

    result = _run(repo)
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    ctx = payload["hookSpecificOutput"]["additionalContext"]
    assert "changed more recently than current-state.md itself" in ctx
    assert "api-contract.md" in ctx


def test_current_state_touched_after_spec_is_silent(tmp_path):
    """current-state.md itself is the most recent commit -- no drift to report."""
    repo = _make_git_repo_with_required_context(tmp_path)
    time.sleep(1.1)
    (repo / "docs" / "current-state.md").write_text(
        "**Task:** Build the order API\n\n"
        "**Clarifying Questions Asked:** Y\n\n"
        "## Required Context\n\n"
        "* `docs/specs/api-contract.md`\n\n"
        "- [x] Step 1 done\n",
        encoding="utf-8",
    )
    _git("add", ".", cwd=repo)
    _git("commit", "-q", "-m", "current-state.md touched after spec", cwd=repo)

    result = _run(repo)
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_placeholder_required_context_is_ignored(tmp_path):
    """The template's own placeholder line ("docs/[relevant file]") must never be
    treated as a real path to check."""
    repo = tmp_path / "repo"
    docs = repo / "docs"
    docs.mkdir(parents=True)
    _git("init", "-q", "-b", "main", cwd=repo)
    _git("config", "user.email", "test@example.com", cwd=repo)
    _git("config", "user.name", "Test", cwd=repo)
    (docs / "current-state.md").write_text(
        "**Task:** Build the order API\n\n"
        "**Clarifying Questions Asked:** Y\n\n"
        "## Required Context\n\n"
        "* `docs/[relevant file]`\n"
        "* `[other required file paths]`\n",
        encoding="utf-8",
    )
    _git("add", ".", cwd=repo)
    _git("commit", "-q", "-m", "base", cwd=repo)

    result = _run(repo)
    assert result.returncode == 0
    assert result.stdout.strip() == ""


# ---------------------------------------------------------------------------
# Learning Checkpoint enforcement opt-in prompt: only fires when
# .project-starter.yml sets checkpoint_enforcement: session-prompt AND the
# current session_id (from stdin) hasn't already recorded a choice.
# ---------------------------------------------------------------------------

def _write_session_prompt_config(tmp_path: Path) -> None:
    (tmp_path / ".project-starter.yml").write_text(
        "project_type: web-app\ndocs_path: docs/\ncheckpoint_enforcement: session-prompt\n",
        encoding="utf-8",
    )


def test_session_prompt_config_unset_never_prompts_even_with_session_id(tmp_path):
    result = _run(tmp_path, stdin=json.dumps({"session_id": "session-a"}))
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_session_prompt_no_session_id_does_not_prompt(tmp_path):
    _write_session_prompt_config(tmp_path)
    result = _run(tmp_path, stdin="{}")
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_session_prompt_unanswered_session_prompts(tmp_path):
    _write_session_prompt_config(tmp_path)
    result = _run(tmp_path, stdin=json.dumps({"session_id": "session-a"}))
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    ctx = payload["hookSpecificOutput"]["additionalContext"]
    assert payload["hookSpecificOutput"]["hookEventName"] == "SessionStart"
    assert "session_id: session-a" in ctx
    assert "record_checkpoint_choice.py" in ctx


def test_session_prompt_answered_session_is_silent(tmp_path):
    _write_session_prompt_config(tmp_path)
    cps.write_choice("session-a", True, cwd=str(tmp_path))
    result = _run(tmp_path, stdin=json.dumps({"session_id": "session-a"}))
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_session_prompt_answered_false_is_also_silent(tmp_path):
    _write_session_prompt_config(tmp_path)
    cps.write_choice("session-a", False, cwd=str(tmp_path))
    result = _run(tmp_path, stdin=json.dumps({"session_id": "session-a"}))
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_session_prompt_different_session_id_prompts_again(tmp_path):
    _write_session_prompt_config(tmp_path)
    cps.write_choice("session-a", True, cwd=str(tmp_path))
    result = _run(tmp_path, stdin=json.dumps({"session_id": "session-b"}))
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    ctx = payload["hookSpecificOutput"]["additionalContext"]
    assert "session_id: session-b" in ctx


def test_session_prompt_combines_with_scoping_nudge(tmp_path):
    """Both nudges can fire in the same additionalContext string."""
    _write_session_prompt_config(tmp_path)
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "current-state.md").write_text(
        "**Task:** [Task name, e.g., BE Order API]\n", encoding="utf-8",
    )
    result = _run(tmp_path, stdin=json.dumps({"session_id": "session-a"}))
    payload = json.loads(result.stdout)
    ctx = payload["hookSpecificOutput"]["additionalContext"]
    assert "no scoped Current Task" in ctx
    assert "session_id: session-a" in ctx


def test_placeholder_task_never_gets_spec_drift_nudge(tmp_path):
    """An unscoped/placeholder task has no meaningful Required Context yet -- the
    drift check must not run at all for it."""
    repo = tmp_path / "repo"
    docs = repo / "docs" / "specs"
    docs.mkdir(parents=True)
    _git("init", "-q", "-b", "main", cwd=repo)
    _git("config", "user.email", "test@example.com", cwd=repo)
    _git("config", "user.name", "Test", cwd=repo)
    (docs / "api-contract.md").write_text("## GET /orders/{id}\n", encoding="utf-8")
    (repo / "docs" / "current-state.md").write_text(
        "**Task:** [Task name, e.g., BE Order API]\n\n"
        "## Required Context\n\n"
        "* `docs/specs/api-contract.md`\n",
        encoding="utf-8",
    )
    _git("add", ".", cwd=repo)
    _git("commit", "-q", "-m", "base", cwd=repo)
    time.sleep(1.1)
    (docs / "api-contract.md").write_text("## GET /orders/{id}\n## POST /orders\n", encoding="utf-8")
    _git("add", ".", cwd=repo)
    _git("commit", "-q", "-m", "spec changed", cwd=repo)

    result = _run(repo)
    payload = json.loads(result.stdout)
    ctx = payload["hookSpecificOutput"]["additionalContext"]
    assert "changed more recently than current-state.md itself" not in ctx


# ---------------------------------------------------------------------------
# Framework update nudge: opt-in via .project-starter.yml's framework_commit, compared
# against a local git repo standing in for the real GitHub upstream (see
# test_check_framework_update.py -- `git ls-remote` works identically against a local
# path, no network needed).
# ---------------------------------------------------------------------------

def _make_upstream_repo(tmp_path: Path) -> tuple:
    upstream = tmp_path / "upstream"
    upstream.mkdir()
    _git("init", "-q", "-b", "main", cwd=upstream)
    _git("config", "user.email", "test@example.com", cwd=upstream)
    _git("config", "user.name", "Test", cwd=upstream)
    (upstream / "README.md").write_text("hello\n", encoding="utf-8")
    _git("add", ".", cwd=upstream)
    _git("commit", "-q", "-m", "initial", cwd=upstream)
    head = subprocess.run(
        ["git", "rev-parse", "HEAD"], cwd=upstream, capture_output=True, text=True, check=True,
    ).stdout.strip()
    return upstream, head


def test_stale_framework_commit_triggers_update_nudge(tmp_path):
    upstream, old_head = _make_upstream_repo(tmp_path)
    (upstream / "README.md").write_text("hello again\n", encoding="utf-8")
    _git("add", ".", cwd=upstream)
    _git("commit", "-q", "-m", "second commit", cwd=upstream)

    (tmp_path / ".project-starter.yml").write_text(
        f"project_type: web-app\nframework_commit: {old_head}\nframework_repo_url: {upstream}\n",
        encoding="utf-8",
    )
    result = _run(tmp_path)
    assert result.returncode == 0
    payload = json.loads(result.stdout)
    ctx = payload["hookSpecificOutput"]["additionalContext"]
    assert "project_starter_v5" in ctx
    assert "AskUserQuestion" in ctx


def test_up_to_date_framework_commit_is_silent(tmp_path):
    upstream, head = _make_upstream_repo(tmp_path)
    (tmp_path / ".project-starter.yml").write_text(
        f"project_type: web-app\nframework_commit: {head}\nframework_repo_url: {upstream}\n",
        encoding="utf-8",
    )
    result = _run(tmp_path)
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_unset_framework_commit_is_silent(tmp_path):
    (tmp_path / ".project-starter.yml").write_text(
        "project_type: web-app\n", encoding="utf-8",
    )
    result = _run(tmp_path)
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_framework_update_nudge_combines_with_scoping_nudge(tmp_path):
    """Both nudges can fire in the same additionalContext string."""
    upstream, old_head = _make_upstream_repo(tmp_path)
    (upstream / "README.md").write_text("hello again\n", encoding="utf-8")
    _git("add", ".", cwd=upstream)
    _git("commit", "-q", "-m", "second commit", cwd=upstream)
    (tmp_path / ".project-starter.yml").write_text(
        f"project_type: web-app\nframework_commit: {old_head}\nframework_repo_url: {upstream}\n",
        encoding="utf-8",
    )
    docs = tmp_path / "docs"
    docs.mkdir()
    (docs / "current-state.md").write_text(
        "**Task:** [Task name, e.g., BE Order API]\n", encoding="utf-8",
    )
    result = _run(tmp_path)
    payload = json.loads(result.stdout)
    ctx = payload["hookSpecificOutput"]["additionalContext"]
    assert "no scoped Current Task" in ctx
    assert "project_starter_v5" in ctx
