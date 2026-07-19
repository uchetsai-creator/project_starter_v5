import shutil
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

VALID_TYPES: list[str] = [
    "web-app", "cli-tool", "library",
    "data-pipeline", "ml-pipeline", "microservices", "llm-app", "iac", "mobile-app",
]

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
