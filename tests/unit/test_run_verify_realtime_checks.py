"""Tests for the real-time gate checks in adapters/claude/run-verify.sh.

project_type_confirmed / Clarifying Questions Asked / Doc Checklist completeness /
Sprint Documentation Sync / verify_docs+logs+tests+content --strict failures are also
enforced by .githooks/pre-commit, but only at `git commit`. A workflow that pulls
once, does a long stretch of local work, then pushes/merges once at the end may go a
very long time without committing -- those gates would barely ever run. This surfaces
the same checks (see .githooks/pre-commit for the original, staged-file/working-tree-
state versions) on every Stop event instead: the first four read the working tree
directly; the validator failures are parsed out of the --json output run-verify.sh
already captures for logs/verify-*.json -- --strict only changes the exit code, never
the JSON content, so no extra validator invocation is needed. An earlier version of
this nudge counted uncommitted files against a threshold instead -- replaced because
that models commit *frequency*, which this workflow deliberately doesn't have (one
commit/push at the end, not many small ones), so a file-count proxy never fired at a
meaningful moment.

Runs the real script via subprocess against a minimal isolated git repo, matching
test_pre_commit_doc_checklist.py's fixture style and test_session_start_hook.py's
subprocess approach -- skipped if bash isn't on PATH.
"""
import json
import subprocess
from pathlib import Path

import pytest

from tests.conftest import find_posix_bash

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
HOOK = REPO_ROOT / "adapters" / "claude" / "run-verify.sh"

_BASH = find_posix_bash()
pytestmark = pytest.mark.skipif(_BASH is None, reason="bash not found on PATH")

_CLOSEOUT_FOOTER = "\n## Closeout (when all Steps and Verify are done)\n\n- Everything done: yes\n"

# Fake validators -- argparse-compatible stand-ins for the real scripts, returning a
# fixed --json payload shaped like a single --strict failure of that validator.
_FAKE_DOCS_MISSING_REQUIRED = (
    "import argparse, json\n"
    "p = argparse.ArgumentParser()\n"
    "p.add_argument('--project-type', required=True)\n"
    "p.add_argument('--content', action='store_true')\n"
    "p.add_argument('--json', action='store_true', dest='json_output')\n"
    "args = p.parse_args()\n"
    "if args.json_output:\n"
    "    print(json.dumps({'results': [{'doc': 'docs/specs/quickstart.md', 'status': 'missing_required'}]}))\n"
)
_FAKE_CHECK_FAIL = (
    "import argparse, json\n"
    "p = argparse.ArgumentParser()\n"
    "p.add_argument('--project-type', required=True)\n"
    "p.add_argument('--json', action='store_true', dest='json_output')\n"
    "args = p.parse_args()\n"
    "if args.json_output:\n"
    "    print(json.dumps({'results': [{'check': 'file exists', 'status': 'fail'}]}))\n"
)
_FAKE_CONTENT_FAIL = (
    "import argparse, json\n"
    "p = argparse.ArgumentParser()\n"
    "p.add_argument('--project-type', required=True)\n"
    "p.add_argument('--json', action='store_true', dest='json_output')\n"
    "args = p.parse_args()\n"
    "if args.json_output:\n"
    "    print(json.dumps({'documents': [{'name': 'quickstart', 'present': False, 'quality': 'fail'}], 'modules': []}))\n"
)


def _make_repo(
    tmp_path: Path,
    *,
    project_type_confirmed_false: bool = False,
    current_state_body: str | None = None,
    sprint_log_body: str | None = None,
    validator_scripts: dict[str, str] | None = None,
) -> Path:
    """Minimal repo satisfying run-verify.sh's own early-exit preconditions
    (.project-starter.yml + docs/script/validators/verify_docs.py must both exist,
    otherwise the script exits before reaching anything this test cares about)."""
    repo = tmp_path / "repo"
    validators = repo / "docs" / "script" / "validators"
    validators.mkdir(parents=True)
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)

    yml = "project_type: web-app\ndocs_path: docs/\n"
    if project_type_confirmed_false:
        yml += "project_type_confirmed: false\n"
    (repo / ".project-starter.yml").write_text(yml, encoding="utf-8")

    validator_scripts = validator_scripts or {}
    for name in ("verify_docs", "verify_logs", "verify_tests", "verify_content"):
        content = validator_scripts.get(name, "print('{}')\n")
        (validators / f"{name}.py").write_text(content, encoding="utf-8")

    if current_state_body is not None:
        (repo / "docs" / "current-state.md").write_text(current_state_body, encoding="utf-8")

    if sprint_log_body is not None:
        (repo / "docs" / "sprint-change-log.md").write_text(sprint_log_body, encoding="utf-8")

    return repo


