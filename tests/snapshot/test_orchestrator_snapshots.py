import subprocess
import sys

import pytest

from tests.snapshot.conftest import (
    assert_snapshot,
    normalize,
    setup_snapshot_project,
)

COMBOS = [
    ("web-app", "feature"),
    ("data-pipeline", "pipeline-stage"),
    ("cli-tool", "feature"),
    ("library", "feature"),
    ("microservices", "feature"),
    ("llm-app", "eval-run"),
    ("iac", "iac-change"),
    ("mobile-app", "feature"),
    ("ml-pipeline", "pipeline-stage"),
]


@pytest.mark.parametrize("project_type,task_type", COMBOS, ids=[f"{p}__{t}" for p, t in COMBOS])
def test_orchestrator_snapshot(project_type, task_type, snapshot_update, tmp_path):
    proj = setup_snapshot_project(tmp_path, project_type)
    result = subprocess.run(
        [sys.executable, "orchestrator.py", "--dry-run", "--task-type", task_type],
        capture_output=True,
        text=True,
        cwd=str(proj),
    )
    assert result.returncode == 0, f"orchestrator.py failed:\n{result.stderr}"
    assert_snapshot(
        f"orchestrator__{project_type}__{task_type}.md",
        normalize(result.stdout),
        snapshot_update,
    )
