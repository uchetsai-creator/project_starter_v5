"""Regression tests for a nested/custom `docs_path` (e.g. a monorepo subproject using
`docs/isbg/` instead of the default `docs/`).

Two bugs fixed together, both only visible with a nested docs_path:
1. `.githooks/pre-commit` and `.githooks/pre-push` parsed `docs_path` with
   `tr -d "\"' /"`, which stripped the internal `/` too -- `docs/isbg/` became the
   single path segment `docsisbg`, breaking every lookup derived from it (the
   Current-Task scope guard's NON_SOURCE_REGEX, and the validator script paths below).
2. Validator scripts (`docs/script/validators/...`) were looked up at a literal,
   non-docs_path-aware path throughout both hooks and `orchestrator.py`'s rendered
   `.ai/WORKFLOW.md`, instead of `{docs_path}/script/validators/...` -- they only
   worked by coincidence when docs_path was the default `docs/`.

Runs the real bash scripts via subprocess against a minimal isolated git repo, matching
test_pre_commit_clarifications.py / test_pre_push.py -- skipped if bash isn't on PATH.
"""
import shutil
import subprocess
from pathlib import Path

import pytest

from tests.conftest import find_posix_bash

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
PRE_COMMIT = REPO_ROOT / ".githooks" / "pre-commit"
PRE_PUSH = REPO_ROOT / ".githooks" / "pre-push"
VALIDATORS = REPO_ROOT / "templates" / "script" / "validators"

_BASH = find_posix_bash()
pytestmark = pytest.mark.skipif(_BASH is None, reason="bash not found on PATH")

_NESTED_DOCS = "docs/isbg"


def _git(repo: Path, *args: str) -> str:
    return subprocess.run(["git", *args], cwd=repo, check=True, capture_output=True, text=True).stdout.strip()


def _make_nested_repo(tmp_path: Path) -> Path:
    repo = tmp_path / "repo"
    repo.mkdir()
    _git(repo, "init", "-q")
    _git(repo, "config", "user.email", "test@example.com")
    _git(repo, "config", "user.name", "Test")
    (repo / ".project-starter.yml").write_text(
        f"project_type: web-app\ndocs_path: {_NESTED_DOCS}/\ntask_type:\n"
        "spec_code_adapter:\nspec_code_spec:\nspec_code_src:\n",
        encoding="utf-8",
    )
    docs = repo / _NESTED_DOCS
    docs.mkdir(parents=True)
    (docs / "current-state.md").write_text(
        "## Current Task\n\n**Task:** Documentation retrofit complete — ready for new tasks\n\n"
        "**Status:** Complete — Pending Milestone Doc Sync\n", encoding="utf-8",
    )
    shutil.copytree(VALIDATORS, docs / "script" / "validators",
                     ignore=shutil.ignore_patterns("__pycache__"))
    return repo


def test_pre_commit_resolves_nested_docs_path(tmp_path):
    repo = _make_nested_repo(tmp_path)
    (repo / _NESTED_DOCS / "current-state.md").write_text(
        (repo / _NESTED_DOCS / "current-state.md").read_text(encoding="utf-8") + "\nNote.\n",
        encoding="utf-8",
    )
    _git(repo, "add", "-A")
    result = subprocess.run(
        [_BASH, str(PRE_COMMIT)], cwd=repo, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )
    out = result.stdout + result.stderr
    assert f"docs={_NESTED_DOCS}" in out, out
    assert "docs=docsisbg" not in out, out
    assert "verify_docs.py not found" not in out, out


def test_pre_push_resolves_nested_docs_path(tmp_path):
    repo = _make_nested_repo(tmp_path)
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "--no-verify", "-m", "init")
    local_sha = _git(repo, "rev-parse", "HEAD")
    zero = "0" * 40
    stdin = f"refs/heads/work {local_sha} refs/heads/work {zero}\n"
    result = subprocess.run(
        [_BASH, str(PRE_PUSH)], cwd=repo, input=stdin, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )
    out = result.stdout + result.stderr
    assert "docsisbg" not in out, out


def test_orchestrator_render_prefixes_custom_docs_path():
    import importlib.util

    orch_path = REPO_ROOT / "orchestrator.py"
    spec = importlib.util.spec_from_file_location("orchestrator", orch_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    ctx = {
        "task_type": "feature",
        "project_type": "web-app",
        "workflow_key": "feature",
        "docs_path": _NESTED_DOCS,
        "validators": [{"script": "docs/script/validators/verify_docs.py", "args": ["--content"]}],
    }
    out = mod._render(ctx)
    assert f"{_NESTED_DOCS}/script/validators/verify_docs.py" in out, out
    assert "`docs/script/validators/verify_docs.py" not in out, out
    assert f"`{_NESTED_DOCS}/current-state.md`" in out, out


def test_orchestrator_render_default_docs_path_unchanged():
    import importlib.util

    orch_path = REPO_ROOT / "orchestrator.py"
    spec = importlib.util.spec_from_file_location("orchestrator", orch_path)
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)

    ctx = {
        "task_type": "feature",
        "project_type": "web-app",
        "workflow_key": "feature",
        "docs_path": "docs",
        "validators": [{"script": "docs/script/validators/verify_docs.py", "args": []}],
    }
    out = mod._render(ctx)
    assert "docs/script/validators/verify_docs.py" in out, out
