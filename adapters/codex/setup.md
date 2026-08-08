# Codex Setup

This project uses [project_starter](<your-fork-url>) for documentation-driven development.

## Before starting work

Run the orchestrator to generate the workflow plan and context:

```bash
python3 orchestrator.py
```

This writes:
- `.ai/AI_CONTEXT.md` — ordered read list for the current task
- `.ai/WORKFLOW.md` — deterministic workflow plan with post-task validators

Then read `.codex/task-instructions.md` for the current workflow steps.

> **Note:** if `.codex/task-instructions.md` shows `{{WORKFLOW_CONTENT}}` as literal text, run `python3 orchestrator.py --adapter codex` first to inject the current workflow snapshot.

## Regenerating adapter output

```bash
python3 orchestrator.py --adapter codex
```

This re-runs the orchestrator and refreshes `.codex/task-instructions.md` with the current workflow snapshot.
