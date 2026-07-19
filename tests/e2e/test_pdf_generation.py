"""PDF generation smoke test — skipped when plantuml.jar is absent."""
import subprocess
import sys
from pathlib import Path

import pytest

from tests.conftest import REPO_ROOT, setup_fixture

_BUILD_PDF = REPO_ROOT / "templates/script/generators/build_pdf.py"
_PLANTUML_JAR = Path.home() / "plantuml.jar"

_plantuml_missing = not _PLANTUML_JAR.exists() and not any(
    Path(p) / "plantuml.jar"
    for p in ["/usr/local/bin", "/usr/bin", str(Path.home())]
    if (Path(p) / "plantuml.jar").exists()
)


@pytest.mark.skipif(_plantuml_missing, reason="plantuml.jar not found")
def test_pdf_generation_web_app(tmp_path):
    setup_fixture(tmp_path, project_type="web-app", task_type="feature")

    result = subprocess.run(
        [sys.executable, str(_BUILD_PDF), "--project-type", "web-app", "--docs", "docs"],
        cwd=str(tmp_path),
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, f"build_pdf.py failed:\n{result.stderr}\n{result.stdout}"

    pdfs = list(tmp_path.rglob("*.pdf"))
    assert pdfs, "No PDF file produced by build_pdf.py"
    assert pdfs[0].stat().st_size > 0, f"PDF is empty: {pdfs[0]}"
