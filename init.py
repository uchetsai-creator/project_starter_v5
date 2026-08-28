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

# Marks the appended block below so re-running --init (or a project that already has this
# block from a prior --init) doesn't duplicate it.
_GITIGNORE_MARKER = "# --- project_starter_v5: generated/runtime paths ---"
_GITIGNORE_BLOCK = f"""
{_GITIGNORE_MARKER}
.ai/
__pycache__/
*.pyc
.pytest_cache/
logs/
"""

_PROJECT_STARTER_YML = """\
# project_starter — project configuration
# Do not rename this file.

project_type: {project_type}
# Valid values: web-app | cli-tool | library | data-pipeline | ml-pipeline
#               microservices | llm-app | iac | mobile-app

docs_path: docs/

doc_profile: full
# Optional. `lite` downgrades permissions.md, business-*.md, backend/database/deployment.md,
# research.md, and test-plan/test-report.md from Required to Optional -- for a solo/small
# project that doesn't need the full stakeholder-facing document set yet. Core contracts
# (project-requirements.md, quickstart.md, data-model.md, api-contract.md, architecture.md,
# logging-spec.md) stay Required either way. See guidance/doc-profile.md for when to switch.

task_type:
# Optional. Filters .ai/AI_CONTEXT.md to task-relevant documents.
# Valid values: feature | pipeline-stage | bug-fix | sprint-end | eval-run | iac-change

spec_code_adapter:
spec_code_spec:
spec_code_src:
# Optional — all three must be set together to enable the spec <-> code drift gate.
# See README.md -> Spec <-> Code Validator for the full list of adapter names.
# More than one contract to validate (e.g. a REST API plus a background pipeline)?
# Use spec_code_bindings instead — see README.md -> Spec <-> Code Validator.

spec_code_bindings:
# Optional — a list of adapter/spec/src mappings, for more than one contract in
# the same project. Mutually exclusive with the single trio above (this list wins if
# both are set). See README.md -> Spec <-> Code Validator for the example format.

test_command:
# Optional. Shell command that runs this project's test suite, e.g. `pytest -q` |
# `npm test` | `go test ./...`. When set, .githooks/pre-commit actually runs it on every
# commit and blocks if it exits non-zero. Leave blank to skip this gate.

sprint_sync_stale_days:
# Optional. Age-based fallback for the Sprint Documentation Sync guard: that guard's
# main trigger is a count (3 Pending entries in docs/sprint-change-log.md), which a
# low-volume/solo project may never reach. When set, a commit is also blocked once the
# oldest Pending entry's **Date:** field is at least this many days old. Leave blank to
# skip this fallback (default). Example: sprint_sync_stale_days: 14

checkpoint_enforcement:
# Optional (unset | session-prompt | off). Controls how strictly
# adapters/claude/pretooluse_scope_guard.py enforces the Learning Checkpoint scoping
# rule. unset (default) = always enforces, no prompt. `session-prompt` = ask once per
# Claude Code session (session-start-hook.sh) whether to turn the guard on for that
# session; unanswered sessions fail open. `off` = always allow. See README.md ->
# Learning Checkpoint enforcement and pretooluse_scope_guard.py's docstring.
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

    # .gitignore: without this, a fresh project commits .ai/ (generated, meant to be
    # gitignored per README), __pycache__/, and logs/ by default — confirmed by actually
    # running --init into an empty directory and checking `git status` before this fix.
    # Never overwrite an existing .gitignore (unlike the _ROOT_FILES loop above, this file
    # commonly already exists — e.g. from `git init` with a language template); append the
    # generated/runtime block instead, and only once (guarded by _GITIGNORE_MARKER) so
    # re-running --init on the same project doesn't duplicate it.
    gitignore = dest / ".gitignore"
    if not gitignore.exists():
        gitignore.write_text(_GITIGNORE_BLOCK.lstrip("\n"), encoding="utf-8")
        print("[OK] wrote .gitignore")
    elif _GITIGNORE_MARKER not in gitignore.read_text(encoding="utf-8"):
        with gitignore.open("a", encoding="utf-8") as f:
            f.write(_GITIGNORE_BLOCK)
        print("[OK] appended generated/runtime paths to existing .gitignore")

    # framework/ is excluded — README documents its contents (verify_framework.py,
    # mcp_tools.py) as "framework-internal only, NOT copied to user projects", but nothing
    # actually enforced that until now: shutil.copytree() with no ignore= copies everything
    # under templates/script/ unconditionally. Confirmed by actually running --init into a
    # fresh directory and checking for docs/script/framework/ before this fix — it was there.
    docs_script = dest / "docs" / "script"
    docs_script.mkdir(parents=True, exist_ok=True)
    shutil.copytree(
        script_dir / "templates" / "script", docs_script, dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("framework"),
    )
    print("[OK] copied templates/script/ -> docs/script/ (excluding framework-internal-only files)")

    # templates/ (everything except templates/script/, already placed under docs/script/
    # above) holds the init guides (templates/init/<type>.md) and skeleton docs
    # (templates/specs/*.md, templates/architecture/*.md, etc.) that AGENTS.md's own
    # "Project Initialization" step and each templates/init/<type>.md instruct the agent
    # to read/copy from during setup (e.g. "Create docs/specs/quickstart.md from
    # templates/specs/quickstart.md"). Without this, a freshly scaffolded project's first
    # required step — reading templates/init/<type>.md — fails immediately: confirmed by
    # actually running --init into a fresh directory and checking for
    # templates/init/cli-tool.md (and the files it in turn references) before this fix —
    # none of them were there.
    shutil.copytree(
        script_dir / "templates", dest / "templates", dirs_exist_ok=True,
        ignore=shutil.ignore_patterns("script"),
    )
    print("[OK] copied templates/ -> templates/ (excluding templates/script/, handled separately above)")

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
