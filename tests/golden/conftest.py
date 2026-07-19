import re
import shutil
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
GOLDEN_SNAPSHOTS_DIR = REPO_ROOT / "tests" / "golden" / "snapshots"

_TIMESTAMP_RE = re.compile(r"Generated: \d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")

_FRAMEWORK_FILES = [
    "orchestrator.py",
    "build-context.py",
    "_workflow_utils.py",
    "document-registry.yaml",
    "workflow-registry.yaml",
]


@pytest.fixture
def snapshot_update(request):
    return request.config.getoption("--snapshot-update", default=False)


def normalize(text: str) -> str:
    return _TIMESTAMP_RE.sub("Generated: {{TIMESTAMP}}", text)


def assert_golden(name: str, actual: str, update: bool) -> None:
    path = GOLDEN_SNAPSHOTS_DIR / name
    if update or not path.exists():
        GOLDEN_SNAPSHOTS_DIR.mkdir(parents=True, exist_ok=True)
        path.write_text(actual, encoding="utf-8")
        return
    expected = path.read_text(encoding="utf-8")
    assert actual == expected, (
        f"Golden snapshot mismatch: {name}\n"
        f"Re-run with --snapshot-update to accept new output."
    )


def setup_golden_project(tmp_path: Path, project_type: str) -> Path:
    example_docs = REPO_ROOT / "examples" / project_type / "docs"
    dst_docs = tmp_path / "docs"
    shutil.copytree(str(example_docs), str(dst_docs))

    shutil.copytree(
        str(REPO_ROOT / "templates/script/validators"),
        str(tmp_path / "docs/script/validators"),
    )

    for name in _FRAMEWORK_FILES:
        shutil.copy2(str(REPO_ROOT / name), str(tmp_path / name))

    shutil.copy2(
        str(REPO_ROOT / "examples" / project_type / ".project-starter.yml"),
        str(tmp_path / ".project-starter.yml"),
    )

    return tmp_path
