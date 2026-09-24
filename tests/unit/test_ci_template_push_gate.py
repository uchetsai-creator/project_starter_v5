"""The CI template must run the same requirement gate `git push` runs, so `git push --no-verify`
is not a way around it.

Extracts the actual `run:` script of the "Run pre-push requirement gate" step from
templates/ci/github-actions-verify.yml and executes it with bash in an isolated git repo, with the
env vars GitHub Actions would provide (HEAD_SHA = PR head commit, BASE_REF = the PR's base branch).
Skipped if bash isn't on PATH.
"""
import os
import re
import shutil
import subprocess
import textwrap
from pathlib import Path

import pytest

from tests.conftest import find_posix_bash
from tests.unit.test_pre_push import _git, _make_repo, _state

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
TEMPLATE = REPO_ROOT / "templates" / "ci" / "github-actions-verify.yml"
HOOK = REPO_ROOT / ".githooks" / "pre-push"

_BASH = find_posix_bash()
pytestmark = pytest.mark.skipif(_BASH is None, reason="bash not found on PATH")


def _gate_script() -> str:
    text = TEMPLATE.read_text(encoding="utf-8")
    m = re.search(r"- name: Run pre-push requirement gate\n(?:.*\n)*?\s+run: \|\n((?:\s{10,}.*\n?)+)", text)
    assert m, "CI template has no 'Run pre-push requirement gate' step with a run: block"
    return textwrap.dedent(m.group(1))


def _run_gate(repo: Path, base_ref: str) -> subprocess.CompletedProcess:
    assert _BASH is not None
    (repo / ".githooks").mkdir(exist_ok=True)
    shutil.copy2(HOOK, repo / ".githooks" / "pre-push")
    env = {**os.environ, "HEAD_SHA": _git(repo, "rev-parse", "HEAD"), "BASE_REF": base_ref}
    return subprocess.run(
        [_BASH, "-c", _gate_script()], cwd=repo, capture_output=True, text=True,
        encoding="utf-8", errors="replace", env=env,
    )


def test_template_has_the_gate_step_after_the_pre_commit_step():
    text = TEMPLATE.read_text(encoding="utf-8")
    assert text.index("bash .githooks/pre-commit") < text.index("Run pre-push requirement gate")
    assert ".githooks/pre-push" in _gate_script()


def test_ci_gate_blocks_a_pr_into_main_while_the_requirement_is_in_progress(tmp_path):
    result = _run_gate(_make_repo(tmp_path, _state("In Progress")), "main")
    assert result.returncode == 1, result.stdout + result.stderr
    assert "Requirement Status is In Progress" in result.stdout


def test_ci_gate_only_warns_for_a_pr_into_a_non_gated_branch(tmp_path):
    result = _run_gate(_make_repo(tmp_path, _state("In Progress")), "develop")
    assert result.returncode == 0, result.stdout + result.stderr
    assert "[WARN]" in result.stdout


def test_ci_gate_passes_a_verified_complete_requirement(tmp_path):
    result = _run_gate(_make_repo(tmp_path, _state("Complete")), "main")
    assert result.returncode == 0, result.stdout + result.stderr
