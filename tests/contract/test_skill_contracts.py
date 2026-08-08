"""Guards against Claude Skill SKILL.md bodies drifting from the framework's canonical
source docs (the human-edited copies), same purpose as test_agent_adapter_templates.py
but for adapters/claude/skills/ and .claude/skills/ instead of adapters/claude/*.md."""
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

# (SKILL.md path, canonical source file it must stay byte-identical to, after frontmatter)
_SKILL_SOURCES = {
    REPO_ROOT / "adapters/claude/skills/retrofit-existing-project/SKILL.md":
        REPO_ROOT / "templates/init/retrofit.md",
    REPO_ROOT / "adapters/claude/skills/code-quality-check/SKILL.md":
        REPO_ROOT / "code-quality-check.md",
    REPO_ROOT / "adapters/claude/skills/module-completion-check/SKILL.md":
        REPO_ROOT / "templates/module-completion.md",
    REPO_ROOT / "adapters/claude/skills/sprint-doc-sync/SKILL.md":
        REPO_ROOT / "templates/sprint-sync.md",
    REPO_ROOT / "adapters/claude/skills/learning-checkpoint/SKILL.md":
        REPO_ROOT / "guidance/learning-checkpoints/common.md",
    REPO_ROOT / ".claude/skills/add-framework-adapter/SKILL.md":
        REPO_ROOT / "docs/contributing-adapters.md",
}

_FRONTMATTER_RE = re.compile(r"\A---\n.*?\n---\n\n(.*)\Z", re.DOTALL)


def _split_frontmatter(skill_md_text):
    match = _FRONTMATTER_RE.match(skill_md_text)
    assert match, "SKILL.md must start with a --- frontmatter block followed by a blank line"
    return match.group(1)


def test_all_skill_sources_exist():
    for skill_path, source_path in _SKILL_SOURCES.items():
        assert skill_path.exists(), f"missing {skill_path}"
        assert source_path.exists(), f"missing source {source_path} referenced by {skill_path}"


def test_skill_frontmatter_has_name_and_description():
    for skill_path in _SKILL_SOURCES:
        text = skill_path.read_text(encoding="utf-8")
        frontmatter_match = re.match(r"\A---\n(.*?)\n---\n", text, re.DOTALL)
        assert frontmatter_match, f"{skill_path} missing frontmatter block"
        frontmatter = frontmatter_match.group(1)
        assert re.search(r"^name:\s*\S+", frontmatter, re.MULTILINE), f"{skill_path} frontmatter missing name"
        assert re.search(r"^description:\s*\S+", frontmatter, re.MULTILINE), f"{skill_path} frontmatter missing description"


def test_skill_bodies_match_source_docs():
    mismatches = []
    for skill_path, source_path in _SKILL_SOURCES.items():
        body = _split_frontmatter(skill_path.read_text(encoding="utf-8"))
        source_text = source_path.read_text(encoding="utf-8")
        if body != source_text:
            mismatches.append(f"{skill_path.relative_to(REPO_ROOT)} != {source_path.relative_to(REPO_ROOT)}")
    assert not mismatches, (
        f"SKILL.md body drifted from its canonical source doc: {mismatches}. "
        "Update the SKILL.md body (after the frontmatter) to match the source file exactly."
    )
