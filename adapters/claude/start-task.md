Run `python3 orchestrator.py` in the project root to refresh the workflow plan and context for the current task.

Then read:
- `.ai/AI_CONTEXT.md` — ordered read list for the current task
- `.ai/WORKFLOW.md` — deterministic workflow plan (pre-task, validators, closeout)

**Last generated workflow snapshot** (from the most recent `orchestrator.py` run):

> **Note:** if this section is empty or shows a raw placeholder, run
> `python3 orchestrator.py --adapter claude` to inject the current workflow snapshot.

{{WORKFLOW_CONTENT}}

After running the orchestrator and reading both context files, confirm the task type and workflow key, present the steps, and ask which step to begin.
