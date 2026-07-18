#!/usr/bin/env python3
"""
build-context.py — Context Builder for project_starter_v4.

Reads .project-starter.yml + docs/current-state.md, queries document-registry.yaml,
and writes .ai/AI_CONTEXT.md listing exactly which files the AI must read.

Usage:
  python3 build-context.py
  python3 build-context.py --task-type sprint-end
  python3 build-context.py --dry-run
"""

import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

from _workflow_utils import _read_task_type_from_current_state, _resolve_task_type

try:
    import yaml
except ImportError:
    print("❌  PyYAML not found. Install with: pip install pyyaml", file=sys.stderr)
    sys.exit(1)

# Task type → document keys that are relevant (used to filter Optional docs).
# None means "all" (sprint-end includes everything).
TASK_TYPE_DOCS: dict[str, list[str] | None] = {
    "feature":        ["architecture", "backend", "data-model", "api-contract", "permissions", "logging-spec"],
    "pipeline-stage": ["pipeline-contract", "pipeline-debug", "data-model", "logging-spec"],
    "bug-fix":        ["pipeline-debug", "llm-debug", "logging-spec"],
    "sprint-end":     None,
    "eval-run":       ["eval-spec", "eval-log", "llm-contract"],
    "iac-change":     ["topology", "runbook", "drift-policy"],
}

PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}

VALID_TASK_TYPES = list(TASK_TYPE_DOCS)


def _load_yaml(path: Path) -> dict:
    with path.open() as fh:
        return yaml.safe_load(fh) or {}




def _classify(doc_key: str, meta: dict, project_type: str, task_type: str | None) -> str:
    """Return 'required', 'if_present', or 'skip'."""
    pt_parts = [p.strip() for p in project_type.split("+")]
    required_for = meta.get("required_for", [])
    optional_for = meta.get("optional_for", [])

    is_required = any(pt in required_for for pt in pt_parts)
    is_optional = any(pt in optional_for for pt in pt_parts)

    if is_required:
        return "required"

    if is_optional:
        if task_type is None:
            return "if_present"
        relevant = TASK_TYPE_DOCS.get(task_type)
        if relevant is None:          # sprint-end: treat optional as required
            return "required"
        return "if_present" if doc_key in relevant else "skip"

    return "skip"


def build_context(project_root: Path, task_type_override: str | None = None) -> dict:
    yml_path = project_root / ".project-starter.yml"
    registry_path = project_root / "document-registry.yaml"

    if not yml_path.exists():
        print(f"❌  .project-starter.yml not found at {yml_path}", file=sys.stderr)
        sys.exit(1)
    if not registry_path.exists():
        print(f"❌  document-registry.yaml not found at {registry_path}", file=sys.stderr)
        sys.exit(1)

    cfg = _load_yaml(yml_path)
    project_type_raw = cfg.get("project_type", "")
    # YAML parses `[your-project-type]` as a list; coerce to string for display
    if isinstance(project_type_raw, list):
        project_type_str = "+".join(str(x) for x in project_type_raw)
    else:
        project_type_str = str(project_type_raw or "")
    if not project_type_str or project_type_str in ("your-project-type", "[your-project-type]"):
        print("❌  project_type not set in .project-starter.yml — replace [your-project-type] with your actual type", file=sys.stderr)
        sys.exit(1)
    project_type = project_type_str

    docs_path = cfg.get("docs_path", "docs/").rstrip("/")
    current_state_path = project_root / docs_path / "current-state.md"

    task_type = _resolve_task_type(cfg, current_state_path, task_type_override)

    documents = _load_yaml(registry_path).get("documents", {})

    required: list[dict] = []
    if_present: list[dict] = []
    skipped: list[dict] = []

    for key, meta in documents.items():
        status = _classify(key, meta, project_type, task_type)
        entry = {
            "key":      key,
            "path":     f"{docs_path}/{meta['path']}",
            "purpose":  meta.get("purpose", ""),
            "priority": meta.get("context_priority", "medium"),
        }
        if status == "required":
            required.append(entry)
        elif status == "if_present":
            if_present.append(entry)
        else:
            skipped.append(entry)

    # Sort required docs high → medium → low
    required.sort(key=lambda e: PRIORITY_ORDER.get(e["priority"], 1))

    # current-state.md always first
    cs = {
        "key":      "current-state",
        "path":     f"{docs_path}/current-state.md",
        "purpose":  "Active task: goal, steps, and required context",
        "priority": "high",
    }
    required = [cs] + [e for e in required if e["key"] != "current-state"]

    return {
        "project_type": project_type,
        "task_type":    task_type,
        "required":     required,
        "if_present":   if_present,
        "skipped":      skipped,
    }


def _render(ctx: dict) -> str:
    now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S")
    task_label = ctx["task_type"] or "unset"
    lines = [
        f"# AI Context — {ctx['project_type']} / {task_label}",
        f"Generated: {now}",
        "",
        "## Read (Required)",
    ]
    for e in ctx["required"]:
        lines.append(f"- {e['path']}   # {e['purpose']}")

    if ctx["if_present"]:
        lines.append("")
        lines.append("## Read (If Present)")
        for e in ctx["if_present"]:
            lines.append(f"- {e['path']}   # {e['purpose']}")

    if ctx["skipped"]:
        lines.append("")
        lines.append("## Skip")
        for e in ctx["skipped"]:
            lines.append(f"- {e['path']}")

    lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Generate .ai/AI_CONTEXT.md for the current task."
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
        help="Print output without writing .ai/AI_CONTEXT.md",
    )
    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent
    ctx = build_context(project_root, args.task_type)
    output = _render(ctx)

    if args.dry_run:
        print(output)
        return

    ai_dir = project_root / ".ai"
    ai_dir.mkdir(exist_ok=True)
    out_path = ai_dir / "AI_CONTEXT.md"
    out_path.write_text(output)

    print(f"✅  Written to {out_path}")
    print(f"    Project type : {ctx['project_type']}")
    print(f"    Task type    : {ctx['task_type'] or 'unset — showing all Required docs'}")
    print(f"    Required     : {len(ctx['required'])} docs")
    print(f"    If present   : {len(ctx['if_present'])} docs")
    print(f"    Skip         : {len(ctx['skipped'])} docs")


if __name__ == "__main__":
    main()
