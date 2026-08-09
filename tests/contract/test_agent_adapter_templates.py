"""Guards against orchestrator.py's embedded _ADAPTER_TEMPLATES drifting from the
framework's adapters/<tool>/ source files (the human-edited copies)."""
import importlib.util
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

spec = importlib.util.spec_from_file_location("orchestrator", REPO_ROOT / "orchestrator.py")
assert spec is not None and spec.loader is not None
orchestrator = importlib.util.module_from_spec(spec)
sys.modules.setdefault("orchestrator", orchestrator)
spec.loader.exec_module(orchestrator)

_SOURCE_FILES = {
    ("claude", "start-task.md"): REPO_ROOT / "adapters/claude/start-task.md",
    ("codex", "setup.md"): REPO_ROOT / "adapters/codex/setup.md",
    ("codex", "task-instructions.md"): REPO_ROOT / "adapters/codex/task-instructions.md",
}


def test_all_adapter_source_files_are_embedded():
    embedded_keys = {
        (adapter, filename)
        for adapter, files in orchestrator._ADAPTER_TEMPLATES.items()
        for filename in files
    }
    assert embedded_keys == set(_SOURCE_FILES.keys())


def test_embedded_templates_match_source_files():
    mismatches = []
    for (adapter, filename), source_path in _SOURCE_FILES.items():
        embedded = orchestrator._ADAPTER_TEMPLATES[adapter][filename]
        on_disk = source_path.read_text(encoding="utf-8")
        if embedded != on_disk:
            mismatches.append(f"{adapter}/{filename}")
    assert not mismatches, (
        f"orchestrator.py _ADAPTER_TEMPLATES drifted from adapters/ source files: {mismatches}. "
        "Update _ADAPTER_TEMPLATES in orchestrator.py to match."
    )
