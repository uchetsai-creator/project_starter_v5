# Project Initialization — AI / LLM Application

<!--
  Read this file ONCE when starting a new AI / LLM Application project.
  After initialization is complete, this file is no longer needed for day-to-day tasks.
  Workflow rules, task completion, and sprint sync live in AGENTS.md.
-->

1. Create docs/project-requirements.md from templates/project-requirements.md.
2. Create docs/specs/research.md from templates/specs/research.md (model selection, provider, alternatives considered).
3. Create docs/specs/quickstart.md from templates/specs/quickstart.md (API key setup, local run, first query).
4. Create docs/architecture/architecture.md from templates/architecture/architecture.md.
5. Create docs/specs/llm-contract.md from templates/specs/llm-contract.md (model, system prompt, parameters, tools).
6. Create docs/specs/prompt-library.md from templates/specs/prompt-library.md (index only — prompt content goes in per-prompt files).
7. Create docs/specs/prompts/ folder. For each prompt, create docs/specs/prompts/[prompt-id]-prompt.md from templates/specs/prompts/prompt.md.
8. Create docs/specs/eval-spec.md from templates/specs/eval-spec.md (judge model, criteria, test case set).
9. Create docs/specs/eval-log.md from templates/specs/eval-log.md (append-only run log — load only during eval tasks).
10. Create docs/specs/llm-debug.md from templates/specs/llm-debug.md.
11. Create docs/specs/logging-spec.md from templates/specs/logging-spec.md.
12. If using RAG: Create docs/specs/rag-contract.md from templates/specs/rag-contract.md.
13. If using MCP servers: Create docs/specs/mcp-contract.md from templates/specs/mcp-contract.md. Add one Server Detail block per connected server. Cross-reference tool names in llm-contract.md Tool Calling section.
14. If this app has a frontend UI (chat interface, dashboard): Create docs/architecture/frontend.md from templates/architecture/frontend.md.
15. If this app is deployed as a hosted service: Create docs/architecture/deployment.md from templates/architecture/deployment.md.
16. If this app stores conversation history or user data: Create docs/architecture/database.md from templates/architecture/database.md and docs/specs/data-model.md from templates/specs/data-model.md.
17. If this app exposes an external API: Create docs/specs/api-contract.md from templates/specs/api-contract.md.
18. If this app has multiple users with different roles: Create docs/specs/permissions.md from templates/specs/permissions.md.
19. If this app enforces domain-specific rules (e.g. content policy, output constraints): Create docs/business/business-rules.md from templates/business/business-rules.md.
20. Create docs/modules/module-data-flow.md from templates/modules/module-data-flow-v2.md.
21. Create docs/modules/module-flow.md from templates/modules/module-flow-v2.md.
22. Create docs/codebase-map.md from templates/codebase-map.md.
23. Create docs/project-plan.md from templates/project-plan.md.
24. Create docs/task-log.md from templates/task-log.md.
25. Create docs/sprint-change-log.md from templates/sprint-change-log.md.
26. Create docs/current-state.md from templates/current-state.md.

---

## Prompt Index Verification Rule

After creating or updating any prompt file under `docs/specs/prompts/`, you MUST:
1. Open `docs/specs/prompt-library.md`
2. Check the Active Prompts table
3. Verify the current prompt has a row with the correct current version
4. If the row is missing or the version is stale, update it before moving on

Do not assume the row exists. Do not rely on memory. Read the file and check.

---

## Quick Filter — AI / LLM Application

Only check these on every task:
- `llm-contract.md` — if system prompt, model, or parameters changed
- `prompt-library.md` + matching `prompts/[id]-prompt.md` — if a prompt was added or modified
- `eval-spec.md` — if test cases were added or eval criteria changed
- `eval-log.md` — append one row after every eval run (load this file only during eval tasks)
- `rag-contract.md` — if retrieval sources, chunking, or embedding model changed
- `mcp-contract.md` — if an MCP server is added/removed, a tool schema changes, or tool-use policy is tuned
- `research.md` — if a new model or provider was evaluated
