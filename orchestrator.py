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

Agent-adapter output (.claude/commands/start-task.md, .codex/setup.md +
.codex/task-instructions.md) is rendered automatically on every run — no flag
needed. Use --adapter to restrict to a single tool, or --no-adapter to skip
adapter rendering entirely for this run:
  python3 orchestrator.py --adapter claude
  python3 orchestrator.py --no-adapter
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

from _workflow_utils import (
    _coerce_project_type,
    _load_valid_task_types,
    _load_yaml,
    _read_task_name_from_current_state,
    _resolve_task_type,
)

VALID_ADAPTERS = ["claude", "codex"]

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
            "> **Note:** if this section is empty or shows a raw placeholder, run\n"
            "> `python3 orchestrator.py --adapter claude` to inject the current workflow snapshot.\n"
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
}


def _invoke_build_context(project_root: Path, task_type: str | None) -> None:
    cmd = [sys.executable, str(project_root / "build-context.py")]
    if task_type:
        cmd += ["--task-type", task_type]
    result = subprocess.run(cmd, capture_output=True, text=True, encoding="utf-8", errors="replace")
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

    spec_code_bindings = _resolve_spec_code_bindings(cfg)

    security_scan_src = cfg.get("security_scan_src") or None
    prose_scan_enabled = cfg.get("prose_scan_enabled") is True

    return {
        "project_type": project_type_str,
        "task_type": task_type,
        "workflow_key": workflow_key,
        "validators": validators,
        "docs_path": docs_path,
        "spec_code_bindings": spec_code_bindings,
        "security_scan_src": security_scan_src,
        "prose_scan_enabled": prose_scan_enabled,
    }


def _resolve_spec_code_bindings(cfg: dict) -> list[dict]:
    """Return a list of {adapter, spec, src} bindings for verify_spec_code.py.

    Supports two forms, checked in this order:
      1. `spec_code_bindings:` — a YAML list of {adapter, spec, src} mappings, for
         projects with more than one contract to validate (e.g. a REST API plus a
         background pipeline in the same repo). Each entry needs all three keys;
         incomplete entries are silently dropped rather than erroring, matching this
         function's overall graceful-skip philosophy — the same as an unconfigured
         single binding rendering no --adapter/--spec/--src flags rather than failing.
      2. The legacy single `spec_code_adapter` / `spec_code_spec` / `spec_code_src`
         trio — still works unchanged, no migration required. Existing
         .project-starter.yml files (this framework's own included) don't need to
         change; `spec_code_bindings` is purely additive.

    Returns an empty list if neither form is configured — verify_spec_code.py still
    runs (per workflow-registry.yaml) but renders with no extra flags and skips
    gracefully, same as before this function existed.
    """
    bindings_raw = cfg.get("spec_code_bindings")
    if bindings_raw:
        bindings = []
        for b in bindings_raw:
            if not isinstance(b, dict):
                continue
            adapter, spec, src = b.get("adapter"), b.get("spec"), b.get("src")
            if adapter and spec and src:
                bindings.append({"adapter": adapter, "spec": spec, "src": src})
        return bindings

    sc_adapter = cfg.get("spec_code_adapter")
    sc_spec = cfg.get("spec_code_spec")
    sc_src = cfg.get("spec_code_src")
    if sc_adapter and sc_spec and sc_src:
        return [{"adapter": sc_adapter, "spec": sc_spec, "src": sc_src}]
    return []


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

    spec_code_bindings = ctx.get("spec_code_bindings") or []
    security_scan_src = ctx.get("security_scan_src")

    if ctx["validators"]:
        rendered: list[str] = []
        for v in ctx["validators"]:
            script = v.get("script", "")
            extra_args = [str(a) for a in v.get("args", [])]
            base_parts = ["python3", script]
            # verify_registry.py validates document-registry.yaml itself,
            # verify_workflow_registry.py validates workflow-registry.yaml itself, and
            # verify_index_coverage.py checks index <-> per-item file coverage by
            # existence alone — none of the three has a project-type concept or accepts
            # --project-type (confirmed: passing it crashes each with "unrecognized
            # arguments", none of the three defines that argparse flag).
            if not script.endswith((
                "verify_registry.py", "verify_workflow_registry.py", "verify_index_coverage.py",
            )):
                base_parts.append(f"--project-type {pt}")

            if script.endswith("verify_spec_code.py") and spec_code_bindings:
                # One rendered line per binding — a project validating more than one
                # contract (e.g. a REST API and a background pipeline) gets one
                # verify_spec_code.py invocation per contract, not one invocation that
                # can only carry a single --adapter/--spec/--src triple.
                for binding in spec_code_bindings:
                    parts = list(base_parts)
                    parts.append(
                        f"--adapter {binding['adapter']} --spec {binding['spec']} --src {binding['src']}",
                    )
                    parts += extra_args
                    rendered.append(" ".join(parts))
                continue

            parts = list(base_parts)
            if security_scan_src and script.endswith("verify_security.py"):
                parts.append(f"--src {security_scan_src}")
            if ctx.get("prose_scan_enabled") and script.endswith("verify_prose.py"):
                parts.append(f"--docs {ctx['docs_path']}")
            parts += extra_args
            rendered.append(" ".join(parts))

        for i, cmd in enumerate(rendered, start=1):
            lines.append(f"{i}. `{cmd}`")
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
    telemetry_dir = project_root / "logs" / "telemetry"
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

    # Optional OTel dual-emission (see _otel.py's docstring) — no-ops unconditionally
    # unless opentelemetry-* is installed and OTEL_EXPORTER_OTLP_ENDPOINT is set. _otel.py
    # lives in docs/script/validators/ in a deployed project, templates/script/validators/
    # in this framework repo's own copy — try both, matching wherever this orchestrator.py
    # actually is (a plain sibling-file import won't reach either).
    try:
        for _candidate in ("docs/script/validators", "templates/script/validators"):
            _dir = project_root / _candidate
            if _dir.is_dir():
                sys.path.insert(0, str(_dir))
                break
        from _otel import emit as _otel_emit  # noqa: PLC0415
        _otel_emit("orchestrator", state)
    except ImportError:
        pass


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


