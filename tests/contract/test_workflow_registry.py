from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent


def load_workflow_registry() -> dict:
    path = _REPO_ROOT / "workflow-registry.yaml"
    with path.open(encoding="utf-8") as f:
        return (yaml.safe_load(f) or {}).get("workflows", {})


def _resolve_script(script: str) -> Path:
    """Map workflow-registry script paths to their location in the framework repo.

    User-project paths use docs/script/; the framework source lives in templates/script/.
    """
    direct = _REPO_ROOT / script
    if direct.exists():
        return direct
    return _REPO_ROOT / script.replace("docs/", "templates/", 1)


# ---------------------------------------------------------------------------
# Contract 4 — every declared validator script exists on disk
# ---------------------------------------------------------------------------

def test_workflow_registry_all_scripts_exist():
    for task_type, workflow in load_workflow_registry().items():
        for v in workflow.get("validators", []):
            p = _resolve_script(v["script"])
            assert p.exists(), f"Missing script: {v['script']} (task_type={task_type})"
