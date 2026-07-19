import subprocess
import sys

import pytest

from tests.snapshot.conftest import (
    _BUILD_CONTEXT_FILES,
    assert_snapshot,
    normalize,
    setup_snapshot_project,
)

COMBOS = [
    ("web-app", "feature"),
    ("data-pipeline", "pipeline-stage"),
    ("llm-app", "eval-run"),
]


@pytest.mark.parametrize("project_type,task_type", COMBOS, ids=[f"{p}__{t}" for p, t in COMBOS])
def test_build_context_snapshot(project_type, task_type, snapshot_update, tmp_path):
    proj = setup_snapshot_project(tmp_path, project_type, extra_files=_BUILD_CONTEXT_FILES)
    result = subprocess.run(
        [sys.executable, "build-context.py", "--dry-run", "--task-type", task_type],
        capture_output=True,
        text=True,
        cwd=str(proj),
    )
    assert result.returncode == 0, f"build-context.py failed:\n{result.stderr}"
    assert_snapshot(
        f"build_context__{project_type}__{task_type}.md",
        normalize(result.stdout),
        snapshot_update,
    )
