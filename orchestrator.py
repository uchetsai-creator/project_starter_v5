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
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from _workflow_utils import _coerce_project_type, _load_valid_task_types, _load_yaml, _read_task_name_from_current_state, _resolve_task_type

VALID_ADAPTERS = ["claude", "codex", "cursor"]

# Adapter output templates, embedded so `--adapter` works from a plain copy of this
# file with no `adapters/` directory present (adapters/ stays in the framework repo —
# see README.md -> Agent Adapters). Keep byte-identical to adapters/<tool>/<file> in
# the framework repo; tests/contract/test_adapter_contracts.py guards against drift.
_ADAPTER_TEMPLATES = {
    "claude": {
        "start-task.md": (
            "Run `python3 orchestrator.py` in the project root to refresh the workflow plan and context for the current task.\n"
            "\n"
            "Then read:\n"
            "- `.ai/AI_CONTEXT.md` — ordered read list for the current task\n"
            "- `.ai/WORKFLOW.md` — deterministic workflow plan (pre-task, validators, closeout)\n"
            "\n"
            "**Last generated workflow snapshot** (from the most recent `orchestrator.py` run):\n"
            "\n"
            "{{WORKFLOW_CONTENT}}\n"
            "\n"
            "After running the orchestrator and reading both context files, confirm the task type and workflow key, present the steps, and ask which step to begin.\n"
        ),
    },
    "codex": {
        "setup.md": (
            "# Codex Setup\n"
            "\n"
            "This project uses [project_starter](<your-fork-url>) for documentation-driven development.\n"
            "\n"
            "## Before starting work\n"
            "\n"
            "Run the orchestrator to generate the workflow plan and context:\n"
            "\n"
            "```bash\n"
            "python3 orchestrator.py\n"
            "```\n"
            "\n"
            "This writes:\n"
            "- `.ai/AI_CONTEXT.md` — ordered read list for the current task\n"
            "- `.ai/WORKFLOW.md` — deterministic workflow plan with post-task validators\n"
            "\n"
            "Then read `.codex/task-instructions.md` for the current workflow steps.\n"
            "\n"
            "> **Note:** if `.codex/task-instructions.md` shows `{{WORKFLOW_CONTENT}}` as literal text, run `python3 orchestrator.py --adapter codex` first to inject the current workflow snapshot.\n"
            "\n"
            "## Regenerating adapter output\n"
            "\n"
            "```bash\n"
            "python3 orchestrator.py --adapter codex\n"
            "```\n"
            "\n"
            "This re-runs the orchestrator and refreshes `.codex/task-instructions.md` with the current workflow snapshot.\n"
        ),
        "task-instructions.md": (
            "# Task Instructions\n"
            "\n"
            "Follow the steps below. Run post-task validators in order before committing.\n"
            "\n"
            "{{WORKFLOW_CONTENT}}\n"
            "\n"
            "---\n"
            "\n"
            "Regenerate this file at any time:\n"
            "\n"
            "```bash\n"
            "python3 orchestrator.py --adapter codex\n"
            "```\n"
        ),
    },
    "cursor": {
        ".cursorrules": (
            "# project_starter workflow rules\n"
            "\n"
            "## Before starting any task\n"
            "\n"
            "1. Run `python3 orchestrator.py` in the project root\n"
            "2. Read `.ai/AI_CONTEXT.md` — ordered context for the current task\n"
            "3. Read `.ai/WORKFLOW.md` — deterministic workflow plan\n"
            "\n"
            "## Current workflow snapshot\n"
            "\n"
            "{{WORKFLOW_CONTENT}}\n"
            "\n"
            "## Post-task\n"
            "\n"
            "Run all validators listed under \"Post-task validators\" in `.ai/WORKFLOW.md` in order before committing.\n"
            "\n"
            "## Constraint\n"
            "\n"
            "Document selection logic lives exclusively in `document-registry.yaml` and `orchestrator.py`. Do not add selection logic to adapter files.\n"
            "\n"
            "## Regenerate\n"
            "\n"
            "```bash\n"
            "python3 orchestrator.py --adapter cursor\n"
            "```\n"
        ),
    },
}


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
        print(f"[FAIL] .project-starter.yml not found at {yml_path}", file=sys.stderr)
        sys.exit(1)
    if not registry_path.exists():
        print(f"[FAIL] workflow-registry.yaml not found at {registry_path}", file=sys.stderr)
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

    spec_code = None
    sc_adapter = cfg.get("spec_code_adapter")
    sc_spec = cfg.get("spec_code_spec")
    sc_src = cfg.get("spec_code_src")
    if sc_adapter and sc_spec and sc_src:
        spec_code = {"adapter": sc_adapter, "spec": sc_spec, "src": sc_src}

    return {
        "project_type": project_type_str,
        "task_type": task_type,
        "workflow_key": workflow_key,
        "validators": validators,
        "docs_path": docs_path,
        "spec_code": spec_code,
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

    spec_code = ctx.get("spec_code")

    if ctx["validators"]:
        for i, v in enumerate(ctx["validators"], start=1):
            script = v.get("script", "")
            extra_args = [str(a) for a in v.get("args", [])]
            parts = ["python3", script]
            # verify_registry.py validates document-registry.yaml itself — it has no
            # project-type concept and does not accept --project-type.
            if not script.endswith("verify_registry.py"):
                parts.append(f"--project-type {pt}")
            if spec_code and script.endswith("verify_spec_code.py"):
                parts.append(f"--adapter {spec_code['adapter']} --spec {spec_code['spec']} --src {spec_code['src']}")
            parts += extra_args
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


def _track_orchestrator_run(project_root: Path, task_name: str) -> None:
    telemetry_dir = project_root / ".ai" / "telemetry"
    telemetry_dir.mkdir(parents=True, exist_ok=True)
    state_file = telemetry_dir / ".orchestrator_runs.json"
    try:
        state = json.loads(state_file.read_text(encoding="utf-8")) if state_file.exists() else {}
    except (json.JSONDecodeError, OSError):
        state = {}
    if state.get("task") == task_name:
        state["runs"] = state.get("runs", 0) + 1
    else:
        state = {"task": task_name, "runs": 1}
    state_file.write_text(json.dumps(state), encoding="utf-8")


def _render_adapter_file(template_text: str, workflow_content: str) -> str:
    return template_text.replace("{{WORKFLOW_CONTENT}}", workflow_content)


def _run_adapter(adapter: str, project_root: Path, workflow_content: str, dry_run: bool) -> None:
    templates = _ADAPTER_TEMPLATES[adapter]

    if adapter == "claude":
        rendered = _render_adapter_file(templates["start-task.md"], workflow_content)
        if dry_run:
            print("\n--- .claude/commands/start-task.md (dry-run) ---")
            print(rendered)
        else:
            out_dir = project_root / ".claude" / "commands"
            out_dir.mkdir(parents=True, exist_ok=True)
            out_path = out_dir / "start-task.md"
            out_path.write_text(rendered, encoding="utf-8")
            print(f"[OK] Adapter → {out_path}")

    elif adapter == "codex":
        for filename in ("setup.md", "task-instructions.md"):
            rendered = _render_adapter_file(templates[filename], workflow_content)
            if dry_run:
                print(f"\n--- .codex/{filename} (dry-run) ---")
                print(rendered)
            else:
                out_dir = project_root / ".codex"
                out_dir.mkdir(exist_ok=True)
                out_path = out_dir / filename
                out_path.write_text(rendered, encoding="utf-8")
                print(f"[OK] Adapter → {out_path}")

    elif adapter == "cursor":
        rendered = _render_adapter_file(templates[".cursorrules"], workflow_content)
        if dry_run:
            print("\n--- .cursorrules (dry-run) ---")
            print(rendered)
        else:
            out_path = project_root / ".cursorrules"
            out_path.write_text(rendered, encoding="utf-8")
            print(f"[OK] Adapter → {out_path}")


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
    out_path.write_text(output, encoding="utf-8")

    docs_dir = project_root / ctx["docs_path"]
    task_name = _read_task_name_from_current_state(docs_dir / "current-state.md")
    _track_orchestrator_run(project_root, task_name)

    print(f"[OK] Written to {out_path}")
    print(f"    Project type : {ctx['project_type']}")
    print(f"    Task type    : {ctx['task_type'] or 'unset'}")
    print(f"    Workflow     : {ctx['workflow_key']}")
    print(f"    Validators   : {len(ctx['validators'])}")

    if args.adapter:
        _run_adapter(args.adapter, project_root, output, dry_run=False)


if __name__ == "__main__":
    main()
