import os
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


def find_posix_bash() -> str | None:
    """Locate a real POSIX bash (Git Bash / MSYS2), not
    C:\\Windows\\System32\\bash.exe — the WSL launcher stub GitHub's windows-latest
    runner PATH resolves "bash" to first. When WSL has no distro installed, that stub
    ignores every argument, prints "Use 'wsl.exe --install <Distro>' to install." to
    stdout, and exits 1 — for ANY command, not just a missing one. A caller checking
    only the exit code sees an ordinary-looking non-zero failure with no obvious
    connection to WSL; confirmed by reproducing this exact failure in CI (see
    CHANGELOG.md) and decoding the UTF-16 byte fragment left in the pytest assertion
    diff back to that message."""
    if os.name != "nt":
        return shutil.which("bash")
    for env_var in ("ProgramFiles", "ProgramFiles(x86)"):
        base = os.environ.get(env_var)
        if base:
            candidate = Path(base) / "Git" / "bin" / "bash.exe"
            if candidate.exists():
                return str(candidate)
    # Fall back to scanning PATH for any bash.exe that isn't the System32 stub.
    for directory in os.environ.get("PATH", "").split(os.pathsep):
        candidate = Path(directory) / "bash.exe"
        if candidate.exists() and "system32" not in str(candidate).lower():
            return str(candidate)
    return shutil.which("bash")


def pytest_addoption(parser):
    parser.addoption(
        "--snapshot-update",
        action="store_true",
        default=False,
        help="Regenerate snapshot golden files",
    )

sys.path.insert(0, str(REPO_ROOT / "templates/script/validators"))
from _registry import VALID_TYPES  # noqa: E402,F401 -- re-exported for `from tests.conftest import VALID_TYPES`

# Framework files that must be copied into an E2E project root
_PROJECT_FILES = [
    "orchestrator.py",
    "build-context.py",
    "_workflow_utils.py",
    "document-registry.yaml",
    "workflow-registry.yaml",
]


def setup_fixture(
    tmp_path: Path,
    project_type: str,
    task_type: str | None = None,
) -> Path:
    """Create a self-contained project fixture in tmp_path for E2E tests.

    Copies filled fixture docs, framework scripts, and validators so that
    orchestrator.py / build-context.py / verify_docs.py all work from tmp_path.

    Returns the docs path (tmp_path / "docs").
    """
    # 1. Copy filled fixture docs
    src_docs = REPO_ROOT / "tests" / "fixtures" / project_type / "docs"
    dst_docs = tmp_path / "docs"
    if src_docs.exists():
        shutil.copytree(src_docs, dst_docs)
    else:
        dst_docs.mkdir(parents=True)

    # 2. Copy validators to docs/script/validators/ (matches workflow-registry paths)
    shutil.copytree(
        REPO_ROOT / "templates/script/validators",
        tmp_path / "docs/script/validators",
    )

    # 3. Copy top-level framework scripts and config to tmp_path
    for name in _PROJECT_FILES:
        shutil.copy2(REPO_ROOT / name, tmp_path / name)

    # 4. Write .project-starter.yml
    (tmp_path / ".project-starter.yml").write_text(
        f"project_type: {project_type}\n"
        f"task_type: {task_type or ''}\n"
        "docs_path: docs/\n",
        encoding="utf-8",
    )

    # 5. Write docs/current-state.md so orchestrator can read the task name
    (dst_docs / "current-state.md").write_text(
        f"# Current State\n\n**Task Type:** {task_type or ''}\n**Task:** E2E fixture task\n",
        encoding="utf-8",
    )

    return dst_docs
