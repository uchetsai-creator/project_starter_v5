#!/usr/bin/env python3
"""
orchestrator.py — Workflow Manager for project_starter_v5.

Reads .project-starter.yml + docs/current-state.md, selects the correct
validator sequence from workflow-registry.yaml, invokes build-context.py
internally, and writes .ai/WORKFLOW.md so AI agents follow a deterministic plan.

Usage:
  python3 orchestrator.py
  python3 orchestrator.py --task-type sprint-end
  python3 orchestrator.py --dry-run
  python3 orchestrator.py --adapter claude
  python3 orchestrator.py --adapter claude --dry-run
"""

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from _workflow_utils import _coerce_project_type, _load_valid_task_types, _resolve_task_type

try:
    import yaml
except ImportError:
    print("❌  PyYAML not found. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

VALID_ADAPTERS = ["claude", "codex", "cursor"]


def _load_yaml(path: Path) -> dict:
    with path.open() as fh:
        return yaml.safe_load(fh) or {}


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
    project_type_str = _coerce_project_type(cfg.get("project_type", ""))

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
        "docs_path": docs_path,
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


def _read_task_name(docs_path: Path) -> str:
    state = docs_path / "current-state.md"
    if not state.exists():
        return "(unknown)"
    text = state.read_text()
    m = re.search(r"\*\*Task:\*\*\s*(.+)", text)
    return m.group(1).strip() if m else "(unknown)"


def _track_orchestrator_run(project_root: Path, task_name: str) -> None:
    telemetry_dir = project_root / ".ai" / "telemetry"
    telemetry_dir.mkdir(parents=True, exist_ok=True)
    state_file = telemetry_dir / ".orchestrator_runs.json"
    try:
        state = json.loads(state_file.read_text()) if state_file.exists() else {}
    except (json.JSONDecodeError, OSError):
        state = {}
    if state.get("task") == task_name:
        state["runs"] = state.get("runs", 0) + 1
    else:
        state = {"task": task_name, "runs": 1}
    state_file.write_text(json.dumps(state))


def _render_adapter_file(template_path: Path, workflow_content: str) -> str:
    return template_path.read_text().replace("{{WORKFLOW_CONTENT}}", workflow_content)


def _run_adapter(adapter: str, project_root: Path, workflow_content: str, dry_run: bool) -> None:
    adapter_dir = project_root / "adapters" / adapter

    if adapter == "claude":
        template = adapter_dir / "start-task.md"
        if not template.exists():
            print(f"❌  Adapter template not found: {template}", file=sys.stderr)
            sys.exit(1)
        rendered = _render_adapter_file(template, workflow_content)
        if dry_run:
            print("\n--- .claude/commands/start-task.md (dry-run) ---")
            print(rendered)
        else:
            out_dir = project_root / ".claude" / "commands"
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / "start-task.md"
            out_path.write_text(rendered)
            print(f"✅  Adapter → {out_path}")

    elif adapter == "codex":
        for filename in ("setup.md", "task-instructions.md"):
            template = adapter_dir / filename
            if not template.exists():
                print(f"❌  Adapter template not found: {template}", file=sys.stderr)
                sys.exit(1)
            rendered = _render_adapter_file(template, workflow_content)
            if dry_run:
                print(f"\n--- .codex/{filename} (dry-run) ---")
                print(rendered)
            else:
                out_dir = project_root / ".codex"
                out_dir.mkdir(exist_ok=True)
                out_path = out_dir / filename
                out_path.write_text(rendered)
                print(f"✅  Adapter → {out_path}")

    elif adapter == "cursor":
        template = adapter_dir / ".cursorrules"
        if not template.exists():
            print(f"❌  Adapter template not found: {template}", file=sys.stderr)
            sys.exit(1)
        rendered = _render_adapter_file(template, workflow_content)
        if dry_run:
            print("\n--- .cursorrules (dry-run) ---")
            print(rendered)
        else:
            out_path = project_root / ".cursorrules"
            out_path.write_text(rendered)
            print(f"✅  Adapter → {out_path}")


def main() -> None:
    project_root = Path(__file__).resolve().parent
    valid_task_types = _load_valid_task_types(project_root)

    parser = argparse.ArgumentParser(
        description="Generate .ai/WORKFLOW.md for the current task."
    )
    parser.add_argument(
        "--task-type",
        choices=valid_task_types or None,
        metavar="TYPE",
        help=f"Override task type ({', '.join(valid_task_types)})" if valid_task_types else "Override task type",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print output without writing .ai/WORKFLOW.md or invoking build-context.py",
    )
    parser.add_argument(
        "--adapter",
        choices=VALID_ADAPTERS,
        metavar="TOOL",
        help=f"Render adapter output after writing WORKFLOW.md ({', '.join(VALID_ADAPTERS)})",
    )
    args = parser.parse_args()

    ctx = _build_workflow(project_root, args.task_type)
    output = _render(ctx)

    if args.dry_run:
        print(output)
        if args.adapter:
            _run_adapter(args.adapter, project_root, output, dry_run=True)
        return

    _invoke_build_context(project_root, ctx["task_type"])

    ai_dir = project_root / ".ai"
    ai_dir.mkdir(exist_ok=True)
    out_path = ai_dir / "WORKFLOW.md"
    out_path.write_text(output)

    docs_dir = project_root / ctx["docs_path"]
    task_name = _read_task_name(docs_dir)
    _track_orchestrator_run(project_root, task_name)

    print(f"✅  Written to {out_path}")
    print(f"    Project type : {ctx['project_type']}")
    print(f"    Task type    : {ctx['task_type'] or 'unset'}")
    print(f"    Workflow     : {ctx['workflow_key']}")
    print(f"    Validators   : {len(ctx['validators'])}")

    if args.adapter:
        _run_adapter(args.adapter, project_root, output, dry_run=False)


if __name__ == "__main__":
    main()
