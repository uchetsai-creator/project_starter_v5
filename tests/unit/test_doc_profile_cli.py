"""CLI-level tests for verify_docs.py's doc_profile (lite/full) support -- the actual
entry point pre-commit and orchestrator.py invoke, on top of the _registry.py unit tests
in test_registry.py. Confirms .project-starter.yml -> doc_profile is read automatically
(no flag needed, matching how pre-commit calls this script today) and that --lite/--full
correctly override it.
"""
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
VERIFY_DOCS = REPO_ROOT / "templates" / "script" / "validators" / "verify_docs.py"
VERIFY_CONTENT = REPO_ROOT / "templates" / "script" / "validators" / "verify_content.py"


def _run(cwd: Path, *args: str, script: Path = VERIFY_DOCS) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(script), *args],
        cwd=str(cwd), capture_output=True, text=True, encoding="utf-8",
        env={**os.environ, "PYTHONUTF8": "1"},
    )


def _empty_docs_project(tmp_path: Path, doc_profile: str | None) -> Path:
    # document-registry.yaml is resolved relative to cwd (or a repo-root-relative fallback
    # that only works inside this framework repo's own layout) -- a real project copies it
    # to project root per README, so the fixture must too.
    shutil.copy2(REPO_ROOT / "document-registry.yaml", tmp_path / "document-registry.yaml")
    docs = tmp_path / "docs"
    docs.mkdir()
    if doc_profile is not None:
        (tmp_path / ".project-starter.yml").write_text(
            f"project_type: web-app\ndocs_path: docs/\ndoc_profile: {doc_profile}\n",
            encoding="utf-8",
        )
    return tmp_path


def _statuses_by_doc(results: list[dict]) -> dict[str, str]:
    return {r["doc"]: r["status"] for r in results}


def test_full_profile_is_default_with_no_config_file(tmp_path):
    project = _empty_docs_project(tmp_path, doc_profile=None)
    result = _run(project, "--project-type", "web-app", "--docs", "docs", "--json")
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["doc_profile"] == "full"
    statuses = _statuses_by_doc(data["results"])
    assert statuses["specs/permissions.md"] == "missing_required"


def test_lite_profile_read_from_project_starter_yml(tmp_path):
    project = _empty_docs_project(tmp_path, doc_profile="lite")
    result = _run(project, "--project-type", "web-app", "--docs", "docs", "--json")
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["doc_profile"] == "lite"
    statuses = _statuses_by_doc(data["results"])
    # downgraded docs must no longer block (missing_optional, not missing_required)
    for doc in (
        "specs/permissions.md", "specs/research.md",
        "business/business-rules.md", "business/business-process.md",
        "business/business-objects.md",
        "specs/test-plan.md", "specs/test-report.md",
        "architecture/backend.md", "architecture/database.md", "architecture/deployment.md",
    ):
        assert statuses[doc] == "missing_optional", f"{doc} should be downgraded in lite mode"
    # core contract docs must still be required in lite mode
    for doc in (
        "project-requirements.md", "specs/quickstart.md",
        "specs/data-model.md", "specs/api-contract.md", "architecture/architecture.md",
    ):
        assert statuses[doc] == "missing_required", f"{doc} must stay required even in lite mode"


def test_strict_does_not_block_commit_on_lite_downgraded_docs(tmp_path):
    project = _empty_docs_project(tmp_path, doc_profile="lite")
    # only create the docs that stay required in lite mode (logging-spec.md is
    # deliberately not lite_downgrade'd -- logging discipline stays cheap/valuable even
    # for a small project, see document-registry.yaml)
    (project / "docs" / "specs").mkdir(parents=True)
    (project / "docs" / "architecture").mkdir()
    (project / "docs" / "project-requirements.md").write_text("x", encoding="utf-8")
    (project / "docs" / "specs" / "quickstart.md").write_text("x", encoding="utf-8")
    (project / "docs" / "specs" / "data-model.md").write_text("x", encoding="utf-8")
    (project / "docs" / "specs" / "api-contract.md").write_text("x", encoding="utf-8")
    (project / "docs" / "specs" / "logging-spec.md").write_text("x", encoding="utf-8")
    (project / "docs" / "architecture" / "architecture.md").write_text("x", encoding="utf-8")

    result = _run(project, "--project-type", "web-app", "--docs", "docs", "--strict")
    assert result.returncode == 0, (
        f"lite profile should not block on downgraded docs\nstdout: {result.stdout}"
    )


