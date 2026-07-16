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

## Phase 2 — Per-Type Document Update Checklist ✅ Complete

The Document Update Checklist in sprint-sync.md lists all documents. When a project declares itself as CLI or Library, many checklist items are not applicable, but the agent still has to read and skip them.

**Goal:** Gate checklist items by project type so agents only evaluate relevant items.

### Done

| Change | Effect |
|---|---|
| Added project-type skip table at the top of the checklist in `sprint-sync.md` | Agents look up their type once and skip non-applicable groups entirely |
| Tagged all 34 checklist items with `[Types: ...]` | Every item is scannable without reading its full trigger condition |
| `[Types: All]` sentinel for universal items | Avoids enumerating 7 types for items that always apply |
| Mixed / Hybrid type instruction in the skip table | Hybrid projects take the union without loading extra files |

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

## Phase 4 — scan_codebase.py per-type awareness ✅ Complete

`scan_codebase.py` previously identified all modules as Feature / Background Job / Shared — a Web App–centric classification that produced misleading output for pipeline and library projects.

**Goal:** Accept a `--project-type` flag so the scanner applies the right module boundary detection heuristic per type.

### Done

| Change | Effect |
|---|---|
| `--project-type` flag added (7 valid values matching AGENTS.md types) | Scanner applies the correct boundary heuristic without guessing |
| `PIPELINE_STAGE_PATTERNS` constant | 30+ canonical stage names (extract, validate, transform, train, evaluate, serve, …) used to classify folders in Data Pipeline / ML Pipeline projects |
| `MODULE_VOCAB` per-type vocabulary table | Singular + plural label per type — report says "pipeline stages" not "feature modules" for pipeline projects |
| `guess_type(name, project_type)` — per-type branching | data-pipeline/ml-pipeline → Pipeline Stage; cli-tool → Command; library → Namespace; microservices → Service; web-app/llm-app → Feature / Background Job (unchanged) |
| Coverage report header and summary line use `plural_label` | `=== Pipeline Stages Coverage Report ===`, `3/4 pipeline stages documented` |
| Numbered stage prefix stripping (`01_extract` → `extract`) | Numbered pipeline layouts are classified correctly |
| `None` (no flag) falls back to web-app behaviour | Zero breaking change for existing callers |

---

## Phase 5 — Token load optimization ✅ Complete

AI agents load AGENTS.md on every task setup. As the framework grows, this cost compounds.

### Done

| Change | Saving |
|---|---|
| Extract document matrix → `init/document-matrix.md` | 33 lines removed from every AGENTS.md load |
| Extract retrofit procedure → `init/retrofit.md` | 88 lines removed from every AGENTS.md load |
| Fix stale Doc Checklist reference (pointed to AGENTS.md; checklist was in sprint-sync.md) | Eliminates double-file load on every task setup |
| Current-state.md template: inline quick-filter guide covers standard task types without loading sprint-sync.md | Most task setups need zero extra file loads |
| Fix stale references in README.md and document-purposes.md (document-matrix location, retrofit location, Doc Checklist source) | Prevents agents following incorrect file-load paths |
| Per-type sprint-sync checklist (Phase 2): type filter table + `[Types: ...]` tags on all checklist items | CLI project sprint sync skips LLM/ML items without reading them |
| Split `document-purposes.md` (822 lines) into `document-purposes-common.md` + 7 per-type files | CLI project loads ~330 lines instead of 822; Web App loads ~450 instead of 822 |
| `document-purposes.md` converted to a short index (type → file lookup table) | Agents never load the full monolith — always load only what applies |
| Updated `AGENTS.md` reference to point to common + per-type files | Reference path is correct; no stale pointers |

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

## Phase 7 — Event-Driven / Messaging Support (future)

`api-contract.md` records REST endpoints and WebSocket events, but cannot express the publisher/subscriber contracts, schema evolution rules, and dead-letter handling that event-driven architectures need. This gap is most acute for Microservices projects that communicate via Kafka, RabbitMQ, or similar brokers.

**Goal:** Add `event-catalog.md` as the canonical source for all event schemas — decoupled from `service-contract.md` (which covers synchronous REST between services) and from `api-contract.md` (which covers client-facing APIs).

