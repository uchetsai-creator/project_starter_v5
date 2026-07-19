"""
_workflow_utils.py — Shared task-type helpers for orchestrator.py and build-context.py.
"""
from __future__ import annotations

import re
from pathlib import Path


def _load_valid_task_types(project_root: Path) -> list[str]:
    """Derive valid task types from workflow-registry.yaml keys (excluding 'default')."""
    try:
        import yaml
    except ImportError:
        return []
    wf_path = project_root / "workflow-registry.yaml"
    if not wf_path.exists():
        return []
    with wf_path.open(encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}
    return [k for k in data.get("workflows", {}) if k != "default"]


def _read_task_type_from_current_state(path: Path) -> str | None:
    if not path.exists():
        return None
    text = path.read_text()
    m = re.search(r"\*\*Task Type:\*\*\s*(\S+)", text)
    if m:
        value = m.group(1).strip("[]")
        if value and value not in ("task-type", ""):
            return value
    return None


def _resolve_task_type(cfg: dict, current_state_path: Path, override: str | None) -> str | None:
    if override:
        return override
    from_state = _read_task_type_from_current_state(current_state_path)
    if from_state:
        return from_state
    return cfg.get("task_type") or None
