"""
_workflow_utils.py — Shared task-type helpers for orchestrator.py and build-context.py.
"""
from __future__ import annotations

import re
import sys
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


def _coerce_project_type(raw) -> str:
    """Coerce project_type from config (list or str) to '+'-joined string; exit on placeholder."""
    if isinstance(raw, list):
        coerced = "+".join(str(x) for x in raw)
    else:
        coerced = str(raw or "")
    if not coerced or coerced in ("your-project-type", "[your-project-type]"):
        print(
            "❌  project_type not set in .project-starter.yml — replace [your-project-type] with your actual type",
            file=sys.stderr,
        )
        sys.exit(1)
    return coerced


def _resolve_task_type(cfg: dict, current_state_path: Path, override: str | None) -> str | None:
    if override:
        return override
    from_state = _read_task_type_from_current_state(current_state_path)
    if from_state:
        return from_state
    return cfg.get("task_type") or None
