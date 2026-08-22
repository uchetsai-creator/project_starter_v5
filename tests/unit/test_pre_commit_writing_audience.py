"""Tests for the Writing Audience violations guard in .githooks/pre-commit.

Previously hardcoded to a handful of `audience: external` documents (business-rules.md,
pipeline-contract.md, research.md, quickstart.md, architecture/*.md, module data-flow
files) -- `audience` in document-registry.yaml only ever meant "is this in the generated
PDF for stakeholders," never "is per-task planning narrative acceptable here." Every
document registered in document-registry.yaml describes the system's *current* state;
current-state.md's Steps section and sprint-change-log.md are deliberately NOT in the
registry -- that's where task/sprint narrative actually belongs. The guard now reads
every document's path from document-registry.yaml dynamically (single source of truth)
instead of a second hardcoded list, so `audience: internal` contract docs like
api-contract.md are covered too.

Runs the real bash script via subprocess against a minimal isolated git repo, matching
test_pre_commit_doc_checklist.py's approach -- skipped if bash isn't on PATH.
"""
import shutil
import subprocess
from pathlib import Path

import pytest

from tests.conftest import find_posix_bash

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
HOOK = REPO_ROOT / ".githooks" / "pre-commit"

_BASH = find_posix_bash()
pytestmark = pytest.mark.skipif(_BASH is None, reason="bash not found on PATH")


def _make_repo(tmp_path: Path, doc_relpath: str, doc_body: str) -> Path:
    """doc_relpath is relative to docs/ (matching document-registry.yaml's `path` field),
    e.g. "specs/api-contract.md"."""
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)

    (repo / ".project-starter.yml").write_text(
        "project_type: web-app\ndocs_path: docs/\n", encoding="utf-8",
    )
    shutil.copy2(REPO_ROOT / "document-registry.yaml", repo / "document-registry.yaml")
    shutil.copy2(REPO_ROOT / "_workflow_utils.py", repo / "_workflow_utils.py")

    doc_path = repo / "docs" / doc_relpath
    doc_path.parent.mkdir(parents=True, exist_ok=True)
    doc_path.write_text(doc_body, encoding="utf-8")

    subprocess.run(["git", "add", "."], cwd=repo, check=True)
    return repo


def _run_hook(repo: Path) -> subprocess.CompletedProcess:
    assert _BASH is not None  # module-level skipif guarantees this by the time we get here
    return subprocess.run(
        [_BASH, str(HOOK)], cwd=repo, capture_output=True, text=True,
        encoding="utf-8", errors="replace",
    )


def test_task_reference_in_internal_contract_doc_now_blocks(tmp_path):
    """api-contract.md is audience: internal -- previously entirely outside this guard's
    hardcoded list, so this used to pass clean. Confirms the regression this gap allowed
    is now caught."""
    repo = _make_repo(
        tmp_path, "specs/api-contract.md",
        "## GET /orders/{id}\nImplemented in Sprint 3, see Task 42 for the plan.\n",
    )
    result = _run_hook(repo)
    assert "Writing Audience violations" in result.stdout
    assert "api-contract.md" in result.stdout
    assert result.returncode == 1


def test_task_reference_in_external_doc_still_blocks(tmp_path):
    """Regression coverage for the pre-existing behavior (architecture.md is
    audience: external) -- must still work after switching to the registry-driven list."""
    repo = _make_repo(
        tmp_path, "architecture/architecture.md",
        "## Components\nAdded in Sprint 2 (Task 10).\n",
    )
    result = _run_hook(repo)
    assert "Writing Audience violations" in result.stdout
    assert result.returncode == 1


def test_clean_internal_contract_doc_does_not_block(tmp_path):
    repo = _make_repo(
        tmp_path, "specs/api-contract.md",
        "## GET /orders/{id}\nReturns basic order info.\n",
    )
    result = _run_hook(repo)
    assert "Writing Audience" not in result.stdout
    assert result.returncode == 0


def test_per_module_data_flow_file_still_blocks(tmp_path):
    """Regression: module-data-flow files (index + one per module) are NOT in
    document-registry.yaml at all -- their exact paths depend on however many modules
    a project has, so there's no fixed path to register. Switching to a purely
    registry-driven list silently dropped this coverage entirely; a supplementary
    pattern match restores it. Module name ("orders") is dynamic on purpose -- this
    must work for a name never seen at registry-authoring time."""
    repo = _make_repo(
        tmp_path, "modules/orders/orders-module-data-flow.md",
        "## Overview\nImplemented in Sprint 4, see Task 55.\n",
    )
    result = _run_hook(repo)
    assert "Writing Audience violations" in result.stdout
    assert "orders-module-data-flow.md" in result.stdout
    assert result.returncode == 1


def test_module_data_flow_index_file_still_blocks(tmp_path):
    repo = _make_repo(
        tmp_path, "modules/module-data-flow.md",
        "| orders | Sprint 4, Task 55 |\n",
    )
    result = _run_hook(repo)
    assert "Writing Audience violations" in result.stdout
    assert result.returncode == 1


