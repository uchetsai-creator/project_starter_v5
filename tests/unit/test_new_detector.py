import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
NEW_DETECTOR = REPO_ROOT / "templates" / "script" / "generators" / "new_detector.py"


def _setup_project(tmp_path: Path) -> Path:
    """Copy just what new_detector.py needs (itself, verify_spec_code.py, and one
    capability file) into an isolated tmp_path, preserving the relative layout the
    tool expects (script/generators/ + script/validators/_spec_code_adapters/)."""
    gen_dir = tmp_path / "templates" / "script" / "generators"
    val_dir = tmp_path / "templates" / "script" / "validators"
    adapters_dir = val_dir / "_spec_code_adapters"
    gen_dir.mkdir(parents=True)
    adapters_dir.mkdir(parents=True)

    shutil.copy(NEW_DETECTOR, gen_dir / "new_detector.py")
    shutil.copy(
        REPO_ROOT / "templates" / "script" / "validators" / "verify_spec_code.py",
        val_dir / "verify_spec_code.py",
    )
    shutil.copy(
        REPO_ROOT / "templates" / "script" / "validators" / "_spec_code_adapters" / "_capability_web_api.py",
        adapters_dir / "_capability_web_api.py",
    )
    return tmp_path


def _run(tmp_path: Path, *args: str) -> subprocess.CompletedProcess:
    script = tmp_path / "templates" / "script" / "generators" / "new_detector.py"
    return subprocess.run(
        [sys.executable, str(script), *args],
        capture_output=True, text=True, cwd=str(tmp_path),
    )


def test_list_capabilities_shows_all_seven(tmp_path):
    proj = _setup_project(tmp_path)
    result = _run(proj, "--list-capabilities")
    assert result.returncode == 0
    for key in ("web-api", "cli", "data-pipeline", "library", "llm-app", "iac", "mobile"):
        assert key in result.stdout


def test_missing_required_args_errors(tmp_path):
    proj = _setup_project(tmp_path)
    result = _run(proj, "--capability", "web-api")
    assert result.returncode != 0
    assert "--name" in result.stderr


def test_dry_run_does_not_write_files(tmp_path):
    proj = _setup_project(tmp_path)
    detector_path = proj / "templates/script/validators/_spec_code_adapters/django.py"
    capability_path = proj / "templates/script/validators/_spec_code_adapters/_capability_web_api.py"
    before = capability_path.read_text(encoding="utf-8")

    result = _run(proj, "--capability", "web-api", "--name", "django", "--dry-run")

    assert result.returncode == 0
    assert not detector_path.exists()
    assert capability_path.read_text(encoding="utf-8") == before
    assert "would write" in result.stdout


def test_scaffold_creates_valid_detector_and_registers_it(tmp_path):
    proj = _setup_project(tmp_path)
    detector_path = proj / "templates/script/validators/_spec_code_adapters/django.py"
    capability_path = proj / "templates/script/validators/_spec_code_adapters/_capability_web_api.py"

    result = _run(proj, "--capability", "web-api", "--name", "django")

    assert result.returncode == 0, result.stderr
    assert detector_path.exists()

    content = detector_path.read_text(encoding="utf-8")
    assert "class DjangoDetector(Detector):" in content
    assert "NormalizedEndpoint" in content
    assert "[OK] django.py self-test passed" in content

    # Generated file must be syntactically valid Python.
    compile(content, str(detector_path), "exec")

    registry_text = capability_path.read_text(encoding="utf-8")
    assert "'django': ('django', 'DjangoDetector', ('.py',))," in registry_text
    compile(registry_text, str(capability_path), "exec")


def test_scaffold_with_alias_registers_in_verify_spec_code(tmp_path):
    proj = _setup_project(tmp_path)
    verify_spec_code_path = proj / "templates/script/validators/verify_spec_code.py"

    result = _run(proj, "--capability", "web-api", "--name", "django", "--alias")

    assert result.returncode == 0, result.stderr
    registry_text = verify_spec_code_path.read_text(encoding="utf-8")
    assert "'django': ('_capability_web_api', 'WebAPIAdapter', 'django')," in registry_text
    compile(registry_text, str(verify_spec_code_path), "exec")


def test_duplicate_name_errors_without_overwriting(tmp_path):
    proj = _setup_project(tmp_path)
    _run(proj, "--capability", "web-api", "--name", "django")
    result = _run(proj, "--capability", "web-api", "--name", "django")
    assert result.returncode != 0
    assert "already" in result.stderr


def test_existing_framework_name_conflicts(tmp_path):
    proj = _setup_project(tmp_path)
    result = _run(proj, "--capability", "web-api", "--name", "fastapi")
    assert result.returncode != 0
    assert "already" in result.stderr


@pytest.mark.parametrize("bad_name", ["my-framework", "123abc", "my framework"])
def test_invalid_name_rejected(tmp_path, bad_name):
    proj = _setup_project(tmp_path)
    result = _run(proj, "--capability", "web-api", "--name", bad_name)
    assert result.returncode != 0


def test_mixed_case_name_is_lowercased(tmp_path):
    proj = _setup_project(tmp_path)
    result = _run(proj, "--capability", "web-api", "--name", "Django")
    assert result.returncode == 0, result.stderr
    detector_path = proj / "templates/script/validators/_spec_code_adapters/django.py"
    assert detector_path.exists()
