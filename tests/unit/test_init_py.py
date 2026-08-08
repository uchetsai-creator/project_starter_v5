"""Coverage for init.py invoked directly (no bash) — the path a native Windows user
without Git Bash/WSL actually takes, since setup.sh itself is bash-only and cannot run
there at all. tests/unit/test_setup_sh_init.py proves setup.sh --init still works when a
POSIX bash is available (it delegates to init.py — see setup.sh); this file proves the
same outcomes hold with zero bash involved, which is the whole point of init.py existing.
"""
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
INIT_PY = REPO_ROOT / "init.py"

_REQUIRED_ROOT_FILES = [
    "AGENTS.md",
    "orchestrator.py",
    "build-context.py",
    "_workflow_utils.py",
    "workflow-registry.yaml",
    "document-registry.yaml",
    "detect_type.py",
    "debug-instrumentation-rules.md",
    "code-quality-check.md",
    "CLAUDE.md",
    ".project-starter.yml",
]


def _run_init(dest: Path, project_type: str = "web-app") -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(INIT_PY), project_type, str(dest)],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def test_init_py_copies_all_required_root_files(tmp_path):
    dest = tmp_path / "proj"
    result = _run_init(dest)
    assert result.returncode == 0, result.stderr

    missing = [name for name in _REQUIRED_ROOT_FILES if not (dest / name).exists()]
    assert not missing, f"init.py did not create: {missing}\nstdout: {result.stdout}"

    assert (dest / ".githooks" / "pre-commit").exists()
    assert (dest / "guidance").is_dir()
    assert (dest / "docs" / "script" / "validators").is_dir()


def test_init_py_writes_valid_project_type(tmp_path):
    dest = tmp_path / "proj"
    result = _run_init(dest, project_type="cli-tool")
    assert result.returncode == 0, result.stderr

    yml_text = (dest / ".project-starter.yml").read_text(encoding="utf-8")
    assert "project_type: cli-tool" in yml_text
    assert "[your-project-type]" not in yml_text


def test_init_py_rejects_unknown_type(tmp_path):
    dest = tmp_path / "proj"
    result = _run_init(dest, project_type="not-a-real-type")
    assert result.returncode != 0


def test_init_py_installs_pre_commit_hook_when_dest_is_a_git_repo(tmp_path):
    dest = tmp_path / "proj"
    dest.mkdir()
    (dest / ".git").mkdir()
    (dest / ".git" / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")

    result = _run_init(dest)
    assert result.returncode == 0, result.stderr
    assert (dest / ".git" / "hooks" / "pre-commit").exists()


def test_init_py_missing_args_exits_nonzero():
    result = subprocess.run(
        [sys.executable, str(INIT_PY)],
        cwd=str(REPO_ROOT), capture_output=True, text=True, encoding="utf-8",
    )
    assert result.returncode != 0
