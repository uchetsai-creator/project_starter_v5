# Workflow Plan — iac-change / iac
Generated: {{TIMESTAMP}}

## Pre-task
1. Run `python3 orchestrator.py` → read `.ai/AI_CONTEXT.md` and `.ai/WORKFLOW.md`

## Implementation
- Follow Steps in `docs/current-state.md`

## Post-task validators (run in order)
1. `python3 docs/script/validators/verify_registry.py`
2. `python3 docs/script/validators/verify_workflow_registry.py`
3. `python3 docs/script/validators/verify_docs.py --project-type iac --content`
4. `python3 docs/script/validators/verify_content.py --project-type iac --strict`
5. `python3 docs/script/validators/verify_spec_code.py --project-type iac --strict`
6. `python3 docs/script/validators/verify_security.py --project-type iac --strict`

## Closeout
- Follow Closeout section in `docs/current-state.md`

