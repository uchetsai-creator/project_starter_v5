# Workflow Plan — eval-run / llm-app
Generated: {{TIMESTAMP}}

## Pre-task
1. Run `python3 orchestrator.py` → read `.ai/AI_CONTEXT.md` and `.ai/WORKFLOW.md`

## Implementation
- Follow Steps in `docs/current-state.md`

## Post-task validators (run in order)
1. `python3 docs/script/validators/verify_registry.py --project-type llm-app`
2. `python3 docs/script/validators/verify_docs.py --project-type llm-app --content`
3. `python3 docs/script/validators/verify_content.py --project-type llm-app --strict`

## Closeout
- Follow Closeout section in `docs/current-state.md`

