import subprocess
import sys

import pytest

from tests.snapshot.conftest import (
    REPO_ROOT,
    assert_snapshot,
    normalize,
    patched_project_type,
)

_ORCHESTRATOR = REPO_ROOT / "orchestrator.py"

COMBOS = [
    ("web-app", "feature"),
    ("data-pipeline", "pipeline-stage"),
]


@pytest.mark.parametrize("project_type,task_type", COMBOS, ids=[f"{p}__{t}" for p, t in COMBOS])
def test_orchestrator_snapshot(project_type, task_type, snapshot_update):
    with patched_project_type(project_type):
        result = subprocess.run(
            [
                sys.executable, str(_ORCHESTRATOR),
                "--dry-run",
                "--task-type", task_type,
            ],
            capture_output=True,
            text=True,
            cwd=str(REPO_ROOT),
        )
    assert result.returncode == 0, f"orchestrator.py failed:\n{result.stderr}"
    assert_snapshot(
        f"orchestrator__{project_type}__{task_type}.md",
        normalize(result.stdout),
        snapshot_update,
    )