def _run(repo: Path) -> subprocess.CompletedProcess:
    assert _BASH is not None  # module-level skipif guarantees this by the time we get here
    return subprocess.run(
        [_BASH, str(HOOK)], cwd=repo, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )


def _nudge_context(result: subprocess.CompletedProcess) -> str:
    payload = json.loads(result.stdout)
    assert payload["hookSpecificOutput"]["hookEventName"] == "Stop"
    ctx: str = payload["hookSpecificOutput"]["additionalContext"]
    return ctx


def test_no_issues_produces_no_nudge(tmp_path):
    repo = _make_repo(
        tmp_path,
        current_state_body=(
            "**Task:** Build the order API\n\n"
            "**Clarifying Questions Asked:** Y\n\n"
            "**Status:** In Progress\n\n"
            "## Doc Checklist (this task only)\n\n"
            "- [x] `docs/specs/api-contract.md` — endpoint added\n"
            + _CLOSEOUT_FOOTER
        ),
    )
    result = _run(repo)
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_project_type_confirmed_false_produces_nudge(tmp_path):
    repo = _make_repo(tmp_path, project_type_confirmed_false=True)
    result = _run(repo)
    assert result.returncode == 0
    ctx = _nudge_context(result)
    assert "project_type_confirmed" in ctx


def test_real_task_missing_cqa_produces_nudge(tmp_path):
    repo = _make_repo(
        tmp_path,
        current_state_body=(
            "**Task:** Build the order API\n\n"
            "**Clarifying Questions Asked:** [Y / N/A — reason]\n\n"
            "**Status:** In Progress\n\n"
        ),
    )
    result = _run(repo)
    assert result.returncode == 0
    ctx = _nudge_context(result)
    assert "Clarifying Questions Asked" in ctx


def test_placeholder_task_does_not_trigger_cqa_check(tmp_path):
    repo = _make_repo(
        tmp_path,
        current_state_body=(
            "**Task:** [Task name, e.g., BE Order API]\n\n"
            "**Clarifying Questions Asked:** [Y / N/A — reason]\n\n"
            "**Status:** In Progress\n\n"
        ),
    )
    result = _run(repo)
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_complete_with_unchecked_doc_checklist_produces_nudge(tmp_path):
    repo = _make_repo(
        tmp_path,
        current_state_body=(
            "**Task:** Build the order API\n\n"
            "**Clarifying Questions Asked:** Y\n\n"
            "**Status:** Complete — Pending Sprint Doc Sync\n\n"
            "## Doc Checklist (this task only)\n\n"
            "- [ ] `docs/architecture/architecture.md` — check if diagram needs updating\n"
            + _CLOSEOUT_FOOTER
        ),
    )
    result = _run(repo)
    assert result.returncode == 0
    ctx = _nudge_context(result)
    assert "Doc Checklist" in ctx


def test_complete_with_all_checked_does_not_trigger_doc_checklist_nudge(tmp_path):
    repo = _make_repo(
        tmp_path,
        current_state_body=(
            "**Task:** Build the order API\n\n"
            "**Clarifying Questions Asked:** Y\n\n"
            "**Status:** Complete — Pending Sprint Doc Sync\n\n"
            "## Doc Checklist (this task only)\n\n"
            "- [x] `docs/architecture/architecture.md` — no changes needed\n"
            + _CLOSEOUT_FOOTER
        ),
    )
    result = _run(repo)
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_multiple_issues_combined_in_one_nudge(tmp_path):
    repo = _make_repo(
        tmp_path,
        project_type_confirmed_false=True,
        current_state_body=(
            "**Task:** Build the order API\n\n"
            "**Clarifying Questions Asked:** [Y / N/A — reason]\n\n"
            "**Status:** In Progress\n\n"
        ),
    )
    result = _run(repo)
    assert result.returncode == 0
    ctx = _nudge_context(result)
    assert "project_type_confirmed" in ctx
    assert "Clarifying Questions Asked" in ctx


