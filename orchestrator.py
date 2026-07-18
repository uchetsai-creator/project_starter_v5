#!/usr/bin/env python3
"""
orchestrator.py — Workflow Manager for project_starter_v4.

Reads .project-starter.yml + docs/current-state.md, selects the correct
validator sequence from workflow-registry.yaml, invokes build-context.py
internally, and writes .ai/WORKFLOW.md so AI agents follow a deterministic plan.

Usage:
  python3 orchestrator.py
  python3 orchestrator.py --task-type sprint-end
  python3 orchestrator.py --dry-run
"""

import argparse
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

try:
    import yaml
except ImportError:
    print("❌  PyYAML not found. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

VALID_TASK_TYPES = ["feature", "pipeline-stage", "bug-fix", "sprint-end", "eval-run", "iac-change"]


def _load_yaml(path: Path) -> dict:
    with path.open() as fh:
        return yaml.safe_load(fh) or {}


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


def _invoke_build_context(project_root: Path, task_type: str | None) -> None:
    cmd = [sys.executable, str(project_root / "build-context.py")]
    if task_type:
        cmd += ["--task-type", task_type]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(result.stderr, file=sys.stderr, end="")
        sys.exit(result.returncode)
    print(result.stdout, end="")


def _build_workflow(project_root: Path, task_type_override: str | None = None) -> dict:
    yml_path = project_root / ".project-starter.yml"
    registry_path = project_root / "workflow-registry.yaml"

    if not yml_path.exists():
        print(f"❌  .project-starter.yml not found at {yml_path}", file=sys.stderr)
        sys.exit(1)
    if not registry_path.exists():
        print(f"❌  workflow-registry.yaml not found at {registry_path}", file=sys.stderr)
        sys.exit(1)

    cfg = _load_yaml(yml_path)
    project_type_raw = cfg.get("project_type", "")
    if isinstance(project_type_raw, list):
        project_type_str = "+".join(str(x) for x in project_type_raw)
    else:
        project_type_str = str(project_type_raw or "")
    if not project_type_str or project_type_str in ("your-project-type", "[your-project-type]"):
        print(
            "❌  project_type not set in .project-starter.yml — replace [your-project-type] with your actual type",
            file=sys.stderr,
        )
        sys.exit(1)

    docs_path = cfg.get("docs_path", "docs/").rstrip("/")
    current_state_path = project_root / docs_path / "current-state.md"

    task_type = _resolve_task_type(cfg, current_state_path, task_type_override)

    workflows = _load_yaml(registry_path).get("workflows", {})
    workflow_key = task_type if (task_type and task_type in workflows) else "default"
    workflow = workflows.get(workflow_key, {})
    validators = workflow.get("validators", [])

    return {
        "project_type": project_type_str,
        "task_type": task_type,
        "workflow_key": workflow_key,
        "validators": validators,
    }


def _render(ctx: dict) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    task_label = ctx["task_type"] or "unset"
    pt = ctx["project_type"]

    lines = [
        f"# Workflow Plan — {task_label} / {pt}",
        f"Generated: {now}",
        "",
        "## Pre-task",
        "1. Run `python3 orchestrator.py` → read `.ai/AI_CONTEXT.md` and `.ai/WORKFLOW.md`",
        "",
        "## Implementation",
        "- Follow Steps in `docs/current-state.md`",
        "",
        "## Post-task validators (run in order)",
    ]

    if ctx["validators"]:
        for i, v in enumerate(ctx["validators"], start=1):
            script = v.get("script", "")
            extra_args = v.get("args", [])
            parts = ["python3", script, f"--project-type {pt}"] + [str(a) for a in extra_args]
            lines.append(f"{i}. `{' '.join(parts)}`")
    else:
        lines.append("_(no validators configured for this task type)_")

    lines += [
        "",
        "## Closeout",
        "- Follow Closeout section in `docs/current-state.md`",
        "",
    ]
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate .ai/WORKFLOW.md for the current task."
    )
    parser.add_argument(
        "--task-type",
        choices=VALID_TASK_TYPES,
        metavar="TYPE",
        help=f"Override task type ({', '.join(VALID_TASK_TYPES)})",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print output without writing .ai/WORKFLOW.md or invoking build-context.py",
    )
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent
    ctx = _build_workflow(project_root, args.task_type)
    output = _render(ctx)

    if args.dry_run:
        print(output)
        return

    _invoke_build_context(project_root, ctx["task_type"])

    ai_dir = project_root / ".ai"
    ai_dir.mkdir(exist_ok=True)
    out_path = ai_dir / "WORKFLOW.md"
    out_path.write_text(output)

    print(f"✅  Written to {out_path}")
    print(f"    Project type : {ctx['project_type']}")
    print(f"    Task type    : {ctx['task_type'] or 'unset'}")
    print(f"    Workflow     : {ctx['workflow_key']}")
    print(f"    Validators   : {len(ctx['validators'])}")


if __name__ == "__main__":
    main()
