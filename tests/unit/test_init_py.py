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
    "learning-log.md",
    "CLAUDE.md",
    ".project-starter.yml",
    ".gitignore",
]

_SKILL_DIRS = [
    "retrofit-existing-project",
    "code-quality-check",
    "module-completion-check",
    "sprint-doc-sync",
    "learning-checkpoint",
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


def test_init_py_copies_claude_skills(tmp_path):
    """adapters/claude/skills/ -> .claude/skills/ so Skills auto-trigger by description
    match out of the box, instead of requiring a separate manual copy step per README."""
    dest = tmp_path / "proj"
    result = _run_init(dest)
    assert result.returncode == 0, result.stderr

    skills_dest = dest / ".claude" / "skills"
    for skill_name in _SKILL_DIRS:
        skill_md = skills_dest / skill_name / "SKILL.md"
        assert skill_md.exists(), f"missing {skill_md} after init.py"
        text = skill_md.read_text(encoding="utf-8")
        assert text.startswith("---\n"), f"{skill_md} missing frontmatter"
        assert f"name: {skill_name}" in text
        assert "description:" in text

    # add-framework-adapter is framework-repo-only — must NOT be copied into user projects
    assert not (skills_dest / "add-framework-adapter").exists()


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


def test_init_py_writes_gitignore_covering_generated_paths(tmp_path):
    """Without this, a fresh project commits .ai/, __pycache__/, and logs/ by default —
    confirmed by actually running --init into an empty dir and checking git status."""
    dest = tmp_path / "proj"
    result = _run_init(dest)
    assert result.returncode == 0, result.stderr

    text = (dest / ".gitignore").read_text(encoding="utf-8")
    for entry in (".ai/", "__pycache__/", "*.pyc", "logs/"):
        assert entry in text, f"{entry!r} missing from generated .gitignore"


def test_init_py_appends_to_existing_gitignore_without_overwriting(tmp_path):
    """.gitignore commonly already exists (e.g. from `git init` with a language template)
    — unlike the other root files, it must never be silently overwritten."""
    dest = tmp_path / "proj"
    dest.mkdir()
    (dest / ".gitignore").write_text("node_modules/\n.env\n", encoding="utf-8")

    result = _run_init(dest)
    assert result.returncode == 0, result.stderr

    text = (dest / ".gitignore").read_text(encoding="utf-8")
    assert "node_modules/" in text
    assert ".env" in text
    assert ".ai/" in text


def test_init_py_does_not_duplicate_gitignore_block_on_second_run(tmp_path):
    dest = tmp_path / "proj"
    first = _run_init(dest)
    assert first.returncode == 0, first.stderr
    second = _run_init(dest)
    assert second.returncode == 0, second.stderr

    text = (dest / ".gitignore").read_text(encoding="utf-8")
    assert text.count(".ai/") == 1


def test_init_py_missing_args_exits_nonzero():
    result = subprocess.run(
        [sys.executable, str(INIT_PY)],
        cwd=str(REPO_ROOT), capture_output=True, text=True, encoding="utf-8",
    )
    assert result.returncode != 0
