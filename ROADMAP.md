# project_starter_v4 — Roadmap

## Vision

project_starter_v4 started as a Web App framework. This roadmap tracks the expansion to support all major software project types so the same AI-agent workflow can be applied to any project without producing empty or irrelevant documents.

---

## Phase 1 — Multi-Type Foundation ✅ Complete

**Goal:** Add Project Type declaration to AGENTS.md so AI agents know which documents are required vs N/A. Introduce Pipeline Stage module type. Create templates for all new project types.

### Framework changes

| File | Change |
|---|---|
| `AGENTS.md` | Add `## Project Type` section — type declaration, document matrix, per-type initialization sequences |
| `docs/templates/flows/module-data-flow-v2.md` | Add **Pipeline Stage** as 4th module type (Format D) |
| `document-purposes.md` | Add entries for all new template documents |
| `docs/templates/specs/logging-spec.md` | Add **Request Tracing** section — trace_id generation, propagation rules, log format; applies to all entry points (HTTP, pipeline trigger, LLM call, job start) |

### New templates

| Template | For project type | Replaces / supplements |
|---|---|---|
| `specs/pipeline-contract.md` | Data Pipeline, ML Pipeline | `api-contract.md` |
| `specs/cli-contract.md` | CLI Tool | `api-contract.md` |
| `specs/public-api.md` | Library / SDK | `api-contract.md` |
| `specs/model-contract.md` | ML Pipeline | — |
| `specs/experiment-log.md` | ML Pipeline | `sprint-change-log.md` (per experiment) |
| `specs/service-catalog.md` | Microservices | — |
| `specs/service-contract.md` | Microservices | `api-contract.md` (inter-service) |
| `specs/release-guide.md` | Library / SDK, CLI Tool | `deployment.md` |
| `specs/compatibility-matrix.md` | Library / SDK, CLI Tool | — |
| `architecture/distribution.md` | Library / SDK, CLI Tool | `deployment.md` |
| `specs/pipeline-debug.md` | Data Pipeline, ML Pipeline | — (debug guide: stage failure → root cause) |
| `specs/llm-debug.md` | AI / LLM Application | — (debug guide: retriever → prompt → tool → eval → API) |

### Init file completeness fixes

All 7 init files verified against `document-matrix.md`. Gaps fixed:

| Init file | Fix |
|---|---|
| `web-app.md` | Unbundle step 5 into 4 explicit steps; `frontend.md` made conditional |
| `cli-tool.md` | Add conditional steps for `database.md`, `data-model.md`, `compatibility-matrix.md` |
| `data-pipeline.md` | Add conditional step for `business-process.md` |
| `ml-pipeline.md` | Add `pipeline-debug.md` (was Required but missing) |
| `microservices.md` | Explicit "load `templates/init/web-app.md`" instruction; add template paths to system-level steps |
| `llm-app.md` | Add conditional steps for `frontend.md`, `deployment.md`, `database.md`, `data-model.md`, `api-contract.md`, `permissions.md`, `business-rules.md` |

---

## Phase 2 — Per-Type Document Update Checklist (future)

The Document Update Checklist in sprint-sync.md lists all documents. When a project declares itself as CLI or Library, many checklist items are not applicable, but the agent still has to read and skip them.

**Goal:** Gate checklist items by project type so agents only evaluate relevant items.

Approach options:
- Tag each checklist item with applicable project types (e.g., `[Web App, Microservices]`)
- Split into per-type checklists (higher maintenance cost)

---

## Phase 3 — Per-Type Code Quality Check ✅ Complete

`code-quality-check.md` previously assumed a layered Web App architecture. Per-type variants have now been added for all remaining project types.

### Done

