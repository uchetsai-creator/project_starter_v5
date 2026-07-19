import subprocess
import sys
from pathlib import Path

import pytest

from tests.conftest import VALID_TYPES
from tests.snapshot.conftest import REPO_ROOT, assert_snapshot

_VERIFY_DOCS = REPO_ROOT / "templates/script/validators/verify_docs.py"
_FIXTURES = REPO_ROOT / "tests/fixtures"


@pytest.mark.parametrize("project_type", VALID_TYPES)
def test_verify_docs_json_snapshot(project_type, snapshot_update):
    docs_dir = _FIXTURES / project_type / "docs"
    result = subprocess.run(
        [
            sys.executable, str(_VERIFY_DOCS),
            "--project-type", project_type,
            "--docs", str(docs_dir),
            "--json",
        ],
        capture_output=True,
        text=True,
        cwd=str(REPO_ROOT),
    )
    assert result.returncode == 0, f"verify_docs.py failed:\n{result.stderr}"
    assert_snapshot(
        f"verify_docs__{project_type}.json",
        result.stdout,
        snapshot_update,
    )
