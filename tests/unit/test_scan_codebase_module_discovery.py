"""Module discovery in scan_codebase.py: nested starter copies are not product modules,
and --files treats each top-level Python file as one module (one router per feature).
"""
import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SCAN_SCRIPT = REPO_ROOT / "templates/script/scanners/scan_codebase.py"


def _scan_names(src: Path, *extra: str) -> list[str]:
    result = subprocess.run(
        [sys.executable, str(SCAN_SCRIPT), str(src),
         "--project-type", "web-app", "--format", "json", "--docs", str(src.parent / "docs"),
         *extra],
        capture_output=True, text=True, timeout=30, encoding="utf-8",
    )
    assert result.returncode == 0, result.stderr
    return [m["name"] for m in json.loads(result.stdout)["modules"]]


def test_nested_starter_copy_is_skipped(tmp_path):
    root = tmp_path / "product"
    (root / "backend" / "app").mkdir(parents=True)
    (root / "vendored_starter").mkdir()
    (root / "vendored_starter" / ".project-starter.yml").write_text("project_type: web-app\n")
    (root / "vendored_starter" / "scripts").mkdir()

    names = _scan_names(root)

    assert "backend" in names
    assert "vendored_starter" not in names


def test_files_mode_lists_one_module_per_python_file(tmp_path):
    api = tmp_path / "api" / "v1"
    api.mkdir(parents=True)
    for name in ("auth.py", "nudd.py", "__init__.py", "_helpers.py"):
        (api / name).write_text("")
    (api / "notes.txt").write_text("")
    (api / "sub").mkdir()

    names = _scan_names(api, "--files")

    assert sorted(names) == ["auth", "nudd"]
