"""End-to-end coverage for setup.sh --init — the first command in the README Quick Start,
previously exercised only by hand (no automated test invoked setup.sh at all).

Also closes the loop on two prior gaps fixed this session:
- setup.sh's copy list used to omit code-quality-check.md / debug-instrumentation-rules.md
  despite README's own documented new_project/ file tree listing both as root files.
- adapters/claude/skills/ (Claude Skills) used to be an optional, easy-to-miss manual copy
  step (README → Agent Adapters → Claude Code); init.py now copies it automatically as part
  of --init, so a fresh project gets working Skill-based enforcement (e.g.
  learning-checkpoint) without a second setup step.
"""
import subprocess
from pathlib import Path

import pytest

from tests.conftest import find_posix_bash

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SETUP_SH = REPO_ROOT / "setup.sh"

_BASH = find_posix_bash()
pytestmark = pytest.mark.skipif(_BASH is None, reason="bash not found on PATH")

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
]

_SKILL_DIRS = [
    "retrofit-existing-project",
    "code-quality-check",
    "module-completion-check",
    "sprint-doc-sync",
    "learning-checkpoint",
    "task-closeout",
    "research-decision-log",
]


def _run_init(dest: Path, project_type: str = "web-app") -> subprocess.CompletedProcess:
    assert _BASH is not None  # module-level skipif guarantees this by the time we get here
    return subprocess.run(
        [_BASH, str(SETUP_SH), "--init", project_type, str(dest)],
        cwd=str(REPO_ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
    )


def test_setup_sh_init_copies_all_required_root_files(tmp_path):
    dest = tmp_path / "proj"
    result = _run_init(dest)
    assert result.returncode == 0, result.stderr

    missing = [name for name in _REQUIRED_ROOT_FILES if not (dest / name).exists()]
    assert not missing, f"setup.sh --init did not create: {missing}\nstdout: {result.stdout}"

    assert (dest / ".githooks" / "pre-commit").exists()
    assert (dest / "guidance").is_dir()
    assert (dest / "docs" / "script" / "validators").is_dir()


def test_setup_sh_init_writes_valid_project_type(tmp_path):
    dest = tmp_path / "proj"
    result = _run_init(dest, project_type="cli-tool")
    assert result.returncode == 0, result.stderr

    yml_text = (dest / ".project-starter.yml").read_text(encoding="utf-8")
    assert "project_type: cli-tool" in yml_text
    assert "[your-project-type]" not in yml_text


def test_setup_sh_init_rejects_unknown_type(tmp_path):
    dest = tmp_path / "proj"
    result = _run_init(dest, project_type="not-a-real-type")
    assert result.returncode != 0


def test_setup_sh_init_copies_claude_skills(tmp_path):
    """adapters/claude/skills/ -> .claude/skills/ now happens automatically as part of
    --init (see init.py) — no separate manual copy step required."""
    dest = tmp_path / "proj"
    result = _run_init(dest)
    assert result.returncode == 0, result.stderr

    skills_dest = dest / ".claude" / "skills"
    for skill_name in _SKILL_DIRS:
        skill_md = skills_dest / skill_name / "SKILL.md"
        assert skill_md.exists(), f"missing {skill_md} after setup.sh --init"
        text = skill_md.read_text(encoding="utf-8")
        assert text.startswith("---\n"), f"{skill_md} missing frontmatter"
        assert f"name: {skill_name}" in text
        assert "description:" in text

    # add-framework-adapter is framework-repo-only — must NOT be copied into user projects
    assert not (skills_dest / "add-framework-adapter").exists()
