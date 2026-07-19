"""Full pipeline E2E tests for representative project types."""
import subprocess
import sys

import pytest

from tests.conftest import REPO_ROOT, setup_fixture


def _run(args, tmp_path, **kwargs):
    return subprocess.run(args, cwd=str(tmp_path), capture_output=True, text=True, **kwargs)


# ---------------------------------------------------------------------------
# web-app
# ---------------------------------------------------------------------------

def test_e2e_web_app(tmp_path):
    setup_fixture(tmp_path, project_type="web-app", task_type="feature")

    # orchestrator --dry-run produces a workflow mentioning the expected validators
    result = _run([sys.executable, "orchestrator.py", "--dry-run", "--task-type", "feature"], tmp_path)
    assert result.returncode == 0, f"orchestrator failed:\n{result.stderr}"
    assert "verify_docs.py" in result.stdout
    assert "verify_content.py" in result.stdout

    # build-context writes .ai/AI_CONTEXT.md
    _run([sys.executable, "build-context.py", "--task-type", "feature"], tmp_path, check=True)
    context = (tmp_path / ".ai/AI_CONTEXT.md").read_text(encoding="utf-8")
    assert "api-contract.md" in context
    assert "permissions.md" in context

    # verify_docs exits 0 (all required docs present)
    result = _run(
        [sys.executable, "docs/script/validators/verify_docs.py",
         "--project-type", "web-app", "--docs", "docs"],
        tmp_path,
    )
    assert result.returncode == 0, f"verify_docs failed:\n{result.stdout}"

    # verify_content exits 0 (all required docs have real content)
    result = _run(
        [sys.executable, "docs/script/validators/verify_content.py",
         "--project-type", "web-app", "--docs", "docs", "--strict"],
        tmp_path,
    )
    assert result.returncode == 0, f"verify_content failed:\n{result.stdout}"


# ---------------------------------------------------------------------------
# data-pipeline
# ---------------------------------------------------------------------------

def test_e2e_data_pipeline(tmp_path):
    setup_fixture(tmp_path, project_type="data-pipeline", task_type="pipeline-stage")

    result = _run(
        [sys.executable, "orchestrator.py", "--dry-run", "--task-type", "pipeline-stage"],
        tmp_path,
    )
    assert result.returncode == 0, f"orchestrator failed:\n{result.stderr}"
    assert "verify_docs.py" in result.stdout

    _run([sys.executable, "build-context.py", "--task-type", "pipeline-stage"], tmp_path, check=True)
    context = (tmp_path / ".ai/AI_CONTEXT.md").read_text(encoding="utf-8")
    assert "pipeline-contract.md" in context

    result = _run(
        [sys.executable, "docs/script/validators/verify_docs.py",
         "--project-type", "data-pipeline", "--docs", "docs"],
        tmp_path,
    )
    assert result.returncode == 0, f"verify_docs failed:\n{result.stdout}"

    result = _run(
        [sys.executable, "docs/script/validators/verify_content.py",
         "--project-type", "data-pipeline", "--docs", "docs", "--strict"],
        tmp_path,
    )
    assert result.returncode == 0, f"verify_content failed:\n{result.stdout}"


# ---------------------------------------------------------------------------
# llm-app
# ---------------------------------------------------------------------------

def test_e2e_llm_app(tmp_path):
    setup_fixture(tmp_path, project_type="llm-app", task_type="eval-run")

    result = _run(
        [sys.executable, "orchestrator.py", "--dry-run", "--task-type", "eval-run"],
        tmp_path,
    )
    assert result.returncode == 0, f"orchestrator failed:\n{result.stderr}"

    _run([sys.executable, "build-context.py", "--task-type", "eval-run"], tmp_path, check=True)
    context = (tmp_path / ".ai/AI_CONTEXT.md").read_text(encoding="utf-8")
    assert "llm-contract.md" in context

    result = _run(
        [sys.executable, "docs/script/validators/verify_docs.py",
         "--project-type", "llm-app", "--docs", "docs"],
        tmp_path,
    )
    assert result.returncode == 0, f"verify_docs failed:\n{result.stdout}"

    result = _run(
        [sys.executable, "docs/script/validators/verify_content.py",
         "--project-type", "llm-app", "--docs", "docs", "--strict"],
        tmp_path,
    )
    assert result.returncode == 0, f"verify_content failed:\n{result.stdout}"
