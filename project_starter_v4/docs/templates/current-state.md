# Current State

<!--
  EXECUTION RULES — read before starting any task:
  1. Every blocking command must be wrapped with timeout:
     timeout 120 bash -c '...' && echo "✅ done" || echo "❌ timed out"
  2. If any operation has been running for more than 5 minutes without a clear
     success signal — stop, report what you were doing and the last known output,
     and wait for instruction. Do not keep waiting or trying new things silently.
-->

## Current Task

**Task:** [Task name, e.g., BE Order API]

**Goal:** [What this task needs to achieve]

**Status:** In Progress
<!-- When done: "Complete — Pending Sprint Doc Sync" -->

---

## Required Context

<!--
  Only include documents actually needed for this task.
  Do not include project-requirements.md, project-plan.md, or changelog.md
  unless this task explicitly requires them.
-->

* `docs/[relevant file]`
* `[other required file paths]`

---

## Steps

- [ ] **Step 1: [Step name]**
  [Description]
  Expected: [expected result]

- [ ] **Step 2: [Step name]**
  [Description]
  Expected: [expected result]

- [ ] **Verify**
  Run: `[exact command]`
  Expected: `[exact output or behaviour]`
  Do not mark this task complete until the expected output is confirmed.

---

## Next Task

<!--
  Fill this in when the current task is created (copied from project-plan.md once).
  When the current task completes, this becomes the new Current Task — no need to re-read project-plan.md.
  If unknown, write: "See project-plan.md"
-->

**Task:** [Next task name]
**Goal:** [What the next task needs to achieve]
**Required Context:** [Files the next task will need]

---

## Doc Checklist (this task only)

<!--
  WHEN TO FILL: when this task is first set up — not at closeout.
  HOW TO FILL: use the quick filter guide below to identify which docs need updating.
  For task types not listed below, load `templates/sprint-sync.md → Document Update Checklist`.
  Do not load AGENTS.md for this — the guide below covers all standard task types.
  - DB schema task          → keep: data-model.md, database.md, business-objects.md
  - BE endpoint task        → keep: api-contract.md, permissions.md, module-data-flow.md, module-flow.md, logging-spec.md
  - FE task                 → keep: frontend.md, codebase-map.md (page structure)
  - Config/infra task       → keep: deployment.md, quickstart.md
  - Business logic task     → keep: business-rules.md, business-process.md, business-objects.md
  - Script/utility task     → keep: nothing (doc updates usually not needed)
  - Prompt / LLM task       → keep: llm-contract.md, prompt-library.md + prompts/[id]-prompt.md, eval-spec.md
  - Eval run task           → keep: eval-log.md (append one row), eval-spec.md (if criteria changed)
  - RAG task                → keep: rag-contract.md, llm-contract.md (Context Window Strategy)
  - MCP server task         → keep: mcp-contract.md, llm-contract.md (Tool Calling section)
  - Pipeline stage task     → keep: pipeline-contract.md, module-data-flow.md
  - ML model task           → keep: model-contract.md, experiment-log.md

  WHEN TO RUN: at task completion (Task Completion step 1a).
  Apply each item listed here — do NOT re-open AGENTS.md at closeout.
-->

- [ ] `docs/[relevant spec]` — [what to check / update]
- [ ] `docs/[relevant spec]` — [what to check / update]
<!-- Add or remove lines. At task completion, run only what is listed here. -->

---

## Notes

* [Implementation decisions, rationale, or issues encountered]