def test_clean_per_module_data_flow_file_does_not_block(tmp_path):
    repo = _make_repo(
        tmp_path, "modules/orders/orders-module-data-flow.md",
        "## Overview\nHandles order creation and lookup.\n",
    )
    result = _run_hook(repo)
    assert "Writing Audience" not in result.stdout
    assert result.returncode == 0


# ---------------------------------------------------------------------------
# The other three open-ended per-item families -- never covered even by the old
# hardcoded regex (module-data-flow was the only one this guard ever checked before
# switching to the registry-driven list), closed now since it's the same mechanism.
# ---------------------------------------------------------------------------

def test_per_module_flow_file_blocks(tmp_path):
    repo = _make_repo(
        tmp_path, "modules/orders/orders-flow.md",
        "## Overview\nAdded in Sprint 5, Task 60.\n",
    )
    result = _run_hook(repo)
    assert "Writing Audience violations" in result.stdout
    assert result.returncode == 1


def test_per_business_object_file_blocks(tmp_path):
    repo = _make_repo(
        tmp_path, "business/order-object.md",
        "# Order object\nAdded Task 61.\n",
    )
    result = _run_hook(repo)
    assert "Writing Audience violations" in result.stdout
    assert result.returncode == 1


def test_per_business_process_file_blocks(tmp_path):
    repo = _make_repo(
        tmp_path, "business/checkout-process.md",
        "# Checkout process\n(S2) implemented.\n",
    )
    result = _run_hook(repo)
    assert "Writing Audience violations" in result.stdout
    assert result.returncode == 1


def test_per_prompt_file_blocks(tmp_path):
    repo = _make_repo(
        tmp_path, "specs/prompts/summarize-prompt.md",
        "# Prompt\nSprint 6, Task 62.\n",
    )
    result = _run_hook(repo)
    assert "Writing Audience violations" in result.stdout
    assert result.returncode == 1


def test_clean_business_object_file_does_not_block(tmp_path):
    repo = _make_repo(
        tmp_path, "business/order-object.md",
        "# Order object\nRepresents a customer order.\n",
    )
    result = _run_hook(repo)
    assert "Writing Audience" not in result.stdout
    assert result.returncode == 0


def test_a_file_matching_both_registry_and_pattern_is_not_reported_twice(tmp_path):
    """business/business-process.md is both the registered index AND matches the
    per-item ".*-process.md$" pattern -- must be deduped, not reported twice."""
    repo = _make_repo(
        tmp_path, "business/business-process.md",
        "# Business Process Index\nSprint 7, Task 70.\n",
    )
    result = _run_hook(repo)
    assert result.stdout.count("business-process.md:") == 1


def test_current_state_md_is_not_covered_by_this_guard(tmp_path):
    """current-state.md is deliberately NOT in document-registry.yaml -- its own Steps
    section is where per-task Sprint/Task references belong. Must never be flagged.
    (Clarifying Questions Asked is filled in so the *other*, unrelated pre-commit guard
    that checks it doesn't also fail this fixture for a reason unrelated to this test.)"""
    repo = _make_repo(
        tmp_path, "current-state.md",
        "**Task:** x\n\n**Clarifying Questions Asked:** Y\n\n## Steps\n- [ ] Step 1 (Sprint 3, Task 42)\n",
    )
    result = _run_hook(repo)
    assert "Writing Audience" not in result.stdout
    assert result.returncode == 0


def test_sprint_change_log_is_not_covered_by_this_guard(tmp_path):
    """sprint-change-log.md is deliberately NOT in document-registry.yaml -- it IS the
    historical record; Sprint/Task references there are the whole point, not a leak."""
    repo = _make_repo(
        tmp_path, "sprint-change-log.md",
        "### Task: A\n**Status:** Pending documentation synchronization\n",
    )
    result = _run_hook(repo)
    assert "Writing Audience" not in result.stdout
    assert result.returncode == 0


def test_missing_document_registry_does_not_crash(tmp_path):
    """Without document-registry.yaml (e.g. a project that predates it, or a manual
    partial install), REGISTRY_DOC_PATHS resolves empty -- must degrade to "nothing
    checked", not crash the whole hook."""
    repo = tmp_path / "repo"
    repo.mkdir()
    subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
    subprocess.run(["git", "config", "user.name", "Test"], cwd=repo, check=True)
    (repo / ".project-starter.yml").write_text(
        "project_type: web-app\ndocs_path: docs/\n", encoding="utf-8",
    )
    docs = repo / "docs" / "specs"
    docs.mkdir(parents=True)
    (docs / "api-contract.md").write_text("Sprint 3, Task 42\n", encoding="utf-8")
    subprocess.run(["git", "add", "."], cwd=repo, check=True)

    result = _run_hook(repo)
    assert "Writing Audience" not in result.stdout
    assert result.returncode == 0