| Area | What was added |
|---|---|
| **Layering** | Type-aware table (Web App / CLI / Library / Data Pipeline / ML Pipeline / Microservices / AI LLM App) — completed in Phase 1 |
| **Observability** | New area added: trace_id propagation (all types), LLM call structured log (AI/LLM only), pipeline stage row count logging (Data Pipeline / ML Pipeline only) — type-aware enforcement via project-type table |
| **CLI Tool** | Flag parsing isolation, command responsibility separation, exit code consistency — added under `## Type-Specific Checks` |
| **Library / SDK** | No side effects at import, public API stability, test coverage of public surface — added under `## Type-Specific Checks` |
| **Data Pipeline** | Inter-stage contract verification, idempotency, archive/replay guarantees — added under `## Type-Specific Checks` |
| **ML Pipeline** | Data leakage checks, train/test split integrity, metric reproducibility — added under `## Type-Specific Checks` |
| **Microservices** | Service contract conformance, circuit breaker coverage, distributed tracing — added under `## Type-Specific Checks` |

---

## Phase 4 — scan_codebase.py per-type awareness (future)

`scan_codebase.py` currently identifies modules by folder structure. For pipeline and ML projects, "modules" are stages, not folders. For libraries, they are namespaces.

**Goal:** Accept a `--project-type` flag so the scanner applies the right module boundary detection heuristic per type.

---

## Phase 5 — Token load optimization (in progress)

AI agents load AGENTS.md on every task setup. As the framework grows, this cost compounds.

### Done

| Change | Saving |
|---|---|
| Extract document matrix → `init/document-matrix.md` | 33 lines removed from every AGENTS.md load |
| Extract retrofit procedure → `init/retrofit.md` | 88 lines removed from every AGENTS.md load |
| Fix stale Doc Checklist reference (pointed to AGENTS.md; checklist was in sprint-sync.md) | Eliminates double-file load on every task setup |
| Current-state.md template: inline quick-filter guide covers standard task types without loading sprint-sync.md | Most task setups need zero extra file loads |
| Fix stale references in README.md and document-purposes.md (document-matrix location, retrofit location, Doc Checklist source) | Prevents agents following incorrect file-load paths |

### Still needed

- Per-type sprint-sync checklist (links to Phase 2): agents running sprint sync on a CLI project still read LLM and ML items before skipping them
- `document-purposes.md` (800 lines) is the largest file; loaded only as reference but expensive when it is needed — consider splitting into per-type reference files

---

## Phase 6 — UML Diagram Coverage ✅ Complete

**Goal:** Ensure every PDF-included template that benefits from a diagram actually has one, and that existing diagram templates don't produce misleading output for certain project types.

### New diagrams added

| Template | Diagram type | For project type |
|---|---|---|
| `specs/pipeline-contract.md` | Sequence — Extract → Validate → Transform → Load with data contract annotations at each boundary | Data Pipeline, ML Pipeline |
| `specs/rag-contract.md` | Sequence — Query Transformer → Embedding Model → Vector Store → Post-Retrieval Filter → Prompt Builder → LLM → User | AI / LLM Application |

These were the only PDF-included templates without plantuml blocks. Both are auto-picked up by `build_pdf.py` for their respective project types.

### Existing diagram fixes

| Template | Fix |
|---|---|
| `architecture/architecture.md` (System Component Structure) | Added project-type comments — agents now know to remove the Frontend package for Data Pipeline / CLI Tool / ML Pipeline projects instead of generating an inapplicable web-app layout |
| `flows/module-flow-v2.md` | Added `alt success / else error` block to the sequence diagram example — agents now document error branches, not just the happy path |
| `flows/module-data-flow-v2.md` (Pipeline Stage class diagram) | Added `note` linking `InputType / OutputType` to `pipeline-contract.md` — keeps the class structure and data contract in sync |

---

## Known gaps (not yet scheduled)

- Mobile App: `frontend.md` does not cover native mobile structure (no web page, different deployment model)
- IaC / DevOps: Nearly all documents are inapplicable; dedicated IaC template set needed
- Event-Driven / Messaging: `api-contract.md` cannot express event schemas; a separate `event-catalog.md` template is needed (related to Microservices type but distinct)
