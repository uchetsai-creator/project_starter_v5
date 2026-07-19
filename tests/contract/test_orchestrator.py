import re
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


# ---------------------------------------------------------------------------
# Regression guard — Phase 57: orchestrator.py missing `import re`
# ---------------------------------------------------------------------------

def test_orchestrator_imports_re():
    source = (_REPO_ROOT / "orchestrator.py").read_text(encoding="utf-8")
    assert re.search(r"(?m)^import re\b", source), "orchestrator.py is missing top-level `import re`"
