"""End-to-end coverage for setup.sh --init — the first command in the README Quick Start,
previously exercised only by hand (no automated test invoked setup.sh at all).

Also closes the loop on two prior gaps fixed this session:
- setup.sh's copy list used to omit code-quality-check.md / debug-instrumentation-rules.md
  despite README's own documented new_project/ file tree listing both as root files.
- adapters/claude/skills/ (Claude Skills) is documented as an optional post-init copy step in
  README → Agent Adapters → Claude Code, but nothing proved that copy actually produces a
  usable .claude/skills/ layout once combined with a real setup.sh --init project.
"""
import shutil
import subprocess

import pytest

from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
SETUP_SH = REPO_ROOT / "setup.sh"

_BASH = shutil.which("bash")
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
    "CLAUDE.md",
    ".project-starter.yml",
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
        ["bash", str(SETUP_SH), "--init", project_type, str(dest)],
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


def test_setup_sh_init_then_claude_skills_copy_produces_usable_layout(tmp_path):
    """Simulates README → Agent Adapters → Claude Code step 4: copying
    adapters/claude/skills/ into a project that already went through --init."""
    dest = tmp_path / "proj"
    result = _run_init(dest)
    assert result.returncode == 0, result.stderr

    skills_dest = dest / ".claude" / "skills"
    shutil.copytree(REPO_ROOT / "adapters" / "claude" / "skills", skills_dest)

    for skill_name in _SKILL_DIRS:
        skill_md = skills_dest / skill_name / "SKILL.md"
        assert skill_md.exists(), f"missing {skill_md} after copying adapters/claude/skills/"
        text = skill_md.read_text(encoding="utf-8")
        assert text.startswith("---\n"), f"{skill_md} missing frontmatter"
        assert f"name: {skill_name}" in text
        assert "description:" in text
