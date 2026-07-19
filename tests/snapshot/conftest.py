import contextlib
import re
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SNAPSHOTS_DIR = REPO_ROOT / "tests" / "snapshots"

_TIMESTAMP_RE = re.compile(r"Generated: \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")


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


@contextlib.contextmanager
def patched_project_type(project_type: str):
    """Temporarily set project_type in .project-starter.yml for subprocess tests."""
    yml_path = REPO_ROOT / ".project-starter.yml"
    original = yml_path.read_text(encoding="utf-8")
    yml_path.write_text(
        f"project_type: {project_type}\ntask_type:\ndocs_path: docs/\n",
        encoding="utf-8",
    )
    try:
        yield
    finally:
        yml_path.write_text(original, encoding="utf-8")
