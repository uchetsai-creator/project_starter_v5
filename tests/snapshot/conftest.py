import re
import shutil
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SNAPSHOTS_DIR = REPO_ROOT / "tests" / "snapshots"

_TIMESTAMP_RE = re.compile(r"Generated: \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")

_ORCHESTRATOR_FILES = ["orchestrator.py", "_workflow_utils.py", "workflow-registry.yaml"]
_BUILD_CONTEXT_FILES = ["build-context.py", "_workflow_utils.py", "document-registry.yaml"]


def pytest_addoption(parser):
    parser.addoption(
        "--snapshot-update",
        action="store_true",
        default=False,
        help="Regenerate snapshot golden files",
    )


@pytest.fixture
def snapshot_update(request):
    return request.config.getoption("--snapshot-update")


def normalize(text: str) -> str:
    """Replace volatile timestamps so snapshots are stable across runs."""
    return _TIMESTAMP_RE.sub("Generated: {{TIMESTAMP}}", text)


def assert_snapshot(name: str, actual: str, update: bool) -> None:
    """Compare actual to stored golden file, or write it when update=True."""
    path = SNAPSHOTS_DIR / name
    if update or not path.exists():
        SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        path.write_text(actual, encoding="utf-8")
        return
    expected = path.read_text(encoding="utf-8")
    assert actual == expected, (
        f"Snapshot mismatch: {name}\n"
        f"Re-run with --snapshot-update to accept new output."
    )


def setup_snapshot_project(
    tmp_path: Path,
    project_type: str,
    extra_files: list[str] | None = None,
) -> Path:
    """Copy framework scripts into tmp_path and write .project-starter.yml.

    Each test gets its own isolated directory so parallel workers (pytest -n auto)
    never clobber each other's .project-starter.yml.
    """
    for name in dict.fromkeys(_ORCHESTRATOR_FILES + (extra_files or [])):
        src = REPO_ROOT / name
        if src.exists():
            shutil.copy2(src, tmp_path / name)
    (tmp_path / ".project-starter.yml").write_text(
        f"project_type: {project_type}\ntask_type:\ndocs_path: docs/\n",
        encoding="utf-8",
    )
    return tmp_path
