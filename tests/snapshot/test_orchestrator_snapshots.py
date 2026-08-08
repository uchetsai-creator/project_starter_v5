import os
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
    # PYTHONUTF8 forces the child's own stdout/stderr encoding to UTF-8, matching the
    # encoding="utf-8" this decodes with — see golden test helpers for the full rationale.
    result = subprocess.run(
        [sys.executable, "orchestrator.py", "--dry-run", "--task-type", task_type],
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={**os.environ, "PYTHONUTF8": "1"},
        cwd=str(proj),
    )
    assert result.returncode == 0, f"orchestrator.py failed:\n{result.stderr}"
    assert_snapshot(
        f"orchestrator__{project_type}__{task_type}.md",
        normalize(result.stdout),
        snapshot_update,
    )
