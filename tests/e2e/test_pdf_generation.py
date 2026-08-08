"""PDF generation smoke test — skipped when plantuml.jar is absent."""
import os
import subprocess
import sys
from pathlib import Path

import pytest

from tests.conftest import REPO_ROOT, setup_fixture

_BUILD_PDF = REPO_ROOT / "templates/script/generators/build_pdf.py"
_PLANTUML_JAR = Path.home() / "plantuml.jar"

_plantuml_missing = not any(
    p.exists()
    for p in [
        _PLANTUML_JAR,
        Path("/usr/local/bin/plantuml.jar"),
        Path("/usr/bin/plantuml.jar"),
    ]
)


@pytest.mark.skipif(_plantuml_missing, reason="plantuml.jar not found")
def test_pdf_generation_web_app(tmp_path):
    setup_fixture(tmp_path, project_type="web-app", task_type="feature")

    # PYTHONUTF8 forces the child's own stdout/stderr encoding to UTF-8, matching the
    # encoding="utf-8" this decodes with — see golden test helpers for the full rationale.
    result = subprocess.run(
        [sys.executable, str(_BUILD_PDF), "--project-type", "web-app", "--docs", "docs"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
        encoding="utf-8",
        env={**os.environ, "PYTHONUTF8": "1"},
    )
    assert result.returncode == 0, f"build_pdf.py failed:\n{result.stderr}\n{result.stdout}"

    pdfs = list(tmp_path.rglob("*.pdf"))
    assert pdfs, "No PDF file produced by build_pdf.py"
    assert pdfs[0].stat().st_size > 0, f"PDF is empty: {pdfs[0]}"