def test_three_pending_sprint_entries_produces_nudge(tmp_path):
    body = "# Sprint Change Log\n\n" + "".join(
        f"### Task: {n}\n**Status:** Pending documentation synchronization\n---\n\n"
        for n in ("A", "B", "C")
    )
    repo = _make_repo(tmp_path, sprint_log_body=body)
    result = _run(repo)
    assert result.returncode == 0
    ctx = _nudge_context(result)
    assert "Sprint Documentation Sync" in ctx
    assert "3 entries" in ctx


def test_two_pending_sprint_entries_does_not_trigger_nudge(tmp_path):
    body = "# Sprint Change Log\n\n" + "".join(
        f"### Task: {n}\n**Status:** Pending documentation synchronization\n---\n\n"
        for n in ("A", "B")
    )
    repo = _make_repo(tmp_path, sprint_log_body=body)
    result = _run(repo)
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_no_sprint_change_log_does_not_crash(tmp_path):
    repo = _make_repo(tmp_path, sprint_log_body=None)
    result = _run(repo)
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_verify_docs_missing_required_produces_nudge(tmp_path):
    repo = _make_repo(tmp_path, validator_scripts={"verify_docs": _FAKE_DOCS_MISSING_REQUIRED})
    result = _run(repo)
    assert result.returncode == 0
    ctx = _nudge_context(result)
    assert "verify_docs.py would fail --strict" in ctx
    assert "docs/specs/quickstart.md" in ctx


def test_verify_logs_fail_produces_nudge(tmp_path):
    repo = _make_repo(tmp_path, validator_scripts={"verify_logs": _FAKE_CHECK_FAIL})
    result = _run(repo)
    assert result.returncode == 0
    ctx = _nudge_context(result)
    assert "verify_logs.py would fail --strict" in ctx
    assert "file exists" in ctx


def test_verify_tests_fail_produces_nudge(tmp_path):
    repo = _make_repo(tmp_path, validator_scripts={"verify_tests": _FAKE_CHECK_FAIL})
    result = _run(repo)
    assert result.returncode == 0
    ctx = _nudge_context(result)
    assert "verify_tests.py would fail --strict" in ctx


def test_verify_content_fail_produces_nudge(tmp_path):
    repo = _make_repo(tmp_path, validator_scripts={"verify_content": _FAKE_CONTENT_FAIL})
    result = _run(repo)
    assert result.returncode == 0
    ctx = _nudge_context(result)
    assert "verify_content.py would fail --strict" in ctx
    assert "quickstart" in ctx


def test_all_validators_passing_produces_no_validator_nudge(tmp_path):
    """Default fixture validators print '{}' (no results/documents keys at all) --
    the JSON parser must treat a missing key as zero failures, not crash."""
    repo = _make_repo(tmp_path)
    result = _run(repo)
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_still_writes_the_verify_log_alongside_the_nudge(tmp_path):
    """The nudge is additive -- it must not replace or break the existing verify-*.json
    log this script already wrote before this feature existed."""
    repo = _make_repo(tmp_path, project_type_confirmed_false=True)
    _run(repo)
    logs = list((repo / "logs").glob("verify-*.json"))
    assert len(logs) == 1
    data = json.loads(logs[0].read_text(encoding="utf-8"))
    assert isinstance(data, list)
    assert len(data) == 4  # docs, logs, tests, content — one entry each


def test_uninitialised_project_skips_before_reaching_the_nudge(tmp_path):
    """No .project-starter.yml -- the script's own pre-existing early exit fires first;
    the nudge logic must never run (and never crash) in that path."""
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q", "-b", "main"], cwd=repo, check=True)
    result = _run(repo)
    assert result.returncode == 0
    assert result.stdout.strip() == ""


def test_no_current_state_md_does_not_crash(tmp_path):
    """docs/current-state.md may not exist yet (fresh --init project) -- the CQA and
    Doc Checklist checks must be skipped, not crash, when there's nothing to read."""
    repo = _make_repo(tmp_path, project_type_confirmed_false=False)
    result = _run(repo)
    assert result.returncode == 0
    assert result.stdout.strip() == ""
