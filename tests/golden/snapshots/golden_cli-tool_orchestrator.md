# Workflow Plan — feature / cli-tool
Generated: {{TIMESTAMP}}

## Pre-task
1. Run `python3 orchestrator.py` → read `.ai/AI_CONTEXT.md` and `.ai/WORKFLOW.md`

## Implementation
- Follow Steps in `docs/current-state.md`

## Post-task validators (run in order)
1. `python3 docs/script/validators/verify_registry.py --project-type cli-tool`
2. `python3 docs/script/validators/verify_docs.py --project-type cli-tool --content`
3. `python3 docs/script/validators/verify_logs.py --project-type cli-tool --strict`
4. `python3 docs/script/validators/verify_content.py --project-type cli-tool --strict`
5. `python3 docs/script/validators/verify_spec_code.py --project-type cli-tool --strict`

## Closeout
- Follow Closeout section in `docs/current-state.md`

