#!/usr/bin/env python3
"""
init.py — Cross-platform implementation of `setup.sh --init` for project_starter_v5.

setup.sh --init is bash-only, so it doesn't run on native Windows without Git Bash/WSL —
this script is the single source of truth for the --init logic; setup.sh --init delegates
to it (see setup.sh) so both entry points stay in sync automatically instead of duplicating
the copy list by hand in two languages.

Usage:
  python3 init.py <type> <dest>

Valid types: web-app | cli-tool | library | data-pipeline | ml-pipeline
             microservices | llm-app | iac | mobile-app
"""

from __future__ import annotations

import shutil
import stat
import sys
from pathlib import Path

VALID_TYPES = [
    "web-app", "cli-tool", "library", "data-pipeline", "ml-pipeline",
    "microservices", "llm-app", "iac", "mobile-app",
]

# Kept in sync with setup.sh's `for f in ...` copy list by hand — same file this script
# replaces the logic of, not a separate independent list.
_ROOT_FILES = [
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
]

_PROJECT_STARTER_YML = """\
# project_starter — project configuration
# Do not rename this file.

project_type: {project_type}
# Valid values: web-app | cli-tool | library | data-pipeline | ml-pipeline
#               microservices | llm-app | iac | mobile-app

docs_path: docs/

task_type:
# Optional. Filters .ai/AI_CONTEXT.md to task-relevant documents.
# Valid values: feature | pipeline-stage | bug-fix | sprint-end | eval-run | iac-change

spec_code_adapter:
spec_code_spec:
spec_code_src:
# Optional — all three must be set together to enable the spec <-> code drift gate.
# See README.md -> Spec <-> Code Validator for the full list of adapter names.

test_command:
# Optional. Shell command that runs this project's test suite, e.g. `pytest -q` |
# `npm test` | `go test ./...`. When set, .githooks/pre-commit actually runs it on every
# commit and blocks if it exits non-zero. Leave blank to skip this gate.
"""


def init_project(project_type: str, dest: Path) -> None:
    if project_type not in VALID_TYPES:
        print(f"[FAIL] Unknown project type: {project_type}", file=sys.stderr)
        print(f"       Valid values: {' '.join(VALID_TYPES)}", file=sys.stderr)
        sys.exit(1)

    script_dir = Path(__file__).resolve().parent
    print(f"=== project_starter_v5 init: {project_type} -> {dest} ===\n")
    dest.mkdir(parents=True, exist_ok=True)

    for name in _ROOT_FILES:
        shutil.copy2(script_dir / name, dest / name)
        print(f"[OK] copied {name}")

    shutil.copytree(script_dir / ".githooks", dest / ".githooks", dirs_exist_ok=True)
    print("[OK] copied .githooks/")

    shutil.copytree(script_dir / "guidance", dest / "guidance", dirs_exist_ok=True)
    print("[OK] copied guidance/")

    # Claude Skills (static — SKILL.md per procedural doc) so they auto-trigger by
    # description match instead of requiring AGENTS.md to be read and followed by hand.
    # Previously an optional manual copy step (README -> Agent Adapters -> Claude Code);
    # copying it here means a fresh --init project gets working Skill-based enforcement
    # (e.g. learning-checkpoint) without a second, easy-to-miss setup step. Deliberately
    # NOT copying the framework repo's own .claude/skills/add-framework-adapter/ — that
    # one is for people extending project_starter_v5 itself, not for application code.
    shutil.copytree(
        script_dir / "adapters" / "claude" / "skills",
        dest / ".claude" / "skills",
        dirs_exist_ok=True,
    )
    print("[OK] copied adapters/claude/skills/ -> .claude/skills/")

    # CLAUDE.md is Claude Code's auto-loaded context file — importing AGENTS.md here
    # guarantees its rules (including Learning Checkpoint) load at the start of every
    # session, with no dependency on which task-specific docs current-state.md points to.
    claude_md = dest / "CLAUDE.md"
    if not claude_md.exists():
        claude_md.write_text("@AGENTS.md\n", encoding="utf-8")
        print("[OK] wrote CLAUDE.md (@AGENTS.md)")

    docs_script = dest / "docs" / "script"
    docs_script.mkdir(parents=True, exist_ok=True)
    shutil.copytree(script_dir / "templates" / "script", docs_script, dirs_exist_ok=True)
    print("[OK] copied templates/script/ -> docs/script/")

    (dest / ".project-starter.yml").write_text(
        _PROJECT_STARTER_YML.format(project_type=project_type), encoding="utf-8",
    )
    print(f"[OK] wrote .project-starter.yml (project_type: {project_type})")

    # Install pre-commit hook — only if a real git repo exists (HEAD file is the marker)
    git_head = dest / ".git" / "HEAD"
    if git_head.exists():
        git_hooks = dest / ".git" / "hooks"
        git_hooks.mkdir(parents=True, exist_ok=True)
        hook_src = dest / ".githooks" / "pre-commit"
        hook_dst = git_hooks / "pre-commit"
        shutil.copy2(hook_src, hook_dst)
        try:
            hook_dst.chmod(hook_dst.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)
        except OSError:
            pass  # chmod bits are meaningless on some filesystems (e.g. certain Windows setups)
        print("[OK] pre-commit hook installed")
    else:
        print(f"[WARN] {dest} is not a git repository — run git init first, then:")
        print("       cp .githooks/pre-commit .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit")

    print("\nNext steps:")
    print(f"  cd {dest}")
    print("  python3 orchestrator.py --adapter claude   # generate .ai/WORKFLOW.md + start-task.md")
    print(f"  Open templates/init/{project_type}.md and follow its numbered steps.")


def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[union-attr]  # guard above only narrows sys.stdout

    if len(sys.argv) != 3:
        print("Usage: python3 init.py <type> <dest>", file=sys.stderr)
        print(f"  type: {' '.join(VALID_TYPES)}", file=sys.stderr)
        print("  dest: target project directory (will be created if absent)", file=sys.stderr)
        sys.exit(1)

    init_project(sys.argv[1], Path(sys.argv[2]))


if __name__ == "__main__":
    main()
