"""Parametrized orchestrator --dry-run smoke test across all 9 project types."""
import subprocess
import sys

import pytest

from tests.conftest import VALID_TYPES, setup_fixture

_TASK_TYPE_FOR = {
    "web-app": "feature",
    "cli-tool": "feature",
    "library": "feature",
    "data-pipeline": "pipeline-stage",
    "ml-pipeline": "pipeline-stage",
    "microservices": "feature",
    "llm-app": "eval-run",
    "iac": "iac-change",
    "mobile-app": "feature",
}

# Keyword expected in AI_CONTEXT.md after build-context runs for each project type
_CONTEXT_KEYWORD_FOR = {
    "web-app": "api-contract",
    "cli-tool": "cli-contract",
    "library": "public-api",
    "data-pipeline": "pipeline-contract",
    "ml-pipeline": "pipeline-contract",
    "microservices": "service-catalog",
    "llm-app": "eval-run",
    "iac": "runbook",
    "mobile-app": "mobile-contract",
}


@pytest.mark.parametrize("project_type", VALID_TYPES)
def test_e2e_all_types_orchestrator_dry_run(tmp_path, project_type):
    task_type = _TASK_TYPE_FOR[project_type]
    setup_fixture(tmp_path, project_type=project_type, task_type=task_type)

    result = subprocess.run(
        [sys.executable, "orchestrator.py", "--dry-run", "--task-type", task_type],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"orchestrator --dry-run failed for {project_type}:\n{result.stderr}"
    )
    assert "verify_docs.py" in result.stdout, (
        f"verify_docs.py not in orchestrator output for {project_type}"
    )

    subprocess.run(
        [sys.executable, "build-context.py", "--task-type", task_type],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        check=True,
    )
    context = (tmp_path / ".ai/AI_CONTEXT.md").read_text(encoding="utf-8")
    keyword = _CONTEXT_KEYWORD_FOR[project_type]
    assert keyword in context, (
        f"'{keyword}' not found in AI_CONTEXT.md for {project_type}"
    )
