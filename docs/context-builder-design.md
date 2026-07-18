# Context Builder Design — build-context.py

Implements Phase 1 of `docs/refactoring-plan.md`. Replaces the multi-step AI startup inference with a deterministic script that produces `.ai/AI_CONTEXT.md`.

---

## Problem Statement

AI agents currently resolve required context by:
1. Reading `AGENTS.md` (~190 lines) to learn startup rules
2. Reading `docs/current-state.md` for the current task
3. Inferring which documents to load via the Quick filter guide in `templates/sprint-sync.md`

This costs tokens on every task startup and produces inconsistent results across AI tools. `build-context.py` makes the inference deterministic and tool-agnostic.

---

## Inputs

| Source | Field | Purpose |
|---|---|---|
| `.project-starter.yml` | `project_type` | Registry lookup → required documents |
| `.project-starter.yml` | `task_type` (new, optional) | Filter context to task-relevant documents |
| `docs/current-state.md` | `Task Type:` field (new, optional) | Override or supplement `task_type` from yml |
| `document-registry.yaml` | `context_priority`, `purpose`, `related` | Rank and annotate output |

### `task_type` values

| Value | Description | Documents prioritised |
|---|---|---|
| `feature` | New feature implementation | architecture.md, backend.md, data-model.md, api-contract.md |
| `pipeline-stage` | Data/ML pipeline stage | pipeline-contract.md, pipeline-debug.md, data-model.md |
| `bug-fix` | Bug investigation and fix | current-state.md, relevant module flow, debug guide |
| `sprint-end` | Sprint documentation sync | All required docs for type |
| `eval-run` | LLM evaluation run | eval-spec.md, eval-log.md, llm-contract.md |
| `iac-change` | Infrastructure change | topology.md, runbook.md, drift-policy.md |

If `task_type` is not declared, `build-context.py` falls back to listing all Required documents for the project type.

---

## Output Format — `.ai/AI_CONTEXT.md`

```markdown
# AI Context — {project_type} / {task_type}
Generated: {ISO-8601 timestamp}

## Read (Required)
- docs/current-state.md
- docs/specs/pipeline-contract.md   # Define cross-stage contracts
- docs/specs/data-model.md          # Schema reference
- docs/modules/sap-ingestion/sap-ingestion-module-data-flow.md

## Read (If Present)
- docs/specs/pipeline-debug.md      # Only if task involves debugging a stage failure

## Skip
- docs/changelog.md                 # Not needed for task work
- docs/specs/test-report.md         # Not needed for task work
- docs/architecture/frontend.md     # N/A for data-pipeline type
```

The AI reads the `Read (Required)` list on every startup. `Read (If Present)` items are conditional on the task description. `Skip` is explicit — prevents the AI from loading these "just in case."

---

## Document Selection Algorithm

```
1. Load document-registry.yaml
2. Resolve project_type from .project-starter.yml
3. For each document in registry:
   a. Compute R/O/N for this project_type:
        - type in required_for → R
        - type in optional_for → O
        - otherwise → N
   b. If N: → Skip
   c. If R: → Read (Required)
   d. If O: apply task_type filter:
        - task_type is relevant (heuristic match on purpose/related fields) → Read (If Present)
        - otherwise → Skip
4. Apply context_priority sort to Read (Required)
5. Inject current-state.md at top of Read (Required) always
6. Write .ai/AI_CONTEXT.md
```

---

## Registry Lookup Logic

`document-registry.yaml` schema per document entry:

```yaml
documents:
  pipeline-contract:
    file: pipeline-contract.md
    path: specs/pipeline-contract.md
    required_for: [data-pipeline, ml-pipeline]
    optional_for: []
    context_priority: high    # high / medium / low — affects sort order in AI_CONTEXT.md
    purpose: "Define cross-stage input/output contracts and error handling"
    used_by: [context-builder, validator, pdf]
    related: [pipeline-debug, data-model]
```

Required/Optional/N/A status is derived at runtime: a type in `required_for` → R, in `optional_for` → O, absent from both → N. There is no inline `types:` block or `flags:` subfield.

`context_priority` values:
- `high` — always near the top of the Read list; changes frequently during task work
- `medium` — relevant but stable; read once at task start
- `low` — reference only; read if specifically needed

---

## Token Reduction Estimate

| Current startup sequence | Lines loaded | Estimated tokens |
|---|---|---|
| AGENTS.md (full read) | ~190 | ~2 800 |
| current-state.md | ~60 | ~900 |
| Quick filter guide (sprint-sync.md extract) | ~40 | ~600 |
| **Total (current)** | **~290** | **~4 300** |

| Post-Phase-1 startup sequence | Lines loaded | Estimated tokens |
|---|---|---|
| `.ai/AI_CONTEXT.md` | ~20 | ~300 |
| current-state.md | ~60 | ~900 |
| AGENTS.md (simplified, ≤150 lines) | ~150 | ~2 200 |
| **Total (target)** | **~230** | **~3 400** |

**Estimated saving: ~900 tokens per task startup (~20%).** The larger gain is consistency — deterministic context means fewer wasted tool calls from the AI re-reading the wrong documents.

---

## Usage

```bash
# Generate context for the current task:
python3 build-context.py

# Override task type:
python3 build-context.py --task-type sprint-end

# Preview without writing:
python3 build-context.py --dry-run
```

`.ai/` is added to `.gitignore` — generated context is not committed.

---

## Key Decisions

| Decision | Rationale |
|---|---|
| Task type is declared, not inferred | Avoids AI inference complexity; any tool (Claude, Codex, Cursor, manual) can run `build-context.py` |
| Output goes to `.ai/AI_CONTEXT.md` | No MCP / plugin required in v1; AI reads it as a plain file |
| No folder restructuring in Phase 1 | Folder renames touch every script path reference; the context builder value is independent of folder layout |
| Registry schema includes `purpose` and `related` | Context builder needs to know *why* a document is read and what else to suggest — not just whether it is required |