### Planned changes

| File | Change |
|---|---|
| `specs/event-catalog.md` | New template: event name, payload schema, publisher, subscriber(s), version, retention, dead-letter policy — one table row per event type |
| `init/document-matrix.md` | Add `event-catalog.md`: Required for Event-Driven Microservices, Optional for standard Microservices |
| `init/microservices.md` | Add conditional step: "If the system uses async messaging, create `event-catalog.md`" |
| `docs/templates/sprint-sync.md` | Add checklist item: `docs/specs/event-catalog.md [Types: Microservices]` |
| `document-purposes-microservices.md` | Add `event-catalog.md` entry: purpose, update triggers |

Note: Event-Driven is treated as a variant of Microservices (not a new top-level type) because it shares all the same architecture and spec documents; only the inter-service communication pattern differs.

---

## Phase 8 — Mobile App type (future)

`frontend.md` assumes a web page structure (components, routes, API hooks). Native mobile has no pages in the web sense — it has screens, navigation stacks, OS permissions, and app-store distribution rather than server deployment. All existing templates apply to the logic layer but the frontend and deployment templates need mobile variants.

**Goal:** Add `Mobile App` as a supported project type with mobile-specific frontend and distribution templates.

### Planned changes

| File | Change |
|---|---|
| `AGENTS.md` | Add `Mobile App` to the supported types table |
| `init/mobile-app.md` | New init file: step-by-step setup sequence for a Mobile App project |
| `specs/mobile-contract.md` | New template: screen inventory, navigation graph, deep-link scheme, OS permission declarations, push notification payloads |
| `architecture/frontend.md` | Add `## Mobile App` variant section: screen-based structure, navigation pattern, state management strategy, platform differences (iOS/Android) |
| `architecture/distribution.md` | Add `## Mobile App` variant: build pipeline, signing, App Store / Google Play submission checklist, version naming |
| `init/document-matrix.md` | Add `mobile-contract.md` row; mark `frontend.md` and `distribution.md` as Required for Mobile App |
| `document-purposes.md` index | Add `document-purposes-mobile-app.md` entry |
| `document-purposes-mobile-app.md` | New per-type file: mobile-contract.md, frontend.md (mobile variant), distribution.md (app store variant) |
| `docs/templates/sprint-sync.md` | Add checklist item: `docs/specs/mobile-contract.md [Types: Mobile App]` |

---

## Phase 9 — IaC / DevOps type (future)

Infrastructure-as-Code projects (Terraform, Pulumi, Ansible, Helm charts) have almost no overlap with the existing document set. There are no modules in the feature sense, no API contracts, no business objects, and no frontend. The primary artefacts are resource topology, environment diff policy, and operational runbooks.

**Goal:** Add `IaC / DevOps` as a project type with a minimal dedicated template set. Mark all inapplicable existing documents as N/A so agents don't create empty placeholders.

### Planned changes

| File | Change |
|---|---|
| `AGENTS.md` | Add `IaC / DevOps` to the supported types table |
| `init/iac.md` | New init file: step-by-step setup for an IaC project (topology, runbook, drift policy, secrets policy) |
| `specs/runbook.md` | New template: incident response steps per resource type, rollback procedure, health check commands |
| `specs/drift-policy.md` | New template: allowed drift sources, detection cadence, remediation SLA, approval gate for manual changes |
| `architecture/topology.md` | New template: resource graph (regions, VPCs, subnets, services), environment promotion path (dev → staging → prod) |
| `init/document-matrix.md` | Add three new rows; mark all existing spec/architecture/business docs as N/A for IaC / DevOps |
| `document-purposes.md` index | Add `document-purposes-iac.md` entry |
| `document-purposes-iac.md` | New per-type file: topology.md, runbook.md, drift-policy.md |
| `docs/templates/sprint-sync.md` | Add checklist items `[Types: IaC / DevOps]` for the three new docs |
| `scan_codebase.py` | Add `iac` to `VALID_PROJECT_TYPES`; classify `.tf`, `.yaml`, `modules/` as Resource Groups rather than Feature modules |

---

## Phase 10 — Further token load optimization (future)