def test_full_profile_still_blocks_on_the_same_missing_docs(tmp_path):
    """Same fixture as the lite test above, but doc_profile: full -- must still block,
    confirming the lite pass above wasn't just a bug that stopped blocking on everything."""
    project = _empty_docs_project(tmp_path, doc_profile="full")
    (project / "docs" / "specs").mkdir(parents=True)
    (project / "docs" / "architecture").mkdir()
    (project / "docs" / "project-requirements.md").write_text("x", encoding="utf-8")
    (project / "docs" / "specs" / "quickstart.md").write_text("x", encoding="utf-8")
    (project / "docs" / "specs" / "data-model.md").write_text("x", encoding="utf-8")
    (project / "docs" / "specs" / "api-contract.md").write_text("x", encoding="utf-8")
    (project / "docs" / "architecture" / "architecture.md").write_text("x", encoding="utf-8")

    result = _run(project, "--project-type", "web-app", "--docs", "docs", "--strict")
    assert result.returncode == 1


def test_cli_flag_overrides_config_file(tmp_path):
    project = _empty_docs_project(tmp_path, doc_profile="lite")
    result = _run(project, "--project-type", "web-app", "--docs", "docs", "--json", "--full")
    data = json.loads(result.stdout)
    assert data["doc_profile"] == "full"
    assert _statuses_by_doc(data["results"])["specs/permissions.md"] == "missing_required"


def test_lite_and_full_flags_together_is_an_error(tmp_path):
    project = _empty_docs_project(tmp_path, doc_profile=None)
    result = _run(project, "--project-type", "web-app", "--docs", "docs", "--lite", "--full")
    assert result.returncode == 2
    assert "mutually exclusive" in result.stderr


def test_unrecognized_doc_profile_value_defaults_to_full(tmp_path):
    project = _empty_docs_project(tmp_path, doc_profile="something-else")
    result = _run(project, "--project-type", "web-app", "--docs", "docs", "--json")
    data = json.loads(result.stdout)
    assert data["doc_profile"] == "full"


# ---------------------------------------------------------------------------
# verify_content.py -- same doc_profile behavior, different script
# ---------------------------------------------------------------------------

def test_verify_content_lite_excludes_downgraded_docs_from_the_audit_set(tmp_path):
    project = _empty_docs_project(tmp_path, doc_profile="lite")
    result = _run(
        project, "--project-type", "web-app", "--docs", "docs", "--json",
        script=VERIFY_CONTENT,
    )
    assert result.returncode == 0, result.stderr
    data = json.loads(result.stdout)
    assert data["doc_profile"] == "lite"
    audited_names = {d["name"] for d in data["documents"]}
    assert "permissions.md" not in audited_names
    assert "business-rules.md" not in audited_names
    assert "quickstart.md" in audited_names  # unaffected doc still audited


def test_verify_content_full_still_includes_those_docs(tmp_path):
    project = _empty_docs_project(tmp_path, doc_profile="full")
    result = _run(
        project, "--project-type", "web-app", "--docs", "docs", "--json",
        script=VERIFY_CONTENT,
    )
    data = json.loads(result.stdout)
    assert data["doc_profile"] == "full"
    audited_names = {d["name"] for d in data["documents"]}
    assert "permissions.md" in audited_names
    assert "business-rules.md" in audited_names