def main() -> None:
    # Force UTF-8 stdout/stderr regardless of host console codepage. This script prints
    # non-ASCII characters (e.g. "→" in WORKFLOW.md output); Python's default text-mode
    # encoding for a redirected/piped stream on Windows is the OS codepage (cp1252, cp950,
    # ...), not UTF-8 — printing "→" through that raises UnicodeEncodeError and crashes the
    # whole script. Confirmed: this is exactly what broke `orchestrator.py --dry-run` on
    # GitHub's windows-latest CI runner (cp1252) — see CHANGELOG.md.
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[union-attr]  # guard above only narrows sys.stdout

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
        help=(
            f"Restrict adapter output to a single tool ({', '.join(VALID_ADAPTERS)}). "
            f"By default all of {VALID_ADAPTERS} are rendered on every run — this flag "
            "narrows that, it does not opt in to something otherwise off."
        ),
    )
    parser.add_argument(
        "--no-adapter",
        action="store_true",
        help="Skip agent-adapter output entirely for this run (.ai/WORKFLOW.md is still written)",
    )
    parser.add_argument(
        "--no-overwrite",
        action="store_true",
        help="Skip writing .ai/WORKFLOW.md if it already exists (preserves manual edits)",
    )
    args = parser.parse_args()

    if args.adapter:
        adapters_to_run = [args.adapter]
    elif args.no_adapter:
        adapters_to_run = []
    else:
        adapters_to_run = VALID_ADAPTERS

    ctx = _build_workflow(project_root, args.task_type)
    output = _render(ctx)

    if args.dry_run:
        print(output)
        for adapter in adapters_to_run:
            _run_adapter(adapter, project_root, output, dry_run=True)
        return

    _invoke_build_context(project_root, ctx["task_type"])

    ai_dir = project_root / ".ai"
    ai_dir.mkdir(exist_ok=True)
    out_path = ai_dir / "WORKFLOW.md"

    if args.no_overwrite and out_path.exists():
        print(f"[SKIP] {out_path} already exists — skipped (--no-overwrite active, manual edits preserved)")
    else:
        out_path.write_text(output, encoding="utf-8")
        print(f"[OK] Written to {out_path}")

    print(f"    Project type : {ctx['project_type']}")
    print(f"    Task type    : {ctx['task_type'] or 'unset'}")
    print(f"    Workflow     : {ctx['workflow_key']}")
    print(f"    Validators   : {len(ctx['validators'])}")

    docs_dir = project_root / ctx["docs_path"]
    task_name = _read_task_name_from_current_state(docs_dir / "current-state.md")
    _track_orchestrator_run(project_root, task_name)

    for adapter in adapters_to_run:
        _run_adapter(adapter, project_root, output, dry_run=False)


if __name__ == "__main__":
    main()