Phase 5 eliminated most redundant file loads during normal task work. The remaining cost centres are in `AGENTS.md` itself: two large sections — Module Completion Check (~40 lines) and Task Completion (~50 lines) — are loaded on every task startup even though Module Completion is only needed when a module finishes, and Task Completion steps are already summarised in `current-state.md`.

**Goal:** Extract these two sections from `AGENTS.md` into separate load-on-demand files, reducing the mandatory startup payload.

### Planned changes

| File | Change |
|---|---|
| `templates/module-completion.md` | New file: full Module Completion Check procedure extracted from `AGENTS.md`; load only when a module is confirmed 100% complete |
| `templates/task-completion.md` | New file: mandatory post-task steps (Doc Checklist, verification table, sprint-change-log entry, task-log row) extracted from `AGENTS.md`; referenced via a single pointer line in current-state.md |
| `AGENTS.md` | Replace extracted sections with single-line load instructions: "Load `templates/module-completion.md` when module is complete" / "Load `templates/task-completion.md` at task closeout" |
| `current-state.md` template | Add inline closeout checklist summary (4 bullet points) so most task closeouts need zero extra file reads |
| `document-purposes-common.md` | Add entries for the two new template files |

Estimated saving: ~90 lines removed from every `AGENTS.md` load.

---

## Phase 11 — scan_codebase.py improvements (future)

`scan_codebase.py` currently scans one level deep (immediate subdirectories of `src_dir`) and classifies by folder name only. This misses monorepo layouts where each service has its own nested `src/`, and gives no way to auto-scaffold documentation stubs for newly discovered modules.

**Goal:** Support nested discovery, add JSON output for agent consumption, and add a `--scaffold` flag to generate documentation stubs.

### Planned changes

| Change | Effect |
|---|---|
| `--depth N` flag | Scan N levels deep — supports monorepos and Microservices with per-service `src/` folders |
| `--format json` output mode | Machine-readable output for agents that need to programmatically process coverage results without parsing text |
| `--scaffold` flag | Auto-generate stub `[module]-module-data-flow.md` files under `docs/modules/[module]/` for all undocumented modules (agent fills in content); does not overwrite existing files |
| Content peek for pipeline confidence | If a directory contains `*_stage.py`, `step_*.py`, or `run_*.py`, boost Pipeline Stage classification confidence — shown as `Pipeline Stage (detected)` vs `Pipeline Stage (inferred)` |
| `iac` project type support | See Phase 9 |

---

## Phase 12 — Document completeness audit script — verify_docs.py (future)

There is currently no automated way to check whether a project of a given type has created all its Required documents. An agent retrofitting a Data Pipeline project could skip `pipeline-debug.md` without any warning — the gap would only surface during a manual review.

**Goal:** A script that cross-references the declared project type against the document matrix and reports missing Required and Optional documents in `docs/`.

### Planned changes

| File | Change |
|---|---|
| `docs/script/verify_docs.py` | New script — see spec below |
| `README.md` | Document `verify_docs.py` usage alongside `scan_codebase.py` |
| `document-purposes-common.md` | Add `verify_docs.py` entry under Scripts section |

**`verify_docs.py` spec:**

```
Usage:
  python3 docs/script/verify_docs.py --project-type TYPE
  python3 docs/script/verify_docs.py --project-type TYPE --docs PATH
  python3 docs/script/verify_docs.py --project-type TYPE --json

Options:
  --project-type TYPE   Declared project type (same values as scan_codebase.py)
  --docs PATH           Path to docs/ directory (default: docs)
  --strict              Exit with code 1 if any Required document is missing
  --json                Output results as JSON for agent consumption
```

**Output per document:**

| Status | Meaning |
|---|---|
| ✅ Present | File exists in docs/ |
| ❌ Missing Required | File is Required for this type and does not exist |
| ⚠️ Missing Optional | File is Optional for this type and does not exist |
| — N/A | File is not applicable for this type |
| 🔍 Orphan | File exists in docs/ but is not in the matrix for this type |

**Hybrid type support:** `--project-type data-pipeline+web-app` runs the union of both type matrices.

The script reads the required/optional/N/A mapping from a hardcoded matrix in the script itself (derived from `document-matrix.md` at implementation time) so it has no runtime dependency on the template files — it works in any project that copied this framework's scripts.
