# Workflow Plan — feature / microservices
Generated: {{TIMESTAMP}}

## Pre-task
1. Run `python3 orchestrator.py` → read `.ai/AI_CONTEXT.md` and `.ai/WORKFLOW.md`

## Implementation
- Follow Steps in `docs/current-state.md`

## Post-task validators (run in order)
1. `python3 docs/script/validators/verify_registry.py`
2. `python3 docs/script/validators/verify_workflow_registry.py`
3. `python3 docs/script/validators/verify_docs.py --project-type microservices --content`
4. `python3 docs/script/validators/verify_logs.py --project-type microservices --strict`
5. `python3 docs/script/validators/verify_content.py --project-type microservices --strict`
6. `python3 docs/script/validators/verify_spec_code.py --project-type microservices --strict`
7. `python3 docs/script/validators/verify_security.py --project-type microservices --strict`

## Closeout
- Follow Closeout section in `docs/current-state.md`


--- .claude/commands/start-task.md (dry-run) ---
Run `python3 orchestrator.py` in the project root to refresh the workflow plan and context for the current task.

Then read:
- `.ai/AI_CONTEXT.md` — ordered read list for the current task
- `.ai/WORKFLOW.md` — deterministic workflow plan (pre-task, validators, closeout)

**Last generated workflow snapshot** (from the most recent `orchestrator.py` run):

> **Note:** if this section is empty or shows a raw placeholder, run
> `python3 orchestrator.py --adapter claude` to inject the current workflow snapshot.

# Workflow Plan — feature / microservices
Generated: {{TIMESTAMP}}

## Pre-task
1. Run `python3 orchestrator.py` → read `.ai/AI_CONTEXT.md` and `.ai/WORKFLOW.md`

## Implementation
- Follow Steps in `docs/current-state.md`

## Post-task validators (run in order)
1. `python3 docs/script/validators/verify_registry.py`
2. `python3 docs/script/validators/verify_workflow_registry.py`
3. `python3 docs/script/validators/verify_docs.py --project-type microservices --content`
4. `python3 docs/script/validators/verify_logs.py --project-type microservices --strict`
5. `python3 docs/script/validators/verify_content.py --project-type microservices --strict`
6. `python3 docs/script/validators/verify_spec_code.py --project-type microservices --strict`
7. `python3 docs/script/validators/verify_security.py --project-type microservices --strict`

## Closeout
- Follow Closeout section in `docs/current-state.md`


After running the orchestrator and reading both context files, confirm the task type and workflow key, present the steps, and ask which step to begin.


--- .codex/setup.md (dry-run) ---
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

> **Note:** if `.codex/task-instructions.md` shows `# Workflow Plan — feature / microservices
Generated: {{TIMESTAMP}}

## Pre-task
1. Run `python3 orchestrator.py` → read `.ai/AI_CONTEXT.md` and `.ai/WORKFLOW.md`

## Implementation
- Follow Steps in `docs/current-state.md`

## Post-task validators (run in order)
1. `python3 docs/script/validators/verify_registry.py`
2. `python3 docs/script/validators/verify_workflow_registry.py`
3. `python3 docs/script/validators/verify_docs.py --project-type microservices --content`
4. `python3 docs/script/validators/verify_logs.py --project-type microservices --strict`
5. `python3 docs/script/validators/verify_content.py --project-type microservices --strict`
6. `python3 docs/script/validators/verify_spec_code.py --project-type microservices --strict`
7. `python3 docs/script/validators/verify_security.py --project-type microservices --strict`

## Closeout
- Follow Closeout section in `docs/current-state.md`
` as literal text, run `python3 orchestrator.py --adapter codex` first to inject the current workflow snapshot.

## Regenerating adapter output

```bash
python3 orchestrator.py --adapter codex
```

This re-runs the orchestrator and refreshes `.codex/task-instructions.md` with the current workflow snapshot.


--- .codex/task-instructions.md (dry-run) ---
# Task Instructions

Follow the steps below. Run post-task validators in order before committing.

# Workflow Plan — feature / microservices
Generated: {{TIMESTAMP}}

## Pre-task
1. Run `python3 orchestrator.py` → read `.ai/AI_CONTEXT.md` and `.ai/WORKFLOW.md`

## Implementation
- Follow Steps in `docs/current-state.md`

## Post-task validators (run in order)
1. `python3 docs/script/validators/verify_registry.py`
2. `python3 docs/script/validators/verify_workflow_registry.py`
3. `python3 docs/script/validators/verify_docs.py --project-type microservices --content`
4. `python3 docs/script/validators/verify_logs.py --project-type microservices --strict`
5. `python3 docs/script/validators/verify_content.py --project-type microservices --strict`
6. `python3 docs/script/validators/verify_spec_code.py --project-type microservices --strict`
7. `python3 docs/script/validators/verify_security.py --project-type microservices --strict`

## Closeout
- Follow Closeout section in `docs/current-state.md`


---

Regenerate this file at any time:

```bash
python3 orchestrator.py --adapter codex
```

