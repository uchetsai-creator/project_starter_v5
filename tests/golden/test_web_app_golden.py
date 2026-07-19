"""Golden regression tests for web-app example project."""
import subprocess
import sys
from pathlib import Path

import pytest

from tests.golden.conftest import (
    REPO_ROOT,
    assert_golden,
    normalize,
    setup_golden_project,
)

_VERIFY_REGISTRY = REPO_ROOT / "templates/script/validators/verify_registry.py"
_VERIFY_DOCS = REPO_ROOT / "templates/script/validators/verify_docs.py"
_VERIFY_CONTENT = REPO_ROOT / "templates/script/validators/verify_content.py"

PROJECT_TYPE = "web-app"
TASK_TYPE = "feature"


def _run(args, cwd, **kwargs):
    return subprocess.run(args, cwd=str(cwd), capture_output=True, text=True, **kwargs)


def test_orchestrator_dry_run(snapshot_update, tmp_path):
    proj = setup_golden_project(tmp_path, PROJECT_TYPE)
    result = _run(
        [sys.executable, "orchestrator.py", "--dry-run", "--task-type", TASK_TYPE],
        proj,
    )
    assert result.returncode == 0, f"orchestrator failed:\n{result.stderr}"
    assert_golden(f"golden_{PROJECT_TYPE}_orchestrator.md", normalize(result.stdout), snapshot_update)


def test_build_context_dry_run(snapshot_update, tmp_path):
    proj = setup_golden_project(tmp_path, PROJECT_TYPE)
    result = _run(
        [sys.executable, "build-context.py", "--dry-run", "--task-type", TASK_TYPE],
        proj,
    )
    assert result.returncode == 0, f"build-context failed:\n{result.stderr}"
    assert_golden(f"golden_{PROJECT_TYPE}_build_context.md", normalize(result.stdout), snapshot_update)


def test_verify_registry(tmp_path):
    proj = setup_golden_project(tmp_path, PROJECT_TYPE)
    result = _run(
        [sys.executable, str(_VERIFY_REGISTRY), "--registry", str(REPO_ROOT / "document-registry.yaml")],
        proj,
    )
    assert result.returncode == 0, f"verify_registry failed:\n{result.stdout}"


def test_verify_docs_snapshot(snapshot_update, tmp_path):
    proj = setup_golden_project(tmp_path, PROJECT_TYPE)
    result = _run(
        [sys.executable, str(_VERIFY_DOCS), "--project-type", PROJECT_TYPE, "--docs", "docs", "--json"],
        proj,
    )
    assert result.returncode == 0, f"verify_docs failed:\n{result.stdout}"
    assert_golden(f"golden_{PROJECT_TYPE}_verify_docs.json", result.stdout, snapshot_update)


def test_verify_content_snapshot(snapshot_update, tmp_path):
    proj = setup_golden_project(tmp_path, PROJECT_TYPE)
    result = _run(
        [sys.executable, str(_VERIFY_CONTENT), "--project-type", PROJECT_TYPE, "--docs", "docs"],
        proj,
    )
    assert result.returncode == 0, f"verify_content failed:\n{result.stdout}"
    assert_golden(f"golden_{PROJECT_TYPE}_verify_content.txt", normalize(result.stdout), snapshot_update)
