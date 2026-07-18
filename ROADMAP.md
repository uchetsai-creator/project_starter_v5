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
| `templates/flows/module-data-flow-v2.md` | Add **Pipeline Stage** as 4th module type (Format D) |
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

## Phase 7 — Event-Driven / Messaging Support ✅ Complete

`api-contract.md` records REST endpoints and WebSocket events, but cannot express the publisher/subscriber contracts, schema evolution rules, and dead-letter handling that event-driven architectures need. This gap is most acute for Microservices projects that communicate via Kafka, RabbitMQ, or similar brokers.

**Goal:** Add `event-catalog.md` as the canonical source for all event schemas — decoupled from `service-contract.md` (which covers synchronous REST between services) and from `api-contract.md` (which covers client-facing APIs).

### Done

| File | Change |
|---|---|
| `specs/event-catalog.md` | New template: event inventory table, per-event payload schema + example JSON, retention/dead-letter policy, schema evolution rules, PlantUML pub-sub sequence diagram, cross-service consistency rules |
| `init/document-matrix.md` | Added `event-catalog.md`: Optional (⚠️) for Microservices, N/A for all other types |
| `init/microservices.md` | Added conditional Step 5: create event-catalog.md when system uses async messaging |
| `docs/templates/sprint-sync.md` | Added checklist item for `docs/specs/event-catalog.md [Types: Microservices]`; clarified service-contract.md item to not duplicate async schemas |
| `document-purposes-microservices.md` | Added `event-catalog.md` entry with purpose, load guidance, and update triggers; updated service-contract.md description to reflect sync-only scope |
| `docs/templates/script/verify_docs.py` | Added `event-catalog.md` to MATRIX (O for Microservices) and FILE_LOCATIONS |

**Token impact:** zero — AGENTS.md unchanged. All additions are in load-on-demand files (init, sprint-sync, document-purposes).

Note: Event-Driven is treated as a variant of Microservices (not a new top-level type) because it shares all the same architecture and spec documents; only the inter-service communication pattern differs.

---

## Phase 8 — Mobile App type ✅ Complete

`frontend.md` assumes a web page structure (components, routes, API hooks). Native mobile has no pages in the web sense — it has screens, navigation stacks, OS permissions, and app-store distribution rather than server deployment. All existing templates apply to the logic layer but the frontend and deployment templates need mobile variants.

**Goal:** Add `Mobile App` as a supported project type with mobile-specific frontend and distribution templates.

### Done

| File | Change |
|---|---|
| `AGENTS.md` | Added `Mobile App` row to supported types table and init file table |
| `init/mobile-app.md` | New init file: 10-step setup (requirements → architecture → frontend → mobile-contract → distribution → quickstart → logging → conditional docs → scan → verify) |
| `specs/mobile-contract.md` | New template: app identity, screen inventory, navigation graph, deep-link scheme, OS permission declarations, push notification payloads, App Store / Play Store metadata |
| `architecture/frontend.md` | Added `## Mobile App Variant` section: platform/framework table, screen structure, component/widget strategy, platform-specific adaptations (iOS vs Android) |
| `architecture/distribution.md` | Added `## Mobile App Variant` section: app identity, build pipeline, signing config (iOS certs + Android keystore), release checklist, CI/CD pipeline |
| `init/document-matrix.md` | Added Mobile App column (10th); added `mobile-contract.md` row (✅ Mobile App only) |
| `document-purposes.md` | Added `Mobile App → document-purposes-mobile-app.md` entry |
| `document-purposes-mobile-app.md` | New per-type file: mobile-contract.md, distribution.md (mobile section), compatibility-matrix.md, frontend.md (mobile section), architecture.md note, logging-spec.md note |
| `sprint-sync.md` | Added Mobile App row to type filter; added quick-filter row; added `mobile-contract.md` checklist item `[Types: Mobile App]` |
| `scan_codebase.py` | Added `mobile-app` to `MODULE_VOCAB` ("Screen"); `guess_type()` classifies navigation/components/widgets as Shared, else Screen |
| `verify_docs.py` | Added `mobile-app` to `VALID_TYPES`; extended all MATRIX tuples to 9 columns; added `mobile-contract.md` row |

**Token discipline:** 2 lines added to AGENTS.md (one type row + one init table row) — 197 lines total, within 200-line budget. All detail in load-on-demand files.

**verify_framework.py result after implementation:** all 6 checks ✅ pass.

---

## Phase 9 — IaC / DevOps type ✅ Complete

Infrastructure-as-Code projects (Terraform, Pulumi, Ansible, Helm charts) have almost no overlap with the existing document set. There are no modules in the feature sense, no API contracts, no business objects, and no frontend. The primary artefacts are resource topology, environment diff policy, and operational runbooks.

**Goal:** Add `IaC / DevOps` as a project type with a minimal dedicated template set. Mark all inapplicable existing documents as N/A so agents don't create empty placeholders.

### Done

| File | Change |
|---|---|
| `AGENTS.md` | Added `IaC / DevOps` row to supported types table and init file table |
| `init/iac.md` | New init file: 8-step IaC setup (topology, runbook, drift-policy, secrets, quickstart) |
| `specs/runbook.md` | New template: on-call escalation, per-resource-type incident response, rollback, common Terraform ops |
| `specs/drift-policy.md` | New template: drift scope, allowed sources, detection cadence, remediation SLA, approval gate |
| `architecture/topology.md` | New template: resource inventory, environment promotion path, PlantUML network diagram, secrets sources |
| `init/document-matrix.md` | Added IaC / DevOps column (9th); added topology.md / runbook.md / drift-policy.md rows |
| `document-purposes.md` | Added `IaC / DevOps → document-purposes-iac.md` entry |
| `document-purposes-iac.md` | New per-type file: topology.md, runbook.md, drift-policy.md with update triggers |
| `sprint-sync.md` | Added IaC row to type filter; added quick-filter row; added 3 checklist items `[Types: IaC / DevOps]` |
| `scan_codebase.py` | Added `iac` to `MODULE_VOCAB`; IaC branch in `guess_type()`: `modules/`/`.terraform` → Shared, else Resource Group |
| `verify_docs.py` | Added `iac` to `VALID_TYPES`; extended all MATRIX tuples to 8 columns; added topology/runbook/drift-policy rows |

**Token discipline:** 0 lines added to AGENTS.md beyond the two pointer rows (init table + supported types). All detail lives in load-on-demand files.

---

## Phase 10 — Further token load optimization ✅ Complete

Phase 5 eliminated most redundant file loads during normal task work. The remaining cost centres are in `AGENTS.md` itself: two large sections — Module Completion Check (~40 lines) and Task Completion (~50 lines) — are loaded on every task startup even though Module Completion is only needed when a module finishes, and Task Completion steps are already summarised in `current-state.md`.

**Goal:** Extract these two sections from `AGENTS.md` into separate load-on-demand files, reducing the mandatory startup payload.

### Done

| File | Change |
|---|---|
| `templates/module-completion.md` | New file: full Module Completion Check procedure extracted from `AGENTS.md`; load only when a module is confirmed 100% complete |
| `templates/task-completion.md` | New file: mandatory post-task steps (Doc Checklist, verification table, sprint-change-log entry, task-log row) extracted from `AGENTS.md`; referenced via a single pointer line in current-state.md |
| `AGENTS.md` | Replaced Module Completion Check (~40 lines) and Task Completion (~50 lines) with single-line load pointers; updated "closing out" reference to point to Closeout section in current-state.md |
| `docs/templates/current-state.md` | Added inline **Closeout** section (4 bullet points) so standard closeouts need zero extra file loads |
| `document-purposes-common.md` | Added entries for `module-completion.md` and `task-completion.md` |

Saving: ~90 lines removed from every `AGENTS.md` load.

**Token discipline going forward:** every subsequent Phase follows this pattern — AGENTS.md receives only a pointer line; detail lives in a dedicated load-on-demand file.

---

## Phase 11 — scan_codebase.py improvements ✅ Complete

`scan_codebase.py` currently scans one level deep (immediate subdirectories of `src_dir`) and classifies by folder name only. This misses monorepo layouts where each service has its own nested `src/`, and gives no way to auto-scaffold documentation stubs for newly discovered modules.

**Goal:** Support nested discovery, add JSON output for agent consumption, and add a `--scaffold` flag to generate documentation stubs.

### Done

| Change | Effect |
|---|---|
| `--depth N` flag | Scan N levels deep — supports monorepos and Microservices with per-service `src/` folders; default 1 preserves existing behaviour |
| `--format json` output mode | Machine-readable output including per-module type/status/flow_file and a coverage summary object; agents parse this without text scraping |
| `--scaffold` flag | Auto-generates stub `[module]-module-data-flow.md` files under `docs/modules/[module]/` for all undocumented modules; skips existing files (idempotent) |
| Content peek for pipeline confidence | Directories containing `*_stage.py`, `step_*.py`, or `run_*.py` are labelled `Pipeline Stage (detected)`; others are `Pipeline Stage` (name-matched) or `Pipeline Stage (inferred)` |
| `iac` project type support | Deferred — will be added as part of Phase 9 completion |

**Token impact:** zero — script only; no AGENTS.md changes. `document-purposes-common.md` entry is load-on-demand reference.

---

## Phase 12 — Document completeness audit script — verify_docs.py ✅ Complete

There is currently no automated way to check whether a project of a given type has created all its Required documents. An agent retrofitting a Data Pipeline project could skip `pipeline-debug.md` without any warning — the gap would only surface during a manual review.

**Goal:** A script that cross-references the declared project type against the document matrix and reports missing Required and Optional documents in `docs/`.

### Done

| File | Change |
|---|---|
| `docs/script/verify_docs.py` | New script — see spec below |
| `README.md` | Added "Document completeness audit" section with usage examples and output status table |
| `document-purposes-common.md` | Added `verify_docs.py` entry under Scripts section |

**Token impact:** zero — script is not referenced in AGENTS.md; entry in document-purposes-common.md is load-on-demand reference only.

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

---

## Phase 13 — Framework Integrity Audit: verify_framework.py ✅ Complete

As the framework grows across phases, file references, document-matrix entries, sprint-sync checklist items,
and load-on-demand pointers in AGENTS.md can drift out of sync. There is currently no automated way to
detect a stale pointer, a matrix row without a matching template file, or a checklist item for a document
that no longer exists. The "token discipline" principle from Phase 10 also needs enforcement — without a
check, AGENTS.md can quietly grow back.

**Goal:** A script that audits the framework's own internal consistency — cross-checking pointers, matrix,
checklist, and token budget so that each new Phase ships with confidence that nothing was broken.
Run at the end of every Phase before merging.

### Done

| File | Change |
|---|---|
| `docs/templates/script/verify_framework.py` | New script — 6 checks, `--strict` CI gate, `--json` output |
| `README.md` | Added "Framework maintenance" section with usage and check table |
| `document-purposes-common.md` | Added `verify_framework.py` entry under Scripts section |
| `docs/templates/sprint-sync.md` | Added missing `eval-spec.md` checklist item `[Types: AI / LLM App]` (surfaced by the audit) |

**Checks implemented:**

| Check | What it verifies |
|---|---|
| Stale pointer | Every `.md` reference in AGENTS.md resolves to an existing file in the framework |
| Token budget | AGENTS.md is ≤ 200 lines |
| Matrix ↔ template | Every matrix row has a template file; every template has a matrix row (exempt: supplementary templates) |
| Sprint-sync coverage | Every non-exempt R/O document has a sprint-sync checklist item |
| Purposes coverage | Every Required document appears in the matching document-purposes file (Required-only — Optional docs may live in a sibling type file) |
| Cross-reference integrity | Every `### X.md` section header in document-purposes-*.md has a corresponding template file |

**Audit result after implementation:** all 6 checks ✅ pass.

**Token discipline:** 0 lines added to AGENTS.md. All detail lives in the script file and README.

Note: Phase 13 is designed to be run after every other Phase completes, not just once.

---

## Phase 14 — Framework Correctness Audit ✅ Complete

Running `verify_framework.py` and a full cross-file review after Phase 9 (IaC) and Phase 8 (Mobile App) surfaced a cluster of consistency gaps: init files pointing to a directory that was renamed, a new document missing from the matrix, a broken script reference in a process template, an ASCII-art diagram where a rendered plantuml block should be, and the PDF builder lacking entries for two newly-added project types.

**Goal:** Bring all framework files into agreement — no stale paths, no matrix gaps, no broken script references, no missing PDF entries.

### Init file path fix (Bug 1)

The `flows/` directory (formerly `modules/`) was renamed in Phase 1, but 7 init files still referenced the old path.

| Init file | Fix |
|---|---|
| `init/web-app.md` | `templates/modules/module-data-flow-v2.md` → `templates/flows/module-data-flow-v2.md`; same for `module-flow-v2.md` |
| `init/cli-tool.md` | Same path correction (both flow templates) |
| `init/library.md` | Same path correction |
| `init/data-pipeline.md` | Same path correction |
| `init/ml-pipeline.md` | Same path correction |
| `init/llm-app.md` | Same path correction |
| `init/retrofit.md` | Same path correction in Step 3 |

### eval-log.md missing from document matrix (Bug 2)

`init/llm-app.md` Step 9 instructed agents to create `eval-log.md`, but the file had no row in `document-matrix.md` or `verify_docs.py`, and was listed in `verify_framework.py`'s `TEMPLATE_MATRIX_EXEMPT` set (which exempted it from the matrix check rather than fixing the omission).

| File | Fix |
|---|---|
| `init/document-matrix.md` | Added `eval-log.md` row: ✅ for AI / LLM App, ❌ for all other types |
| `docs/templates/script/verify_docs.py` | Added `eval-log.md` to `MATRIX` (`'R'` for llm-app, `'N'` for all others) and `FILE_LOCATIONS` |
| `docs/templates/script/verify_framework.py` | Removed `specs/eval-log.md` from `TEMPLATE_MATRIX_EXEMPT` (no longer exempt — now in matrix) |

### UML completeness fixes

| Template | Problem | Fix |
|---|---|---|
| `specs/mobile-contract.md` | Navigation Graph section used an ASCII-art tree — not rendered by `build_pdf.py` | Replaced with a `plantuml` state diagram (Auth Stack → App Stack with HomeTab / SearchTab / ProfileTab nested stacks) |
| `business/business-process-v2.md` | Two references to `activity_to_html.py`, a script that does not exist | Removed both references; updated header comment and Activity Diagram Rules section to point to `build_pdf.py` as the actual renderer |

### README.md corrections (4 items)

| Section | Fix |
|---|---|
| Templates tree | `├── modules/` → `├── flows/` (aligns with actual directory name); `module-data-flow-v2.md` and `module-flow-v2.md` listed correctly |
| `verify_docs.py` valid types list | Added `mobile-app` (was omitted despite Phase 8 adding it) |
| `build_pdf.py` valid types list | Added `iac` and `mobile-app` (both omitted despite Phases 8–9 adding them) |
| Diagrams section | "Eight scripts" → "Two tools" (`build_pdf.py` + `translate_docs.py`); removed duplicate table header row; updated renderer note from "all six UML scripts" to "`build_pdf.py`" |

### PDF builder script sync

`pdf_allowlist.py` had no entries for `iac` or `mobile-app`, so `--project-type iac` and `--project-type mobile-app` produced near-empty PDFs.

| File | Change |
|---|---|
| `docs/templates/script/pdf_allowlist.py` | Added `IAC = frozenset({"iac"})`, `MOBILE = frozenset({"mobile-app"})`, `ALL9 = ALL \| IAC \| MOBILE` constants |
| | Updated 15+ existing entries to include `IAC` and/or `MOBILE` where `document-matrix.md` marks them Required or Optional |
| | Added 4 new entries: `("design", "architecture/topology.md", IAC)`, `("design", "specs/mobile-contract.md", MOBILE)`, `("deployment", "specs/runbook.md", IAC)`, `("deployment", "specs/drift-policy.md", IAC)` |
| | Updated `AUTO_SCAN_TYPES`: `modules/*/*-module-data-flow.md` and `modules/*/*-flow.md` → `ALL \| MOBILE`; `business/*-process.md` → added `\| MOBILE` |
| `docs/templates/script/build_pdf.py` | Fixed comment: `flows/*-module-data-flow.md` → `modules/*/*-module-data-flow.md` (matches actual glob pattern) |

**verify_framework.py result after all fixes:** all 6 checks ✅ pass.

---

## Phase 15 — Universal Testing Coverage ✅ Complete

While writing concrete test-plan.md and test-report.md files for a data-pipeline POC project, it became apparent that test-plan.md and test-report.md were completely absent from the framework's enforcement layer: not in `document-matrix.md`, not in `verify_docs.py`, not in any of the 9 init files, not in `sprint-sync.md`, and not in `document-purposes-common.md`. The root cause was that they were listed in `verify_framework.py`'s `TEMPLATE_MATRIX_EXEMPT` set — suppressing the matrix check rather than fixing the omission. Every project type needs a test plan and a test report.

**Goal:** Add test-plan.md and test-report.md to all framework enforcement files so they are Required for all 9 project types.

### Done

| File | Change |
|---|---|
| `docs/templates/init/document-matrix.md` | Added `test-plan.md` and `test-report.md` rows — ✅ Required for all 9 project types |
| `docs/templates/script/verify_docs.py` | Added both to `MATRIX` (`'R'` for all 9 types) and `FILE_LOCATIONS` (`'specs'`) |
| `docs/templates/script/verify_framework.py` | Removed `specs/test-plan.md` and `specs/test-report.md` from `TEMPLATE_MATRIX_EXEMPT` |
| `docs/templates/specs/test-plan.md` | Added **IaC / DevOps** and **Mobile App** rows to the per-type guide table |
| `docs/templates/sprint-sync.md` | Added two `[Types: All]` checklist items for test-plan.md and test-report.md |
| `document-purposes-common.md` | Added `specs/test-plan.md` and `specs/test-report.md` entries (Applies to: All project types) |
| `docs/templates/init/web-app.md` | Added steps 19–20 (test-plan.md, test-report.md); renumbered tail |
| `docs/templates/init/cli-tool.md` | Added steps 16–17; renumbered tail |
| `docs/templates/init/library.md` | Added steps 12–13; renumbered tail |
| `docs/templates/init/data-pipeline.md` | Added steps 17–18 (with Data Pipeline–specific notes); renumbered tail |
| `docs/templates/init/ml-pipeline.md` | Added steps 18–19 (with Pipeline-specific notes); renumbered tail |
| `docs/templates/init/microservices.md` | Added steps 6–7 to System-Level Setup |
| `docs/templates/init/llm-app.md` | Added steps 23–24; renumbered tail |
| `docs/templates/init/iac.md` | Updated "Documents that still apply" note; added steps 7–8; renumbered tail |
| `docs/templates/init/mobile-app.md` | Added Step 9 (test-plan + test-report with Mobile App–specific notes); renumbered Steps 9–10 → Steps 10–11 |
| `docs/templates/init/retrofit.md` | Added steps 2–3 in Step 4 (project status documents) for test-plan.md and test-report.md |

Also during this phase: created concrete test-plan.md, test-report.md, and pipeline-contract.md for a data-pipeline POC; fixed stale DataHub version in dependencies.md (0.12.x → 0.15.0.1) and task count in quickstart.md (10/10 → 12/12); added pipeline-contract.md to pdf_allowlist.py; enhanced test-report.md template with four data-pipeline-specific sections (Contract Tests, Integration Tests, E2E System Test, Fault Injection Tests).

**Bug fix (post-commit):** `docs/templates/business/business-objects-v2.md` contained stale content — an old version of the business process template (showing `# Business Process Index` with `@startuml` activity diagram syntax) instead of the business objects index and `*-object.md` file format. Web App and Microservices initializations copy this file to `docs/business/business-objects.md`, so any project that followed the framework was silently getting the wrong content. Fixed by rewriting the file with the correct Business Objects Index content, including the `plantuml` state diagram template for individual `*-object.md` files.

---

## Phase 16 — PDF Output Improvements ✅ Complete

**Goal:** Make `build_pdf.py` output more useful and the framework more robust around PDF generation.

### Done

| File | Change |
|---|---|
| `docs/templates/script/pdf_allowlist.py` | Removed `task-log.md` and `sprint-change-log.md` from allowlist — dev-process logs, not spec content |
| `docs/templates/script/build_pdf.py` | Added `--content spec\|full` flag — `spec` omits Plan and Test chapters, producing a clean system specification PDF for stakeholder handoff; output filename auto-derives (`project-spec-{lang}.pdf` vs `project-documentation-{lang}.pdf`) |
| `docs/templates/script/build_pdf.py` | Fixed `VALID_PROJECT_TYPES` — `iac` and `mobile-app` were missing, causing `--project-type iac` to exit with an error |
| `docs/templates/script/build_pdf.py` | Added `script/.gitignore` to exclude `plantuml.jar`, `__pycache__/`, `.pdf_build_cache/` |
| `docs/templates/script/verify_framework.py` | Added **Check 9** (`build-pdf-type-sync`) — compares `build_pdf.py` VALID_PROJECT_TYPES against the canonical `PURPOSES_FILES` registry so a missing type is caught automatically |
| `docs/.gitignore` | Added `*.pdf` — PDF files should be generated in actual project repos, not committed to the framework template repo |
| `README.md` | Updated PDF generation section with `--content spec` usage and explanation |
## Phase 17 — Spec Content Quality Check ✅ Complete

`verify_docs.py` currently only checks whether a file exists. A file that contains only template headers and `<!-- TODO -->` placeholders passes the audit despite having no real content. There is currently no way to tell the difference between a filled spec and an empty one.

**Goal:** Add content-level checking to `verify_docs.py` so that the audit catches unfilled placeholders, missing required sections, and near-empty documents — without requiring an LLM call.

### Changes

| File | Change |
|---|---|
| `docs/templates/script/verify_docs.py` | Add `--content` flag: scan each Required document for (1) unfilled placeholders (`<!-- TODO -->`, `_TBD_`, `[placeholder]`), (2) required section headers by document type (e.g. `## Error Handling`, `## Acceptance Criteria`), (3) minimum fill length per section (≥ 3 non-empty lines) |
| `docs/templates/script/verify_docs.py` | Output: per-document fill score (e.g. `pipeline-contract.md  72% filled  ⚠️ 2 unfilled sections`) and summary line (`Spec fill: 8/11 documents fully filled`) |
| `docs/templates/script/verify_framework.py` | Add Check 10 (`content-check-sections`): verify that the required-section list used by `--content` is defined for every document type in the matrix |

**Token impact:** zero — AGENTS.md unchanged. Script-only change.

---

## Phase 18 — LLM Judge Spec Review ✅ Complete

Script-based checks (Phase 17) catch structural gaps but cannot evaluate whether the content is clear, unambiguous, or testable. A spec that says "the system should respond quickly" passes every rule check but is useless for development.

**Goal:** Add a prompt template that lets an LLM score a spec on a rubric and return a structured PASS/FAIL with per-criterion evidence. This is the "LLM-as-a-Judge" layer.

### New templates

| Template | For project type | Purpose |
|---|---|---|
| `specs/spec-review.md` | All types | Rubric prompt: 5 criteria × 1–5 score + evidence + overall PASS/FAIL |

### Rubric criteria (all project types)

| Criterion | What is checked |
|---|---|
| Completeness | Every requirement has an Acceptance Criterion |
| Ambiguity | No vague terms without measurable definition ("fast", "appropriate", "sufficient") |
| Error Coverage | Error paths, timeouts, null returns, and retry behaviour described |
| Testability | A QA engineer can write a test case from the spec alone |
| Consistency | No contradictions between sections or between this doc and related docs |

Per-type addenda are listed inside the template (e.g. Data Pipeline adds Idempotency; AI/LLM App adds Hallucination Handling).

### Integration

| File | Change |
|---|---|
| `docs/templates/sprint-sync.md` | Add pre-closeout step: "Run spec-review.md against all Required spec documents. Resolve all FAIL items before closing sprint." |
| `document-purposes-common.md` | Add `specs/spec-review.md` entry: purpose, when to load, what to do with FAIL output |
| `docs/templates/init/document-matrix.md` | `spec-review.md` marked as a process template (exempt from matrix — not a project document) |

**Token impact:** zero — AGENTS.md unchanged. Template is load-on-demand at sprint end.

---

## Phase 19 — Spec Challenge (QA Simulation) ✅ Complete

LLM Judge (Phase 18) scores what is written. Spec Challenge finds what is missing. Instead of asking "how good is this spec?", it asks "what does this spec not answer?" — then iterates until no significant holes remain.

**Goal:** Add a prompt template that instructs an LLM to act as the most demanding QA + architect, generate a list of unanswered questions, and repeat until two consecutive rounds produce no new critical questions.

### New templates

| Template | For project type | Purpose |
|---|---|---|
| `specs/spec-challenge.md` | All types | QA simulation prompt: generate Unresolved Questions list; do not rewrite spec; iterate until dry |

### Challenge question categories (per-type)

| Category | Example questions |
|---|---|
| Failure paths | If the API times out? If the DB returns null? If the queue is full? |
| Concurrency | If two users submit simultaneously? If Airflow retries mid-run? |
| Data integrity | If the source sends a duplicate? If a required field is missing? |
| Permission edge cases | If the user's token expires mid-session? If the role changes during a transaction? |
| Type-specific (Data Pipeline) | If a stage produces zero rows? If upstream schema changes? |
| Type-specific (AI/LLM App) | If the model returns an empty response? If the retriever returns no results? |

### Process

1. Load `specs/spec-challenge.md` with the target spec pasted in.
2. LLM outputs an **Unresolved Questions** list — no rewrites, no scores.
3. Author answers each question by updating the spec.
4. Repeat until the LLM's new question list has zero Critical items.
5. Record final round count in `docs/specs/test-report.md → Spec Challenge` section.

### Integration

| File | Change |
|---|---|
| `docs/templates/sprint-sync.md` | Add step after spec-review.md: "Run spec-challenge.md. Iterate until no Critical questions remain." |
| `document-purposes-common.md` | Add `specs/spec-challenge.md` entry |
| `docs/templates/specs/test-report.md` | Add `## Spec Challenge` section: rounds run, final unresolved count, sign-off |

**Token impact:** zero — AGENTS.md unchanged. Template is load-on-demand.

---

## Phase 20 — Verification Trigger Layer ✅ Complete

Phases 17–19 add three verification layers, but all three still depend on the developer (or AI agent) remembering to run them. The trigger mechanism must work regardless of which AI tool is being used — Claude Code, Codex, Cursor, or none.

**Goal:** Make verification automatic at the git commit boundary, with AI-tool-specific fast-feedback as an optional layer on top. Scripts are the stable core; triggers are just entry points.

### Trigger architecture

```
Any AI tool (Claude / Codex / Cursor / manual)
        ↓
      edit files
        ↓
   git commit
        ↓
 .githooks/pre-commit   ← PRIMARY: tool-agnostic, always fires
        ↓
 verify_docs.py --content
 verify_logs.py
 verify_tests.py
        ↓
 PASS → commit proceeds
 FAIL → commit blocked, output shown

Optional fast-feedback layer (Claude Code only):
   Claude stop → .claude/settings.json Stop hook → same scripts
   → logs/verify-{timestamp}.json
```

### Changes

| File | Change |
|---|---|
| `.githooks/pre-commit` | New shell script: reads `.project-starter.yml` for project type, runs `verify_docs.py --content`, `verify_logs.py`, `verify_tests.py`; blocks commit on failure |
| `.project-starter.yml` | New config file created at project init: `project_type: data-pipeline` / `docs_path: docs/` — single source of truth for all scripts and hooks |
| `docs/templates/init/web-app.md` (and all 8 other init files) | Add setup step: "Run `cp .githooks/pre-commit .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit`"; create `.project-starter.yml` |
| `.claude/settings.json` (optional, Claude Code only) | Stop hook: same scripts → `logs/verify-{timestamp}.json`; documented as optional fast-feedback, not required |
| `docs/current-state.md` template | Closeout section: `Verify: run pre-commit hook or paste verify_docs output — Required: __ / __ present` |
| `document-purposes-common.md` | Add `.githooks/pre-commit` and `.project-starter.yml` entries |
| `README.md` | Add "Verification" section: architecture diagram, setup instructions, note that Claude Code hook is optional |

### Tool compatibility

| AI tool | Pre-commit hook fires? | Claude Code Stop hook fires? |
|---|---|---|
| Claude Code | ✅ on git commit | ✅ optional fast-feedback |
| Codex | ✅ on git commit | ❌ not applicable |
| Cursor | ✅ on git commit | ❌ not applicable |
| Manual (no AI) | ✅ on git commit | ❌ not applicable |

**Token impact:** zero — AGENTS.md unchanged.

> **Note:** The trigger architecture diagram above was extended in Phase 21 to add five additional process checks (AGENTS.md token budget, changelog audit trail, closeout completeness, Writing Audience violations, and `verify_framework`). The `README.md → Verification` section has the complete, current diagram.

---

## Phase 21 — Complete Hook Coverage ✅ Complete

Phase 20 covers the verification scripts (docs / logs / tests). Five additional AGENTS.md process rules are still instruction-only — any AI tool or developer can silently violate them with no catch. All five can be enforced at the git commit boundary, making them tool-agnostic.

**Goal:** Extend `.githooks/pre-commit` to cover all five remaining process rules. No Claude Code dependency.

### Checks added to pre-commit hook

| What git staged files indicate | Check | Catches |
|---|---|---|
| Running in framework repo (`templates/script/verify_framework.py` present) | Run `verify_framework.py --strict` | Stale pointer, matrix gap, token budget violation created mid-Phase |
| `AGENTS.md` in staged files | Count lines; fail if > 200 | Token budget drift |
| Any `specs/*.md` or `architecture/*.md` staged | Check if `changelog.md` is also staged; warn if not | Silent spec changes with no audit trail |
| `current-state.md` staged | Grep Closeout section for `___` or `<!-- ` | Task "closed" without filling Closeout |
| Any spec-facing doc staged | Grep for `Sprint \d`, `Task \d+`, `\(S\d+\)` patterns | Writing Audience violations in stakeholder docs |

All checks run inside the single `.githooks/pre-commit` script from Phase 20 — no new files needed.

### Tool compatibility

All five checks fire on `git commit` regardless of AI tool used:

| AI tool | All 5 checks fire? |
|---|---|
| Claude Code | ✅ |
| Codex | ✅ |
| Cursor | ✅ |
| Manual | ✅ |

Optional Claude Code fast-feedback: `PostToolUse` hooks in `.claude/settings.json` can surface the same warnings mid-session before commit, documented as optional in README.

### Integration

| File | Change |
|---|---|
| `.githooks/pre-commit` | Extend with 5 new check blocks; each block only runs if its trigger condition matches staged files |
| `README.md` | Update "Verification" section: full table of all checks, trigger conditions, severity (warn vs. block) |
| `document-purposes-common.md` | Add note: process rules in AGENTS.md are enforced by pre-commit, not by agent memory |

**Token impact:** zero — AGENTS.md unchanged.

---

## Phase 22 — Self-Improving Framework via Auto-Fix PR ✅ Complete

When a project's spec has quality problems, the cause is either (a) the project's content is insufficient, or (b) the framework template for that project type doesn't give enough guidance. Type (b) is a framework gap — it affects every future project of the same type, not just this one.

**Goal:** Automatically diagnose whether a spec problem is project-level or framework-level, and for framework-level gaps, open a PR on `project_starter_v4` with a generic template fix — no project content included.

### Iteration limit

The self-improving loop runs **at most 2 rounds per spec quality check cycle**. After 2 rounds, remaining gaps are logged as known issues and left for manual review — preventing runaway PR creation and keeping the feedback signal focused.

```
Round 1: diagnose → open PRs for framework gaps found
         ↓ (after merge or skip)
Round 2: re-run spec check → open PRs for any new gaps surfaced
         ↓
Stop. Remaining issues → logged to logs/framework-gaps.md for manual triage.
```

### Diagnosis logic

```
Spec quality problem found
    ↓
Does the framework template for {type} / {document}
already include guidance on this?
    ├── Yes → project/AI execution issue → feedback to project only
    └── No  → framework gap (max 2 rounds)
                → auto-generate generic template improvement
                → open PR on project_starter_v4
                → PR contains: type + document + missing guidance
                → no project-specific content
```

### Auto-fix PR scope

| Framework gap type | Auto-fix action |
|---|---|
| Required section missing from template | Add section with guidance comment to the template file |
| No example for a required field | Add `<!-- Example: ... -->` block |
| Per-type addendum missing (e.g. Data Pipeline has no Error Handling row) | Add row to per-type table in template |

### New script

| Script | Input | Output |
|---|---|---|
| `templates/script/propose_framework_fix.py` | `--type`, `--document`, `--gap-description` | Creates branch on `project_starter_v4`, edits template, opens PR via `gh pr create` |

### PR format (auto-generated)

```
Title: [Auto-fix] {type} / {document}: add {gap description} section

Body:
Detected gap: {type} projects using {document} have no template
guidance for: {gap description}.

Fix: added a placeholder section with guidance comments to the template.
Review and fill in concrete guidance before merging.

Source: auto-generated by diagnose_spec.py. No project content included.
```

### Integration

| File | Change |
|---|---|
| `templates/script/diagnose_spec.py` | New: takes spec quality check output → classifies each problem as project-level or framework-level → calls `propose_framework_fix.py` for framework gaps; accepts `--round 1\|2` flag; on round 2 writes remaining gaps to `logs/framework-gaps.md` instead of opening more PRs |
| `templates/sprint-sync.md` | Add optional sprint-end step: run `diagnose_spec.py --round 1`, merge or skip PRs, then run `--round 2`; stop after round 2 |
| `README.md` | Add "Self-improving loop" section: diagram + iteration limit explanation + how to run `diagnose_spec.py` |

**Token impact:** zero — AGENTS.md unchanged.

> **Canonical reference:** `README.md → Self-improving loop` is the authoritative source for usage commands, PR format, and architecture diagram. This Phase 22 entry is the historical record of the design decision. `templates/sprint-sync.md → Step 7` cross-references README.md for runtime usage.

---

## Phase 23 — Task / Sprint Quality Gate ✅ Complete

Every task closeout currently only checks whether Required documents exist (`verify_docs.py`). Logs and test execution have no quality gate — they can be missing, empty, or low-quality with no automated catch.

**Goal:** Extend the per-task closeout check to cover three quality dimensions: documents, logs, and test execution.

### Checks added

| Dimension | What is checked | Tool |
|---|---|---|
| Docs | Required files present + sections filled (via Phase 17 `--content`) | `verify_docs.py --content` |
| Logs | `logging-spec.md` format followed: trace_id present, structured fields, no raw print statements; per-type addenda (pipeline row count, LLM call log) | `verify_logs.py` (new) |
| Test execution | `test-report.md` filled: test count > 0, pass/fail recorded, edge cases listed; for Data Pipeline / ML Pipeline: contract tests and fault injection sections non-empty | `verify_tests.py` (new) |

### New scripts

| Script | Flag | Output |
|---|---|---|
| `docs/templates/script/verify_logs.py` | `--project-type`, `--logs PATH` | Per-file: trace_id ✅/❌, structured format ✅/❌, per-type fields present |
| `docs/templates/script/verify_tests.py` | `--project-type`, `--docs PATH` | test-report.md fill score, missing sections, `PASS / FAIL` |

### Integration

| File | Change |
|---|---|
| `docs/current-state.md` template | Closeout section: add three lines — `verify_docs --content`, `verify_logs`, `verify_tests` — Claude must paste output; git diff shows whether it was done |
| `docs/templates/sprint-sync.md` | Add sprint-end step: run all three verifiers; record summary in `task-log.md` |
| `.githooks/pre-commit` (Phase 21 template) | Add `verify_logs.py` and `verify_tests.py` to pre-commit hook chain |
| `document-purposes-common.md` | Add entries for `verify_logs.py` and `verify_tests.py` |

**Token impact:** zero — AGENTS.md unchanged.

---

## Phase 24 — Full Document Content Quality Gate ✅ Complete

`verify_docs.py` checks whether required documents *exist*. `verify_docs.py --content` scans for generic placeholder patterns. Neither knows what *specific sections* each document must contain, nor which sections apply to which project type. An agent can leave `pipeline-contract.md` with empty stage rows, `api-contract.md` with no endpoint entries, or `architecture.md` with no diagram — and no tool will catch it today.

**Goal:** Add `verify_content.py` — for every Required document in the project's declared type, verify that each document's required sections contain real content, gated by document type × project type.

### What was already implemented (partial Phase 24)

`verify_module_docs.py` was shipped and covers module flow files only:

- **Coverage check** — for every module in scan_codebase.py output, confirms `docs/modules/[module]/[module]-module-data-flow.md` exists
- **Module type quality** — section-level checks per module type:

| Module type | Required content |
|---|---|
| **Pipeline Stage** | `Input` block: Source, Format, Schema non-empty; `Output` block: Destination, Format non-empty; `Error Handling`: transient + missing-input cases, ≥ 3 lines |
| **Feature** | ≥ 1 real `Function:` + `File:` pair (not placeholder); operations filled or explicitly `Not Supported` |
| **Background Job** | `Trigger:` non-empty; success path (`→ acknowledge / commit`) present; `Error Handling`: transient + permanent cases, ≥ 3 lines |
| **Shared Utility** | `plantuml` class block non-empty; ≥ 1 real method signature; `Used by` table ≥ 1 real row |

This partial work is correct and stays. `verify_content.py` either absorbs it or calls it.

---

### Remaining work — `verify_content.py`

```
templates/script/verify_content.py

Usage:
  python3 docs/script/verify_content.py --project-type TYPE
  python3 docs/script/verify_content.py --project-type TYPE --docs PATH
  python3 docs/script/verify_content.py --project-type TYPE --strict
  python3 docs/script/verify_content.py --project-type TYPE --json
```

Runs all document-level checkers that apply to the declared project type. Each checker is a `check_[docname]()` function with its own section-level rules.

---

### Content quality rules — Universal (all project types)

| Document | Required content |
|---|---|
| `architecture.md` | `plantuml` component block present and non-empty; ≥ 1 component defined (not placeholder `[Component]`) |
| `quickstart.md` | Prerequisites section ≥ 1 real item; ≥ 1 numbered setup step with real command or instruction; Verification step present |
| `research.md` | ≥ 1 decision entry with non-placeholder Rationale; Decision field not blank |
| `test-plan.md` | Testing Strategy section ≥ 3 lines; ≥ 1 test level defined (unit / integration / e2e) with real scope |
| `test-report.md` | *(already covered by `verify_tests.py` — skip in verify_content.py)* |
| `logging-spec.md` | *(already covered by `verify_logs.py` — skip in verify_content.py)* |

---

### Content quality rules — by project type

#### Web App · Microservices

| Document | Required content |
|---|---|
| `api-contract.md` | ≥ 1 endpoint row with real Method + Path (not `[METHOD]`/`[/path]`); Response schema non-placeholder |
| `permissions.md` | Role table ≥ 2 rows (header + ≥ 1 real role); ≥ 1 permission matrix entry |
| `data-model.md` | ≥ 1 entity/table defined; `plantuml` ER block non-empty |
| `backend.md` | Stack section ≥ 1 real technology; Layer pattern described (non-placeholder) |

#### Data Pipeline · ML Pipeline

| Document | Required content |
|---|---|
| `pipeline-contract.md` | Cross-stage table ≥ 1 data row; each row has non-placeholder Input format + Output format |
| `pipeline-debug.md` | ≥ 1 debug scenario with Symptom + Root cause non-empty |
| `data-model.md` | ≥ 1 schema/table defined |
| `backend.md` | Stack section non-empty |

#### ML Pipeline (additional)

| Document | Required content |
|---|---|
| `model-contract.md` | Input schema ≥ 1 real field; Output format non-placeholder; ≥ 1 production threshold defined |
| `experiment-log.md` | ≥ 1 experiment entry with Hypothesis + Result non-empty |

#### CLI Tool

| Document | Required content |
|---|---|
| `cli-contract.md` | ≥ 1 subcommand defined with non-placeholder description; ≥ 1 flag or argument |
| `release-guide.md` | Versioning policy non-empty; ≥ 1 publish step |

#### Library / SDK

| Document | Required content |
|---|---|
| `public-api.md` | ≥ 1 public function or class documented with real signature (not `[FunctionName]`) |
| `release-guide.md` | Same as CLI Tool |
| `compatibility-matrix.md` | ≥ 1 runtime version row with Support status |

#### Microservices (additional)

| Document | Required content |
|---|---|
| `service-catalog.md` | ≥ 1 service row with real name, port, owner |
| `service-contract.md` | ≥ 1 inter-service endpoint or event documented |

#### AI / LLM Application

| Document | Required content |
|---|---|
| `llm-contract.md` | Model name non-placeholder; System prompt ≥ 1 line of real content; ≥ 1 parameter defined |
| `eval-spec.md` | ≥ 1 evaluation criterion with scoring rubric non-empty; ≥ 1 test case |
| `prompt-library.md` | ≥ 1 prompt entry (name + file reference) |

#### IaC / DevOps

| Document | Required content |
|---|---|
| `topology.md` | `plantuml` block non-empty; ≥ 1 resource defined |
| `runbook.md` | ≥ 1 runbook entry with Steps non-empty |
| `drift-policy.md` | Detection cadence non-placeholder; Remediation SLA defined |

#### Mobile App

| Document | Required content |
|---|---|
| `mobile-contract.md` | ≥ 1 screen defined with non-placeholder title; Navigation structure described |
| `architecture.md` | Same as universal rule + ≥ 1 screen component in diagram |

---

### Module flow files (delegated to `verify_module_docs.py`)

`verify_content.py` calls `verify_module_docs.py` internally (or re-runs its logic) for `docs/modules/`. No duplication — module flow rules stay in `verify_module_docs.py`.

---

### Output format

```
Document Content Quality — data-pipeline
────────────────────────────────────────────────────────────────────
Document                    Required   Quality
architecture.md             ✅         ✅  Fully filled
pipeline-contract.md        ✅         ⚠️  Cross-stage table empty
pipeline-debug.md           ✅         ⚠️  No debug scenarios documented
data-model.md               ✅         ✅  Fully filled
quickstart.md               ✅         ✅  Fully filled
research.md                 ✅         ⚠️  Rationale placeholder in 2 decisions
test-plan.md                ✅         ⚠️  No test levels defined
modules/ge-validation       ✅         ✅  Fully filled  (Pipeline Stage)
modules/dbt-transform       ✅         ⚠️  Missing Output contract  (Pipeline Stage)
modules/model-training      ❌ Missing  —

Documents  : 8 / 9 present
Quality    : 3 / 8 existing documents fully filled
```

### Integration

| File | Change |
|---|---|
| `.githooks/pre-commit` | Replace `verify_module_docs.py` call with `verify_content.py` call (subsumes it) |
| `templates/sprint-sync.md` | Update Step 4 quality gate to use `verify_content.py` |
| `guidance/document-purposes-common.md` | Add `verify_content.py` entry; mark `verify_module_docs.py` as internal |
| `templates/script/verify_framework.py` | Update Check 10 to validate `verify_content.py` covers all 9 types and all document checkers |

**Token impact:** zero — AGENTS.md unchanged.

---

## Phase 25 — verify_content.py Bug Fixes + Stale Doc Sync ✅ Complete

A post-Phase-24 audit found three correctness bugs in `verify_content.py` and seven stale references across documentation files. Phase 25 resolves all of them.

### Bug fixes — verify_content.py

| Bug | Location | Description |
|---|---|---|
| Hybrid type dropped | `run_module_docs()` | Only passes `project_types[0]` to `verify_module_docs.py` — secondary types in a hybrid (e.g. `data-pipeline+web-app`) are silently ignored. Fix: join all types with `+` and forward the full string. |
| `_section_body` truncates early | `_section_body()` | Boundary regex `^#+` stops at any heading level. A `##` section body containing `###` sub-sections is truncated before all content is read. Fix: stop only at a heading of the same level or higher. |
| Duplicate exclusion token | `check_cli_contract()` | `'command'` appears twice in the exclusion tuple — copy-paste error. Remove the duplicate. |

### Stale documentation fixes

| File | Issue |
|---|---|
| `README.md` script tree | Add `verify_content.py` to the `templates/script/` listing |
| `README.md` pre-commit architecture diagram | Add `verify_content.py` as step 4; mark `verify_module_docs.py` as internal (not a direct step) |
| `README.md` framework maintenance table | Update Check 10 row from `verify_module_docs.py` → `verify_content.py` |
| `guidance/document-purposes-common.md` | Pre-commit entry says "three quality verifiers" — update to four and list `verify_content.py` |
| `guidance/document-purposes-common.md` | `scan_codebase.py` valid types list omits `iac` and `mobile-app` |
| `build_pdf.py` docstring | Valid types list omits `iac` and `mobile-app` |
| `templates/sprint-sync.md` Optional block | Clarify that `verify_module_docs.py --src` adds only the source-coverage check; `verify_content.py` already calls it internally |

**Token impact:** zero — AGENTS.md unchanged.

---

## Phase 26 — Dead Code Removal ✅ Complete

Four instances of dead code identified across existing scripts. Low risk; each is an isolated, self-contained fix.

| File | Issue | Fix |
|---|---|---|
| `verify_module_docs.py` | `present_count` computed identically to `present`; one is dead | Remove `present_count`; use `present` throughout `print_results` |
| `verify_docs.py` | `elif fill_pct >= 50 or fill_pct >= 80:` — the `>= 80` clause is unreachable | Simplify to `elif fill_pct >= 50:` |
| `scan_codebase.py` | `"constants"` appears twice in `SHARED_PATTERNS` set literal | Remove the duplicate |
| `diagnose_spec.py` | `"flows"` in template subdir search — no document lives under `docs/flows/` in any project type | Remove `"flows"` from the subdir list |

**Token impact:** zero — AGENTS.md unchanged.

---

## Phase 27 — Cross-Script Refactor: Shared Utilities + diagnose_spec.py Update ✅ Complete

A systematic audit revealed four categories of cross-script maintenance risk. Phase 27 addresses the highest-impact ones.

### 1 — `_section_body` interface unification

Three scripts each define their own `_section_body` with incompatible signatures:

| Script | Signature | Returns |
|---|---|---|
| `verify_content.py` | `(text: str, pattern: str)` | `str \| None` |
| `verify_logs.py` | `(lines: list[str], header: str)` | `list[str]` |
| `verify_tests.py` | `(lines: list[str], header_re: compiled)` | `(str, list[str])` |

Fix: standardise on the `verify_content.py` signature (regex pattern on full text, returns body string or None). Update `verify_logs.py` and `verify_tests.py` call sites.

### 2 — `_PLACEHOLDER_RES` / `_is_placeholder` divergence

Defined separately in four scripts with divergent pattern lists — a placeholder caught by one script may not be caught by another.

Fix: move the canonical list to a shared `_verify_common.py` module; import from it in all four scripts.

### 3 — `SKIP_ROOT` duplicates `SKIP_DIRS` in `scan_codebase.py`

`SKIP_ROOT` inside `print_tree` is a local copy of module-level `SKIP_DIRS`. Adding a new directory to one requires a manual update to the other.

Fix: replace `SKIP_ROOT` with a direct reference to `SKIP_DIRS`.

### 4 — `diagnose_spec.py` incompatibility with `verify_content.py` output

`diagnose_spec.py` expects `verify_docs.py --content --json` output (`results[].content.unfilled_sections`). `verify_content.py --json` emits `documents[].issues` instead. Feeding `verify_content.py` output into `diagnose_spec.py` returns zero gaps silently.

Fix: update `diagnose_spec.py` to accept `verify_content.py --json` output (`documents[].issues`); update docstring and `sprint-sync.md` usage example accordingly.

**Token impact:** zero — AGENTS.md unchanged.

---

## Phase 28 — Stale Reference & Formatting Cleanup ✅ Complete

A post-Phase-27 audit found five categories of stale content that slipped through the automated checks: wrong file paths in historical prose, a missing section separator, two references to a script that no longer exists, and a tree entry for a file that is never committed.

**Goal:** Remove all stale references and formatting inconsistencies that `verify_framework.py` cannot catch because they live in prose or non-template files.

### Changes

| File | Change |
|---|---|
| `ROADMAP.md` Phase 1 table | `docs/templates/flows/module-data-flow-v2.md` → `templates/flows/module-data-flow-v2.md` (old `docs/` prefix was never correct for this repo) |
| `ROADMAP.md` between Phase 15 and Phase 16 | Add missing `---` section separator (the only Phase boundary in ROADMAP without one) |
| `ROADMAP.md` Phase 22 PR format block | Align wording with `README.md → Self-improving loop` PR format (title/body template was inconsistent between the two locations) |
| `guidance/document-purposes-common.md` `### codebase-map.md` | Remove reference to `component_to_html.py` — script does not exist; update to point to `build_pdf.py` |
| `templates/codebase-map.md` `## Page Structure Overview` | Remove the same stale `component_to_html.py` reference |
| `README.md` `templates/script/` tree | Annotate `plantuml.jar` entry to make clear it is downloaded separately and not committed to the repo |

**Token impact:** zero — AGENTS.md unchanged.

---

## Phase 29 — AGENTS.md Consolidation ✅ Complete

AGENTS.md has three structural issues that compound as the file approaches the 200-line token budget: a duplicated principles section, a misplaced standalone instruction, and a sprint-sync block whose wording can cause unintended eager file loading.

**Goal:** Merge the duplicate section, relocate the misplaced line, reword the sprint-sync trigger, and restore token headroom before the next Phase causes a budget violation.

### Changes

| File | Change |
|---|---|
| `AGENTS.md` `## Development Principles` + `## Package First` | Merge into a single `## Development Principles` block; add a one-line explanation for each sub-principle currently listed without description (Maintainability First, Glue Code) |
| `AGENTS.md` "Do not scan repository." | Relocate from its isolated position inside the "If continuing an existing project" paragraph into the **Startup sequence** numbered list as an explicit item, making the context unambiguous |
| `AGENTS.md` `## Sprint Documentation Sync` | Reword "Load ... now." to conditional form: "Load `templates/sprint-sync.md` only at sprint end — not during normal task work." Eliminates ambiguity about when loading should occur |
| `AGENTS.md` | After the above changes, verify total line count; target ≤ 185 lines to maintain a safe buffer below the 200-line limit |

**Token impact:** net reduction — merging the duplicate section removes ~8 lines.

---

## Phase 30 — Per-Type Coverage Gaps in Quality & Debug Files ✅ Complete

Three supporting files — `code-quality-check.md`, `debug-instrumentation-rules.md`, and `spec-review.md` — were last substantially updated during Phases 1–3 when only the original project types existed. IaC/DevOps (Phase 9) and Mobile App (Phase 8) were added without corresponding updates to these files. A `test-plan.md` row also needs clarification.

**Goal:** Bring `code-quality-check.md`, `debug-instrumentation-rules.md`, `spec-review.md`, and `test-plan.md` up to date for all 9 project types.

### Changes

| File | Change |
|---|---|
| `code-quality-check.md` `# Required Context` | Replace the hardcoded `docs/architecture/*` path list with a per-type conditional table (Web App / Microservices: full list; CLI Tool / Library: trim to relevant files; IaC: topology + runbook; Data Pipeline: pipeline-contract + pipeline-debug) |
| `code-quality-check.md` `## Permission Consistency`, `## State Machine Consistency` | Convert plain-text indented lists to Markdown tables — the rest of the file uses tables and these two sections are inconsistent |
| `code-quality-check.md` `# Sprint Completion` | Remove section — sprint management is out of scope for a code quality checklist; the content belongs in `sprint-sync.md` |
| `debug-instrumentation-rules.md` intro | Add per-type applicability matrix at the top: which layer numbers apply to which project types (Layer 11/12/14 are Web App / Mobile App only; IaC / CLI Tool / Library have no application layers) |
| `debug-instrumentation-rules.md` `### 1. Entry Point` table | Add IaC / DevOps row (`terraform apply` / `ansible-playbook` invocation) and Mobile App row (app launch / deep-link handler) |
| `templates/specs/spec-review.md` `## Per-type addenda` | Add IaC / DevOps section: topology completeness (all declared resources defined), runbook coverage (all resource types have incident response steps), drift-policy SLA measurability |
| `templates/specs/test-plan.md` IaC / DevOps row — Contract / Service column | Expand to clarify: "Resource compliance policy contract" means OPA / Sentinel policy tests enforcing tagging, CIDR, and IAM constraints — not service API contracts |

**Token impact:** zero — AGENTS.md unchanged.

---

## Phase 31 — Init File Consistency ✅ Complete

Five consistency gaps found across the 9 init files and `retrofit.md`: placeholders that could have been filled at authoring time, a missing CLI flag, undocumented IaC omissions, an ambiguous microservices delegation, and a pre-commit install command copied verbatim nine times.

**Goal:** Make all init files internally consistent and reduce repetition without changing the initialization workflow.

### Changes

| File | Change |
|---|---|
| All 9 `templates/init/*.md` — `.project-starter.yml` creation step | Replace `project_type: [your-type]` placeholder with the actual type for each init file (e.g. `web-app.md` sets `project_type: web-app`) — the init file already knows the type at authoring time |
| `templates/init/retrofit.md` Step 1b | Add `--project-type <type>` flag to the `scan_codebase.py` command — currently missing; without it, the scan runs in web-app-fallback mode for retrofit projects of other types |
| `templates/init/iac.md` | Add explicit steps for `project-plan.md`, `task-log.md`, `sprint-change-log.md`, and `changelog.md` — or add a note explaining these are intentionally omitted for IaC projects and the rationale |
| `templates/init/microservices.md` `## Per-Service Setup` | Add note: when following `web-app.md` steps per service, skip the hook install step and `.project-starter.yml` creation — both are system-level and must be done once at repo root, not per service |
| All 9 `templates/init/*.md` — pre-commit hook install step | Extract the verbatim-repeated install command (`cp .githooks/pre-commit .git/hooks/pre-commit && chmod +x ...`) into a shared reference block or a cross-reference to `README.md → Verification` to avoid maintaining 9 identical copies |

**Token impact:** zero — AGENTS.md unchanged.

---

## Phase 32 — Documentation Deduplication ✅

A systematic audit found eleven duplication patterns across `README.md`, per-type document-purposes files, and template files. Each duplicate is a future maintenance hazard: one copy gets updated, the other silently goes stale.

**Goal:** Establish a single source of truth for each piece of repeated content; downstream locations point to the canonical source.

### Changes

| File | Change |
|---|---|
| `README.md` `## Working on an existing project` | Replace with a one-line cross-reference to `AGENTS.md → Startup sequence` — the section restates the same steps |
| `README.md` `## Module types` | Replace detailed type descriptions with a cross-reference to `templates/flows/module-data-flow-v2.md` — the section is a near-verbatim copy |
| `README.md` `## Key design decisions` — "Seven module types" | Correct to: 4 flow-file formats (Feature, Background Job, Pipeline Stage, Shared Utility / Resource Group); Command / Namespace / Service are `scan_codebase.py` classification labels, not flow-file formats |
| `README.md` `## Retrofitting an existing project` | Align step-count description with `retrofit.md` actual numbering (Steps 1a / 1b / 1c / 2 / 3 / 4 / 5 — not "six steps") |
| `README.md` `## Generating the merged PDF` | Remove the duplicate `--content spec` explanation paragraph (appears twice in the same section) |
| `guidance/document-purposes-common.md` `## How to use this file` | Remove — restates `document-purposes.md` load rules; replace with a one-line pointer to `guidance/document-purposes.md` |
| `guidance/document-purposes-common.md` `### init/[type].md` Files list | Add `init/iac.md` and `init/mobile-app.md` (omitted when Phases 8–9 were added) |
| `guidance/document-purposes-cli-tool.md` `## Business` section | Expand to match `document-purposes-web-app.md` detail level — purpose, when to update, and scope of `business-process.md` and `[process-name]-process.md` |
| `guidance/document-purposes-library.md` | Add `## Business` and `## Flows` sections with explicit note: "N/A — Library projects have no user-facing business processes or module flows; omit both sections." |
| Per-type document-purposes files — `logging-spec.md` Purpose (5 near-identical copies) | Keep the full entry in `document-purposes-common.md` only; replace the 4 per-type copies with a one-line pointer |
| `guidance/document-purposes-microservices.md` — `backend.md` | Keep the full entry in `document-purposes-web-app.md`; replace the microservices copy with a pointer |
| `document-purposes.md` final paragraph | Clarify that template files live under `templates/` in this repo; projects copy them to `docs/` — the current wording implies templates are at project root |

**Token impact:** zero — AGENTS.md unchanged.

---

## Phase 33 — Process Logic & State Machine Fixes ✅ Complete

Eleven ambiguities found where process instructions contradict each other, omit the source of a required value, or create an undocumented double-run. Each is a decision point where an AI agent or developer can silently take the wrong path.

**Goal:** Make every process step unambiguous — no contradictions, no missing prerequisites, no undocumented repeated steps.

### Changes

| File | Change |
|---|---|
| `.project-starter.yml` template + `.githooks/pre-commit` | Add guard comment to the template: "Do not commit with `[your-type]` placeholder." Add a validation check in the pre-commit hook: if `project_type` still matches the placeholder pattern, block the commit with a clear error message |
| `templates/sprint-sync.md` Step 4 + Step 7 | Resolve WARN / Step-7 ambiguity: add a decision gate after Step 4 — "If any WARN remained after manual triage, proceed to Step 7 (`diagnose_spec.py`). If all issues resolved, skip Step 7." |
| `templates/sprint-sync.md` Step 4 + Document Update Checklist | Add a note explaining the two-pass design: Step 4 is a pre-check before the doc updates; the Checklist re-runs `verify_content.py` after all updates to confirm fixes landed |
| `templates/sprint-sync.md` Quick filter guide | Mark as canonical; add a pointer from `templates/current-state.md` template that the quick filter guide lives in `sprint-sync.md` — remove the duplicated copy from `current-state.md` |
| `templates/task-completion.md` Step 1c | Add cross-reference note: "`current-state.md → Closeout` omits this step for brevity — the authoritative procedure is here." |
| `templates/module-completion.md` first line | Change "Run this check after every task" to "Run this check only when a module is confirmed 100% complete — skip otherwise." Aligns with AGENTS.md wording |
| `templates/current-state.md` `## Closeout` verify commands | Add instruction: "Replace TYPE with the value from `.project-starter.yml → project_type`." (currently `--project-type TYPE` with no explanation of where TYPE comes from) |
| `templates/task-log.md` + `guidance/document-purposes-common.md` | Add header comment to `task-log.md` describing all column fields including `plan` and `changelog`; update the `document-purposes-common.md → task-log.md` entry to list the current column set |
| `README.md` + `ROADMAP.md` Phase 20 verification diagram | Align the two architecture diagrams: README.md has the Phase-21-updated version (PostToolUse hook added); annotate the Phase 20 diagram in ROADMAP to note it was extended in Phase 21 |
| `README.md`, `ROADMAP.md` Phase 22, `templates/sprint-sync.md` Step 7 | Designate `README.md` as canonical for self-improving loop usage; ROADMAP.md Phase 22 is historical record; `sprint-sync.md` Step 7 cross-references README. Align the PR format template across all three locations |
| Per-type `document-purposes-*.md` — `business-process.md` Optional trigger | Expand brief entries (data-pipeline and others) to match the web-app detail level — specify the concrete condition under which `business-process.md` should be created |

**Token impact:** zero — AGENTS.md unchanged.

---

## Phase 34 — Framework Inventory: glossary.md & dependencies.md ✅ Complete

`glossary.md` and `dependencies.md` exist as templates but appear in no init file, no document matrix row, and no sprint-sync checklist item. They are listed in `verify_framework.py`'s `TEMPLATE_MATRIX_EXEMPT` set with no rationale comment. Any project following the framework would not know these templates exist or when to use them.

**Goal:** Register both templates in the framework enforcement layer, or document a clear rationale for their exempt status and add discovery guidance so users can find them.

### Changes

| File | Change |
|---|---|
| `templates/script/verify_framework.py` `TEMPLATE_MATRIX_EXEMPT` | Add inline comment explaining why `glossary.md` and `dependencies.md` are exempt (always-optional utilities, created on demand — not gated by project type) |
| `templates/init/document-matrix.md` | Add `glossary.md` and `dependencies.md` rows — mark as ⚠️ Optional for all 9 project types |
| `templates/script/verify_docs.py` | Add both to `MATRIX` as `'O'` for all types and to `FILE_LOCATIONS` |
| All 9 `templates/init/*.md` | Add a conditional note: "Optional: create `docs/specs/glossary.md` if the project introduces domain terms that need definition; create `docs/specs/dependencies.md` to track external dependency versions and upgrade policy." |
| `guidance/document-purposes-common.md` | Add `### specs/glossary.md` and `### specs/dependencies.md` entries explaining purpose, when to create, and update triggers |

**Token impact:** zero — AGENTS.md unchanged.

---

## Phase 35 — Script & Per-Type Document-Purposes Cleanup ✅ Complete

Three targeted issues surfaced that are too isolated to group with other phases: a context-free checker in `verify_content.py` that misreads pipeline projects, an undocumented fork requirement in `diagnose_spec.py`, and a hook entry in `document-purposes-common.md` where two verification counts appear consecutively without explanation.

**Goal:** Make the two scripts and the common guidance entry accurate and self-explanatory for all users, including those who fork the framework.

### Changes

| File | Change |
|---|---|
| `templates/script/verify_content.py` `TYPE_DOCS['data-pipeline']` — `deployment.md`, `database.md` checkers | Add pipeline-aware context: `deployment.md` for data-pipeline should check for a DAG / orchestration-tool reference, not HTTP server config; `database.md` should check for a warehouse / data-lake storage reference, not an OLTP schema. Add a comment explaining the distinction from web-app context. |
| `templates/script/diagnose_spec.py` `DEFAULT_FRAMEWORK_REPO` (lines 38–40) | Add module-level docstring note: "Fork users: set the `PROJECT_STARTER_REPO` environment variable to override the default repo target before running `propose_framework_fix.py`." Add the same env-var note to `README.md → Self-improving loop`. |
| `guidance/document-purposes-common.md` `### .githooks/pre-commit` | Rewrite the verifier count section: list the four quality verifiers (`verify_docs`, `verify_content`, `verify_logs`, `verify_tests`) and five process checks (token budget, changelog gate, Writing Audience violation, Closeout completeness, `verify_framework`) as two explicit labelled groups — not as adjacent numbers |

**Token impact:** zero — AGENTS.md unchanged.

---

## Phase 36 — Architecture Analysis (Design Documents) ✅ Complete

Before any implementation, three design documents establish the target architecture, quantify the current coupling problems, and define the migration plan. No implementation files are modified in this phase.

**Goal:** Produce three decision-ready design documents that all subsequent Phases (37–39) are derived from.

### Deliverables

| File | Content |
|---|---|
| `docs/architecture-analysis.md` | Current architecture diagram (what exists now); dependency graph showing which scripts hardcode the same project-type knowledge; coupling problem catalogue with line-count evidence; recommended responsibility boundaries |
| `docs/refactoring-plan.md` | Phase 1 (registry + context builder + AGENTS.md reduction), Phase 2 (workflow state extraction), Phase 3 (full orchestrator + agent adapters) — each with files affected, migration strategy, and risk level |
| `docs/context-builder-design.md` | Inputs (`.project-starter.yml` fields, `current-state.md` Task Type field), outputs (`.ai/AI_CONTEXT.md` format), document selection algorithm, registry lookup logic, token reduction estimate vs current startup sequence |

### Key decisions captured in the design documents

| Decision | Rationale |
|---|---|
| `document-registry.yaml` schema includes `path`, `purpose`, `context_priority`, `used_by` — not just `required: true` | Context builder needs to know *why* a document is read, not just *whether* it is required |
| Task type is deterministic — declared in `.project-starter.yml` or `current-state.md → Task Type:` field | Avoids AI inference complexity in v1; any tool (Claude, Codex, Cursor, manual) can run the context builder |
| Output goes to `.ai/AI_CONTEXT.md` — AI reads it directly | No MCP / plugin integration in v1; adapter layer is Phase 3 |
| No folder restructuring in Phase 1 | Folder rename touches every script path reference; the value is gained from the registry + context builder alone, without the migration risk |

**Token impact:** zero — no implementation files modified.

---

## Phase 37 — Document Registry ✅ Complete

`verify_docs.py` `MATRIX`, `verify_content.py` `TYPE_DOCS` + `DOC_PATHS`, and `document-matrix.md` all encode the same project-type → document knowledge independently. Adding a new document type currently requires updating three separate files. The registry eliminates this duplication.

**Goal:** Create `document-registry.yaml` as the single source of truth for all document metadata. Refactor `verify_docs.py` and `verify_content.py` to load from it. Delete the hardcoded structures.

### Registry schema (per document entry)

```yaml
pipeline-contract:
  file: pipeline-contract.md
  path: specs/pipeline-contract.md
  required_for: [data-pipeline, ml-pipeline]
  optional_for: []
  context_priority: high        # high | medium | low
  purpose: "Define cross-stage input/output contracts and data formats"
  used_by: [context-builder, validator, init-flow]
  related: [pipeline-debug, data-model]
```

### Changes

| File | Change |
|---|---|
| `document-registry.yaml` (new, repo root) | Full registry — one entry per document; covers all 39 documents currently in `verify_docs.py` MATRIX |
| `templates/script/verify_docs.py` | Remove hardcoded `MATRIX` and `FILE_LOCATIONS`; add `load_registry()` function; all type lookups go through registry |
| `templates/script/verify_content.py` | Remove hardcoded `TYPE_DOCS` and `DOC_PATHS`; load from registry; `UNIVERSAL_DOCS` derived from registry entries where all 9 types are `required_for` |
| `templates/script/verify_framework.py` | Update Check 10: validate registry schema (all 9 types present, required fields present) instead of scraping `TYPE_DOCS` from source |
| `templates/init/document-matrix.md` | Add note: this file is now a human-readable view of `document-registry.yaml` — the registry is authoritative |
| `README.md` | Add `document-registry.yaml` to repo tree; add usage note under "Framework maintenance" |

**Backward compatibility:** `verify_docs.py` and `verify_content.py` CLI flags unchanged — only internal data source changes.

**Token impact:** zero — AGENTS.md unchanged.

---

## Phase 38 — Context Builder ✅ Complete

AI agents currently discover required context by reading AGENTS.md startup rules, then reading `current-state.md`, then inferring which documents to load. This adds token cost on every task startup and produces inconsistent results across AI tools.

**Goal:** Create `build-context.py` — a deterministic script that reads `.project-starter.yml` + `current-state.md` and generates `.ai/AI_CONTEXT.md` listing exactly which files the AI must read for the current task.

### Inputs

| Source | Field | Used for |
|---|---|---|
| `.project-starter.yml` | `project_type` | Registry lookup → required documents |
| `.project-starter.yml` | `task_type` | Filter context to task-relevant documents |
| `current-state.md` | `Task Type:` field (new) | Override or supplement `.project-starter.yml` task_type |
| `document-registry.yaml` | `context_priority`, `purpose`, `related` | Rank and annotate the output |

### Output format — `.ai/AI_CONTEXT.md`

```markdown
# AI Context — data-pipeline / Pipeline Stage
Generated: 2026-07-18T10:00:00

## Read (Required)
- docs/current-state.md
- docs/specs/pipeline-contract.md   # Define cross-stage contracts
- docs/specs/data-model.md          # Schema reference
- docs/modules/sap-ingestion/sap-ingestion-module-data-flow.md

## Read (If Present)
- docs/specs/pipeline-debug.md      # Only if task involves debugging

## Skip
- docs/changelog.md
- docs/specs/test-report.md
- (all documents not relevant to this task type)
```

### Changes

| File | Change |
|---|---|
| `build-context.py` (new, repo root) | Script: reads `.project-starter.yml` + `current-state.md`, queries `document-registry.yaml`, writes `.ai/AI_CONTEXT.md` |
| `.project-starter.yml` schema | Add `task_type` field; valid values derived from module types + task categories (e.g. `pipeline-stage`, `feature`, `bug-fix`, `sprint-end`) |
| `templates/current-state.md` | Add `Task Type:` field to the header block |
| `.ai/` directory | New directory; add `.ai/` to `.gitignore` — generated context is not committed |
| `README.md` | Add "Context Builder" section: how to run, output format, how AI tools consume `.ai/AI_CONTEXT.md` |
| `guidance/document-purposes-common.md` | Add `build-context.py` and `.ai/AI_CONTEXT.md` entries |

**Token impact:** zero — AGENTS.md unchanged in this phase (reduction happens in Phase 39).

---

## Phase 39 — AGENTS.md Simplification via Context Builder ✅ Complete

AGENTS.md currently contains the full document discovery logic: startup sequence rules, Required Context inference, Doc Checklist filter guide. Now that `build-context.py` handles discovery deterministically, these rules can be replaced with a single instruction.

**Goal:** Replace the multi-step document discovery section in AGENTS.md with a pointer to `build-context.py` + `.ai/AI_CONTEXT.md`. Target: AGENTS.md ≤ 150 lines (from current ~190).

### Changes

| File | Change |
|---|---|
| `AGENTS.md` `## Current State → Starting work` | Replace steps 1–3 (read current-state → infer Required Context → start) with: "Run `python3 build-context.py` → read `.ai/AI_CONTEXT.md` → follow the Read list." |
| `AGENTS.md` `## Current State → Closing out a task` | Keep closeout rules unchanged — context builder does not affect closeout |
| `AGENTS.md` Doc Checklist quick filter guide | Remove — this logic moves into `build-context.py` task_type → document mapping |
| `templates/current-state.md` | Remove the embedded quick filter guide comment block; add: "Run `build-context.py` to generate `.ai/AI_CONTEXT.md` before starting." |
| `templates/sprint-sync.md` | Quick filter guide section: replace with "Run `build-context.py --task-type sprint-end`" — deterministic, no manual filtering |
| `guidance/document-purposes-common.md` | Add note under `.githooks/pre-commit`: context builder runs as part of pre-task setup, not the hook chain |

**Token reduction:** removing the startup discovery logic and quick filter guide from AGENTS.md frees ~30–40 lines, bringing total to ≤ 150 — well below the 200-line budget.

**Verification:** run `verify_framework.py --strict` after changes; token budget check will pass at new lower count.

---

## Phase 40 — Script Responsibility Reorganization ✅

`templates/script/` currently holds a flat list of scripts with mixed responsibilities: validation, generation, scanning, and framework-internal auditing. As the toolset grows (orchestrator, adapters), this flat layout makes ownership unclear and raises the risk of shipping framework-internal tools to user projects by mistake.

**Goal:** Introduce responsibility-based subdirectories inside `templates/script/` without changing external-facing paths. Separate scripts shipped to user projects from scripts that are framework-internal only. No script logic changes.

### Proposed layout

```
templates/script/
├── validators/           # shipped to user projects
│   ├── verify_docs.py
│   ├── verify_content.py
│   ├── verify_logs.py
│   ├── verify_tests.py
│   └── verify_module_docs.py
├── generators/           # shipped to user projects
│   ├── build_pdf.py
│   └── diagnose_spec.py
├── scanners/             # shipped to user projects
│   └── scan_codebase.py
└── framework/            # framework-internal only — NOT copied to user projects
    └── verify_framework.py
```

`build-context.py` remains at repo root — it is user-facing and shipped as-is.

### Changes

| File | Change |
|---|---|
| `templates/script/validators/` (new dir) | Move `verify_docs.py`, `verify_content.py`, `verify_logs.py`, `verify_tests.py`, `verify_module_docs.py` here |
| `templates/script/generators/` (new dir) | Move `build_pdf.py`, `diagnose_spec.py` here |
| `templates/script/scanners/` (new dir) | Move `scan_codebase.py` here |
| `templates/script/framework/` (new dir) | Move `verify_framework.py` here; update README note: not for user projects |
| `.githooks/pre-commit` | Update script paths to match new subdirectory layout |
| `guidance/document-purposes-common.md` | Update all `docs/script/` references to new subdirectory paths |
| `templates/sprint-sync.md` | Update verify script invocation paths |
| `templates/current-state.md` | Update verify script invocation paths in Closeout section |
| `README.md` | Update file tree; add "framework-internal vs user-project scripts" distinction note |
| `templates/init/*.md` (all init files) | Update script copy instructions to use new subdirectory paths |

**Risk:** Path references are scattered across many files — run `grep -r "docs/script/" templates/ .githooks/` before starting to generate the full change list.

**Backward compatibility:** User projects that already copied scripts to `docs/script/` are unaffected — only the source paths in the framework template change.

**Verification:** run `verify_framework.py --strict`; all stale-pointer checks must pass after path updates.

---

## Phase 41 — Orchestrator: Workflow Manager

`build-context.py` (Phase 38) solves context assembly for a known task type. But choosing *which* workflow to run, sequencing validators, and deciding when to stop still require the AI agent to read AGENTS.md and reason about the right order. This reasoning is implicit and varies by tool.

**Goal:** Create `orchestrator.py` at repo root — a deterministic workflow manager that reads the current task, selects the correct validator sequence, and writes `.ai/WORKFLOW.md` alongside `.ai/AI_CONTEXT.md`. AI agents follow the workflow plan mechanically rather than reasoning about it.

### Inputs

| Source | Field | Used for |
|---|---|---|
| `.project-starter.yml` | `project_type`, `task_type` | Select workflow template |
| `docs/current-state.md` | `Task Type:` | Override task_type at task level |
| `document-registry.yaml` | `used_by`, `context_priority` | Determine validator scope |

### Output format — `.ai/WORKFLOW.md`

```markdown
# Workflow Plan — bug-fix / data-pipeline
Generated: 2026-07-18T10:00:00

## Pre-task
1. Run `python3 build-context.py` → read `.ai/AI_CONTEXT.md`

## Implementation
- Follow Steps in `docs/current-state.md`

## Post-task validators (run in order)
1. `python3 docs/script/validators/verify_docs.py --project-type data-pipeline --content`
2. `python3 docs/script/validators/verify_logs.py --project-type data-pipeline --strict`
3. `python3 docs/script/validators/verify_content.py --project-type data-pipeline --strict`

## Closeout
- Follow Closeout section in `docs/current-state.md`
```

### Changes

| File | Change |
|---|---|
| `orchestrator.py` (new, repo root) | Reads `.project-starter.yml` + `current-state.md`; selects workflow template; calls `build-context.py`; writes `.ai/WORKFLOW.md` |
| `workflow-registry.yaml` (new, repo root) | Maps `task_type` → ordered validator sequence + pre/post steps |
| `.ai/WORKFLOW.md` | Generated output; gitignored alongside `AI_CONTEXT.md` |
| `.gitignore` | Add `.ai/WORKFLOW.md` |
| `AGENTS.md` `## Current State → Starting work` | Replace `build-context.py` pointer with `orchestrator.py` pointer (orchestrator calls context builder internally) |
| `guidance/document-purposes-common.md` | Add `orchestrator.py`, `workflow-registry.yaml`, `.ai/WORKFLOW.md` entries |
| `README.md` | Add "Orchestrator" section |

**Token impact:** AGENTS.md shrinks further — validator sequence is now in WORKFLOW.md, not recalled from agent memory.

**Verification:** run `orchestrator.py --dry-run`; confirm WORKFLOW.md matches expected validator sequence for each task type.

---

## Phase 42 — Agent Adapters

The orchestrator (Phase 41) produces a tool-agnostic workflow plan. Different AI tools consume instructions differently: Claude Code reads AGENTS.md + slash commands; Codex reads `.codex/` config; Cursor reads `.cursorrules`. Without adapters, each tool user must manually wire up the orchestrator.

**Goal:** Create a thin adapter layer that translates `.ai/WORKFLOW.md` output into the native instruction format of each supported AI tool. Core logic stays in the orchestrator; adapters contain only format translation.

### Adapter responsibilities

| Adapter | Input | Output |
|---|---|---|
| Claude Code | `.ai/WORKFLOW.md` | `.claude/commands/start-task.md` slash command; Stop hook writes task log |
| Codex | `.ai/WORKFLOW.md` | `.codex/setup.md` + `.codex/task-instructions.md` |
| Cursor | `.ai/WORKFLOW.md` | `.cursorrules` (task-scoped rule injection) |

### Changes

| File | Change |
|---|---|
| `adapters/claude/` (new dir) | `start-task.md` — slash command that runs orchestrator then presents WORKFLOW.md to agent; `stop-hook.sh` — writes task-log row on session end |
| `adapters/codex/` (new dir) | `setup.md`, `task-instructions.md` templates populated from WORKFLOW.md |
| `adapters/cursor/` (new dir) | `.cursorrules` template with WORKFLOW.md injection points |
| `orchestrator.py` | Add `--adapter [claude|codex|cursor]` flag; calls adapter render after writing WORKFLOW.md |
| `README.md` | Add "Agent Adapters" section: per-tool setup instructions, adapter architecture diagram |
| `guidance/document-purposes-common.md` | Add `adapters/` directory entry |

**Constraint:** Adapters must not contain document selection logic — that stays in `document-registry.yaml` + `orchestrator.py`. Any adapter that duplicates selection logic is a bug.

**Verification:** run `orchestrator.py --adapter claude --dry-run`; confirm `.claude/commands/start-task.md` is generated with correct WORKFLOW.md content injected.

---

## Phase 43 — Post-Phase-42 Audit Fixes

Full-project audit after Phase 42 surfaced eight issues: a shell syntax error, a missing `--adapter` mention in AGENTS.md, two Stop-hook wiring gaps, a missing registry ↔ matrix sync check, a Codex adapter UX gap, a README ambiguity about `adapters/` scope, and stale `v4` references in docstrings.

**Goal:** Fix all eight issues and add a new `verify_framework.py` check (Check 11) so future additions to `document-registry.yaml` are automatically validated against `document-matrix.md`.

### Changes

| File | Change |
|---|---|
| `.githooks/run-verify.sh` | Fix shell syntax error: `tr -d ""' "` → `tr -d "\"'"` (malformed quote caused parse failure on line 10) |
| `orchestrator.py` | Docstring: `project_starter_v4` → `project_starter_v5` |
| `AGENTS.md` § Starting work | Add one-line note that `--adapter [claude\|codex\|cursor]` can be passed to also render the tool-native instruction file |
| `.claude/settings.json` | Add `adapters/claude/stop-hook.sh` as a second Stop hook command alongside `run-verify.sh` (separate concerns: verification logs vs. task-log row) |
| `adapters/codex/setup.md` | Add prerequisite note: if `task-instructions.md` shows `{{WORKFLOW_CONTENT}}` as literal text, run `--adapter codex` first |
| `README.md` § Project Initialization | Add explicit note that `adapters/` is not copied to user projects; adapter output is generated via `orchestrator.py --adapter <tool>` |
| `README.md` § Framework maintenance | Add Check 11 row to the checks table |
| `guidance/document-purposes-common.md` § verify_framework.py | Update check count (ten → eleven); add Check 11 description |
| `templates/script/framework/verify_framework.py` | Docstring `v4` → `v5`; add `check_registry_matrix_sync` (Check 11): warns when a document-registry.yaml key has no matrix row or vice versa; wire into `CHECK_ORDER`, `CHECK_LABELS`, and `main()` |

**Verification:** run `bash -n .githooks/run-verify.sh` (no parse error); run `python3 templates/script/framework/verify_framework.py --strict` and confirm Check 11 (Registry ↔ matrix sync) passes.

---

## Phase 44 — Validation Telemetry

The framework manages documents, workflow, and validators but has no visibility into AI agent behavior over time — which validators fail most, which tasks retry, which specs change most. Without this data, framework improvement is based on intuition, not evidence.

**Goal:** Add a `.ai/telemetry/` layer. Write structured JSON after each validator run and each task session boundary. Token usage is left as a placeholder — it requires adapter-level data that varies by AI tool and is addressed in a later phase.

### What the framework can log without external dependencies

| Data | Source | Written by |
|---|---|---|
| Validator pass/fail/warn per document | verify scripts | `verify_docs.py`, `verify_content.py` with `--telemetry` flag |
| Task session boundary (task name, adapter) | `current-state.md` + hook | `adapters/claude/stop-hook.sh` |
| Orchestrator run count per task | orchestrator | `orchestrator.py` |
| Token count | API response metadata | placeholder `null` until adapter provides it |

### Changes

| File | Change |
|---|---|
| `.gitignore` | Add `.ai/telemetry/` (generated, not committed) |
| `templates/script/validators/verify_docs.py` | Add `--telemetry` flag: appends run result to `.ai/telemetry/validation-result.json` |
| `templates/script/validators/verify_content.py` | Same `--telemetry` flag and output format |
| `adapters/claude/stop-hook.sh` | Also write `.ai/telemetry/task-run.json` row on session end |
| `orchestrator.py` | On each run, increment `orchestrator_runs` in `.ai/telemetry/task-run.json` for the current task |
| `README.md` | Add "Validation Telemetry" section: schema description, what is logged, what requires adapter data |
| `guidance/document-purposes-common.md` | Add `.ai/telemetry/` directory entry |

**Schema — `validation-result.json`** (append-only array):
```json
{ "ts": "2026-07-18T13:00:00Z", "project_type": "data-pipeline",
  "validator": "verify_content.py", "level": "fail",
  "warn_count": 0, "fail_count": 2,
  "failed_docs": ["pipeline-contract.md", "architecture.md"] }
```

**Schema — `task-run.json`** (append-only array):
```json
{ "ts": "2026-07-18T14:00:00Z", "task": "implement extract stage",
  "adapter": "claude", "orchestrator_runs": 2, "token_count": null }
```

**Verification:** run `verify_docs.py --project-type data-pipeline --telemetry`; confirm `.ai/telemetry/validation-result.json` is written with correct structure.

---

## Phase 45 — Spec ↔ Code Validator: Core + Framework Adapter Interface

> **Architecture note (Phase 52.5):** The framework-specific adapter design introduced here (`AirflowAdapter`, `ClickAdapter`) was superseded by the capability-based adapter + detector plugin architecture defined in Phase 52.5. The `NormalizedForm` contracts and the core `verify_spec_code.py` comparison engine remain unchanged. Phase 52.5 describes what the implementation actually looks like.

Existing validators are structural — they check if documents are filled, not whether code matches what the spec declares. The biggest SDD risk is spec–code drift: a field renamed in code, a stage output changed, a flag removed — none of which current validators catch.

**Goal:** Introduce `verify_spec_code.py` and the `FrameworkAdapter` interface. The core validator never knows about specific frameworks — it only compares `NormalizedForm` objects produced by adapters. Build two PoC adapters (Airflow, Click) to prove the interface works end-to-end, then wire into the existing pipeline.

### Architecture

```
verify_spec_code.py
        │  receives --adapter, --spec, --src
        ▼
FrameworkAdapter (base class)
        │
        ├── extract_spec(spec_path) → NormalizedForm
        ├── extract_code(src_path)  → NormalizedForm
        └── normalize()             → NormalizedForm

verify_spec_code.py
        │  compare(NormalizedForm, NormalizedForm)
        ▼
    MismatchReport
```

`NormalizedForm` is per-project-type — `verify_spec_code.py` compares two instances of the same type and reports added / removed / renamed / type-changed items. It never contains framework-specific logic.

### NormalizedForm per project type

| Project type | NormalizedForm | Key fields |
|---|---|---|
| Web App / Microservices | `NormalizedEndpoint` | method, path, request fields, response fields |
| Data Pipeline / ML Pipeline | `NormalizedStageContract` | stage name, input fields (name + type), output fields (name + type) |
| CLI Tool | `NormalizedCommand` | command name, flags (name + type + required) |
| Library / SDK | `NormalizedFunction` | function name, params (name + type), return type |
| AI / LLM App | `NormalizedTool` | tool name, parameter schema |
| IaC / DevOps | `NormalizedResource` | resource name, resource type, config keys |
| Mobile App | `NormalizedScreen` | screen name, props (name + type) |

### PoC adapters (this phase)

| Adapter | Framework | Project type |
|---|---|---|
| `AirflowAdapter` | Apache Airflow (Python) | Data Pipeline |
| `ClickAdapter` | Click (Python) | CLI Tool |

### Changes

| File | Change |
|---|---|
| `templates/script/validators/verify_spec_code.py` (new) | Core validator: `--project-type`, `--adapter`, `--spec`, `--src`, `--strict`, `--json`, `--dry-run`; loads adapter by name; calls `extract_spec` + `extract_code`; compares NormalizedForms; reports mismatches |
| `templates/script/validators/_spec_code_adapters/` (new dir) | `_base.py` — `FrameworkAdapter` abstract base class + `NormalizedForm` dataclasses; `airflow.py` — `AirflowAdapter`; `click.py` — `ClickAdapter` |
| `workflow-registry.yaml` | Add `verify_spec_code.py` to `pipeline-stage` and `feature` validators for `data-pipeline`, `ml-pipeline`, `cli-tool` |
| `.githooks/pre-commit` | Run `verify_spec_code.py --strict` when `pipeline-contract.md` or `cli-contract.md` is staged |
| `guidance/document-purposes-common.md` | Add `verify_spec_code.py` + `_spec_code_adapters/` entries |
| `README.md` | Add "Spec ↔ Code Validator" section: architecture diagram, per-type NormalizedForm table, usage |

**Constraint:** `verify_spec_code.py` must contain zero framework-specific logic. Any code that knows what Airflow or Click is belongs in an adapter. Any adapter that contains comparison logic is a bug.

**Verification:** declare field `raw_amount: float` in `pipeline-contract.md`; rename to `amount: int` in Airflow stage code; run `verify_spec_code.py --project-type data-pipeline --adapter airflow --strict`; confirm exits 1 reporting field name and type mismatch.

---

## Phase 46 — Framework Adapter Expansion: Web App + Data Pipeline + Library/SDK

> **Architecture note (Phase 52.5):** The individual framework adapters listed here (`FastAPIAdapter`, `FlaskAdapter`, `ExpressAdapter`, `DagsterAdapter`, `PrefectAdapter`, `PythonLibraryAdapter`) were superseded by the capability-based design in Phase 52.5. Each is now a **detector** inside the appropriate capability directory (`api/detectors/`, `pipeline/detectors/`, `library/detectors/`), not a top-level adapter. See Phase 52.5 for the current structure.

Extend the adapter registry (Phase 45) to cover Web App, Microservices, Data Pipeline (additional frameworks), and Library/SDK. Each new adapter implements the same `FrameworkAdapter` interface — no changes to `verify_spec_code.py` core.

### New adapters

| Adapter | Framework | Language | Project type |
|---|---|---|---|
| `FastAPIAdapter` | FastAPI | Python | Web App / Microservices |
| `FlaskAdapter` | Flask | Python | Web App / Microservices |
| `ExpressAdapter` | Express | Node.js | Web App / Microservices |
| `DagsterAdapter` | Dagster | Python | Data Pipeline / ML Pipeline |
| `PrefectAdapter` | Prefect | Python | Data Pipeline / ML Pipeline |
| `PythonLibraryAdapter` | Python `__all__` / type stubs | Python | Library / SDK |

### Changes

| File | Change |
|---|---|
| `_spec_code_adapters/fastapi.py` (new) | `FastAPIAdapter`: parses `@app.{method}("/path")` decorators + Pydantic model fields → `NormalizedEndpoint[]` |
| `_spec_code_adapters/flask.py` (new) | `FlaskAdapter`: parses `@app.route` + `methods=[]` → `NormalizedEndpoint[]` |
| `_spec_code_adapters/express.py` (new) | `ExpressAdapter`: parses `router.{method}('/path', ...)` → `NormalizedEndpoint[]` |
| `_spec_code_adapters/dagster.py` (new) | `DagsterAdapter`: parses `@op` / `@asset` I/O definitions → `NormalizedStageContract[]` |
| `_spec_code_adapters/prefect.py` (new) | `PrefectAdapter`: parses `@task` input/output type hints → `NormalizedStageContract[]` |
| `_spec_code_adapters/python_library.py` (new) | `PythonLibraryAdapter`: reads `__all__` + function signatures → `NormalizedFunction[]` |
| `workflow-registry.yaml` | Add `verify_spec_code.py` to validator sequences for `web-app`, `microservices`, `library` |
| `.githooks/pre-commit` | Add trigger for `api-contract.md`, `public-api.md` staged |
| `README.md` § Spec ↔ Code Validator | Update adapter registry table with all new adapters |

**Verification:** spec has `POST /orders`, code has `POST /order` (FastAPI); run `verify_spec_code.py --project-type web-app --adapter fastapi --strict`; confirm exits 1 reporting route path mismatch.

---

## Phase 47 — Framework Adapter Expansion: LLM App + IaC + Mobile + Custom Adapter SDK

> **Architecture note (Phase 52.5):** The individual framework adapters listed here (`ToolSchemaAdapter`, `TerraformAdapter`, `PulumiAdapter`, `ReactNativeAdapter`, `FlutterAdapter`) were superseded by the capability-based design in Phase 52.5. Each is now a **detector** inside the appropriate capability directory (`library/detectors/`, `iac/detectors/`, `mobile/detectors/`). The Custom Adapter SDK (`_example_adapter.py`, `docs/contributing-adapters.md`) is updated in Phase 52.5 to reflect the two-layer pattern.

Extend the adapter registry to the remaining three project types. Simultaneously ship the Custom Adapter SDK so the community can contribute adapters for frameworks not covered here — without modifying the core validator.

### New adapters

| Adapter | Framework | Project type |
|---|---|---|
| `ToolSchemaAdapter` | Python function docstrings / OpenAI tool schema | AI / LLM App |
| `TerraformAdapter` | Terraform HCL | IaC / DevOps |
| `PulumiAdapter` | Pulumi (Python) | IaC / DevOps |
| `ReactNativeAdapter` | React Native | Mobile App |
| `FlutterAdapter` | Flutter / Dart | Mobile App |

### Custom Adapter SDK

| Deliverable | Description |
|---|---|
| `_spec_code_adapters/_base.py` | Already exists (Phase 45); extended with richer docstrings and type annotations for external consumers |
| `_spec_code_adapters/_example_adapter.py` (new) | Fully annotated reference implementation; every method documented with contract, expected input, expected output |
| `docs/contributing-adapters.md` (new) | Step-by-step guide: implement `FrameworkAdapter`, register adapter name, write unit test, submit PR |

### Changes

| File | Change |
|---|---|
| `_spec_code_adapters/tool_schema.py` (new) | `ToolSchemaAdapter` → `NormalizedTool[]` |
| `_spec_code_adapters/terraform.py` (new) | `TerraformAdapter` → `NormalizedResource[]` |
| `_spec_code_adapters/pulumi.py` (new) | `PulumiAdapter` → `NormalizedResource[]` |
| `_spec_code_adapters/react_native.py` (new) | `ReactNativeAdapter` → `NormalizedScreen[]` |
| `_spec_code_adapters/flutter.py` (new) | `FlutterAdapter` → `NormalizedScreen[]` |
| `_spec_code_adapters/_example_adapter.py` (new) | Reference implementation for SDK |
| `docs/contributing-adapters.md` (new) | Custom Adapter SDK developer guide |
| `workflow-registry.yaml` | Add `verify_spec_code.py` to validator sequences for `llm-app`, `iac`, `mobile-app` |
| `.githooks/pre-commit` | Add trigger for `llm-contract.md`, `topology.md`, `mobile-contract.md` staged |
| `README.md` § Spec ↔ Code Validator | Add "Writing a custom adapter" subsection pointing to SDK |

**Verification:** run `verify_spec_code.py --list-adapters`; confirm all adapters from Phases 45–47 are listed; confirm `_example_adapter.py` passes its own unit test.

---

## Phase 48 — Semantic Adapter (LLM-Assisted Matching)

Phases 45–47 catch structural mismatches (field absent, route path wrong, flag renamed). They cannot catch semantic mismatches: `order_id: string` in spec, `id: int` in code — same concept, different name and type. Detecting this reliably requires LLM inference.

**Goal:** Add `SemanticAdapter` — a wrapper that implements the same `FrameworkAdapter` interface but adds an LLM comparison pass on top of any structural adapter's `NormalizedForm` output. `verify_spec_code.py` core is unchanged; `--semantic` simply selects `SemanticAdapter` as the adapter.

### Architecture

```
verify_spec_code.py --semantic --adapter fastapi
        │
        ▼
SemanticAdapter(wraps=FastAPIAdapter)
        │
        ├── extract_spec() → delegates to FastAPIAdapter → NormalizedEndpoint[]
        ├── extract_code() → delegates to FastAPIAdapter → NormalizedEndpoint[]
        └── compare()      → structural diff first
                           → remaining ambiguous pairs → LLM
                           → LLM returns { verdict, reasoning } per field
```

### How semantic matching works

```
Structural pass (always first):
  spec field: order_id    code field: id
  → name differs → MISMATCH (structural, no LLM needed)

Structural pass finds no mismatch:
  spec field: order_total: float
  code field: price: Decimal
  → name differs but not caught by normalisation → escalate to LLM

LLM pass:
  "spec declares order_total: float described as 'total price of the order';
   code has price: Decimal — are these the same field?"
  → LLM: likely same concept; float→Decimal compatible; name mismatch → WARNING
```

### Changes

| File | Change |
|---|---|
| `_spec_code_adapters/semantic.py` (new) | `SemanticAdapter(wraps: FrameworkAdapter)`: delegates extract_spec/extract_code to wrapped adapter; adds LLM comparison pass; returns `NormalizedForm` annotated with semantic verdicts |
| `verify_spec_code.py` | Add `--semantic` flag: when set, wraps the selected adapter with `SemanticAdapter`; structural pass always runs first |
| `workflow-registry.yaml` | Semantic adapter is **not** added to any default validator sequence — opt-in only |
| `README.md` § Spec ↔ Code Validator | Add "Semantic matching" subsection: when to use, token cost estimate, output format |

**Constraint:** `--semantic` must never run automatically in pre-commit or default workflow sequences. It is a developer-invoked analysis tool, not a gate. Any PR that adds `--semantic` to a default sequence is a bug.

**Verification:** spec field `order_id: string`, code field `id: int`; run `verify_spec_code.py --adapter fastapi --semantic --project-type web-app`; confirm LLM reports field name mismatch with reasoning; confirm same run without `--semantic` also catches it via structural pass.

---

## Phase 49 — Adapter Contract Hardening

**Discovered in post-Phase-48 audit.**

`_base.py` contract states: `extract_spec()` and `extract_code()` must return `[]` on any error — never raise. `airflow.py` and `click.py` both call `open()` directly inside `extract_spec()` without try/except, violating this invariant. A missing or unreadable spec file crashes the validator instead of returning `[]`. All other error paths in these files already catch exceptions, making this a gap in an otherwise consistent pattern.

**Goal:** Wrap all bare `open()` calls inside `extract_spec()` (and `extract_code()` if any) in every adapter with try/except, returning `[]` on failure. Audit every adapter for this pattern — not just the two confirmed cases.

### Changes

| File | Change |
|---|---|
| `_spec_code_adapters/airflow.py` | Wrap `open()` in `extract_spec()` with `try/except OSError` → return `[]` |
| `_spec_code_adapters/click.py` | Same fix |
| All other adapters | Audit and fix any bare `open()` in `extract_spec()` / `extract_code()` |

**Verification:** pass a non-existent path to `extract_spec()` on each adapter; confirm `[]` is returned and no exception propagates.

---

## Phase 50 — Remove Hardcoded Personal URLs from Generator Scripts

**Discovered in post-Phase-48 audit.**

`diagnose_spec.py` and `propose_framework_fix.py` both hardcode `DEFAULT_FRAMEWORK_REPO = "uchetsai-creator/project_starter_v4"`. A user who runs either script without setting `PROJECT_STARTER_FRAMEWORK_REPO` will open GitHub PRs against someone else's v4 repository. `adapters/codex/setup.md` also hardcodes the same personal GitHub URL in a user-facing link.

**Goal:** Eliminate the default fallback in both generator scripts so a missing env var produces a clear error rather than silently misdirecting. Update `adapters/codex/setup.md` to use a generic placeholder.

### Changes

| File | Change |
|---|---|
| `templates/script/generators/diagnose_spec.py` | Remove `DEFAULT_FRAMEWORK_REPO` constant; exit with actionable error if `PROJECT_STARTER_FRAMEWORK_REPO` is not set |
| `templates/script/generators/propose_framework_fix.py` | Same; also rename temp dir prefix from `ps4-fix-` → `ps5-fix-` |
| `adapters/codex/setup.md` | Replace personal GitHub URL with `<your-fork-url>` placeholder |

**Verification:** run `diagnose_spec.py` without `PROJECT_STARTER_FRAMEWORK_REPO`; confirm error message names the missing variable and exits non-zero.

---

## Phase 51 — Complete VALID_TYPES Centralization

**Discovered in post-Phase-48 audit.**

`verify_docs.py` and `verify_content.py` were refactored to import `VALID_TYPES` from `_registry.py`. Three validators were not updated: `verify_logs.py`, `verify_tests.py`, and `verify_module_docs.py` each declare their own independent hardcoded list. `verify_spec_code.py` has a fifth independent declaration (`VALID_PROJECT_TYPES`). `scan_codebase.py` derives a sixth from `MODULE_VOCAB.keys()`. Adding a new project type to `document-registry.yaml` will not propagate to any of these scripts automatically.

**Goal:** All validators and scan_codebase.py derive their valid-type list from `_registry.py` at runtime. No hardcoded list remains except inside `_registry.py` itself.

### Changes

| File | Change |
|---|---|
| `templates/script/validators/verify_logs.py` | Replace hardcoded `VALID_TYPES` list with `from _registry import VALID_TYPES` |
| `templates/script/validators/verify_tests.py` | Same |
| `templates/script/validators/verify_module_docs.py` | Same |
| `templates/script/validators/verify_spec_code.py` | Replace `VALID_PROJECT_TYPES` list with import from `_registry`; rename to `VALID_TYPES` for consistency |
| `templates/script/scanners/scan_codebase.py` | Derive valid types from `_registry.VALID_TYPES` instead of `MODULE_VOCAB.keys()` |

**Verification:** add a dummy type to `document-registry.yaml`; confirm all five scripts accept it as valid without code changes; remove dummy entry.

---

## Phase 52 — Sync Design Docs to Current Implementation

**Discovered in post-Phase-48 audit.**

Three internal design documents diverge from the implemented system:

1. `docs/context-builder-design.md` documents a `document-registry.yaml` schema (`types:` block with inline R/N/O values and a `flags:` subfield) that was never implemented. The actual schema uses `required_for: [list]` / `optional_for: [list]`. A new contributor following the design doc would write invalid registry entries.
2. `docs/architecture-analysis.md` is the "before" snapshot of coupling problems. Several problems it lists as open are partially or fully resolved (`MATRIX` dict removed, `_registry.py` added, Check 11 added). The PlantUML diagram still shows nodes that no longer exist.
3. `docs/refactoring-plan.md` describes Phase 1 (Document Registry) as future planned work; it is fully implemented. Phases 2 and 3 have no status markers.

**Goal:** Update all three documents to reflect current reality. These are internal docs — accuracy matters more than preserving history.

### Changes

| File | Change |
|---|---|
| `docs/context-builder-design.md` | Rewrite schema section to show the actual `required_for` / `optional_for` format with real examples from `document-registry.yaml` |
| `docs/architecture-analysis.md` | Mark resolved problems ✅; update PlantUML to remove `MATRIX` node; correct "no automated check" claim for document-matrix drift |
| `docs/refactoring-plan.md` | Mark Phase 1 ✅ Complete; add status to Phases 2–3; note which sub-items remain open (VALID_TYPES in 3 validators — tracked in Phase 51) |

**Verification:** read each updated doc; confirm it matches the current file structure; grep for removed artifacts (`MATRIX`, `translate_docs`, stale schema keys) to confirm none remain.

---

## Phase 52.5 — Capability-Based Adapter Architecture

**Discovered in post-Phase-47 architectural review.**

### Problem

Phases 45–47 established a working `FrameworkAdapter` interface but encoded the wrong abstraction boundary. Each adapter maps one-to-one with a specific framework: `FastAPIAdapter`, `AirflowAdapter`, `TerraformAdapter`. Adding Django, Spring Boot, or Spark each requires a new top-level adapter. The registry grows linearly with framework count.

The root cause: "framework" was used as the primary concept when "capability" should be. A FastAPI project and a Flask project both validate the same contract type — HTTP endpoints. The capability is shared; only the extraction mechanism differs.

### Goal

Separate contract validation (capability) from framework-specific extraction (detector). Adding a new framework should require adding a detector, not a new adapter.

### Architecture

```
verify_spec_code.py
        │
        ▼
Capability Adapter
  owns: spec parsing, source discovery, detector orchestration
  does not know: framework names, routing patterns, annotation syntax
        │
        ├── Detector A  (framework-specific extraction)
        └── Detector B  (framework-specific extraction)
                │
                ▼
        NormalizedForm  →  compare()  →  MismatchReport
```

**Responsibility boundaries:**

| Layer | Owns | Does not own |
|---|---|---|
| Capability Adapter | spec parsing, file discovery, detector orchestration | framework names, patterns |
| Detector | extraction logic for one framework | file discovery, comparison |
| `verify_spec_code.py` | comparison, reporting | any adapter or detector detail |

### Invariants

- A detector must not perform file discovery — it receives already-discovered source files from the capability adapter.
- Framework-specific logic must not appear in a capability adapter.
- `verify_spec_code.py` must not contain any framework or capability knowledge.
- Adding a new framework requires adding a detector, not a new adapter.

### Backward Compatibility

Existing `--adapter fastapi` CLI usage must continue to work unchanged. Legacy framework names become aliases that resolve to the appropriate capability adapter. A new `--framework` flag allows explicit detector selection when the capability adapter cannot auto-detect.

### Migration Scope

- Existing framework adapters (Phases 45–47) are reclassified as detectors under their respective capabilities.
- Capability adapters replace framework adapters as the primary public interface.
- `_base.py` gains a `Detector` abstraction alongside the existing `FrameworkAdapter`.
- `docs/contributing-adapters.md` is updated: "add a new framework" means adding a detector, not a new adapter.

---

## Phase 53 — Deduplicate Shared Utilities

**Discovered in post-Phase-48 audit.**

Three duplication problems identified:

1. `templates/script/validators/_registry.py` and `templates/script/framework/_registry.py` are byte-for-byte identical. Both must be updated in sync; there is no mechanism to detect drift.
2. `_annotation_str()` — an AST-annotation-to-string helper — is independently defined across multiple adapter files with identical logic.
3. `_read_task_type_from_current_state()` and `_resolve_task_type()` are duplicated between `orchestrator.py` and `build-context.py`.

**Goal:** Single source of truth for each piece of shared logic. No duplication that requires coordinated updates.

### Changes

| Area | Change |
|---|---|
| `_registry.py` duplication | Delete the framework copy; update `verify_framework.py` to import from the validators copy |
| `_annotation_str()` duplication | Extract to a shared utility module within `_spec_code_adapters`; all adapters and detectors import from it |
| Task-type reader duplication | Extract to a shared location consumed by both `orchestrator.py` and `build-context.py` |
| `docs/contributing-adapters.md` | Note that shared utilities exist and must be imported, not copied |

**Verification:** run all validator self-tests and `verify_framework.py`; confirm no import errors after consolidation.

---

## Phase 54 — v4 → v5 Naming Sweep

**Discovered in post-Phase-48 audit.**

A large number of files still refer to `project_starter_v4` in docstrings, CLI descriptions, comments, and headers. Only `orchestrator.py`, `verify_framework.py`, `verify_spec_code.py`, and the Phase 45–48 adapter files correctly say v5. The stale references create confusion about which version a file belongs to and erode confidence in the codebase's internal consistency.

**Affected files:** `ROADMAP.md` (title), `document-registry.yaml` (header comment), `build-context.py` (docstring), both `_registry.py` copies (docstring + user-facing error message), `verify_docs.py`, `verify_content.py`, `verify_logs.py`, `verify_tests.py`, `verify_module_docs.py` (all: docstrings + argparse descriptions), `docs/architecture-analysis.md`, `docs/refactoring-plan.md` (headers), `.project-starter.yml` (comment), `.githooks/pre-commit` (banner comment), `propose_framework_fix.py` (temp dir prefix `ps4-fix-`).

**Goal:** Replace every `project_starter_v4` reference with `project_starter_v5` (or remove the version suffix where not needed). Change `ps4-fix-` temp prefix to `ps5-fix-` in `propose_framework_fix.py`.

### Changes

All files listed above: search-replace `project_starter_v4` → `project_starter_v5` and `ps4-fix-` → `ps5-fix-`. No logic changes.

**Verification:** `grep -r "project_starter_v4" templates/ *.py *.md *.yaml .githooks/` returns zero results after the sweep.

---

## Phase 55 — Fix Missing Cross-References and Dead References

**Discovered in post-Phase-48 audit.**

Three discoverability gaps:

1. `docs/contributing-adapters.md` is the canonical guide for writing new framework adapters. It is referenced from `_base.py` and `_example_adapter.py` but does not appear in the README file tree — a contributor reading the README cannot find it.
2. README Phase 14 history mentions `translate_docs.py` as one of the generator scripts. This file does not exist anywhere in the repo (likely planned but never implemented or since removed). The dead reference misleads readers looking for it.
3. `verify_module_docs.py` has no automated trigger path. Neither `.githooks/pre-commit` nor `.githooks/run-verify.sh` calls it. Its only invocation path is manual, and this is not documented anywhere.

**Goal:** Close all three gaps. Items are classified by fix type — "CI gate" items block commit; "contributor tool" items inform the developer but do not block.

### Changes

| File | Change | Type |
|---|---|---|
| `README.md` file tree | Add `docs/contributing-adapters.md` under the `docs/` section | Contributor tool |
| `README.md` Phase 14 history note | Remove `translate_docs.py` reference; note only `build_pdf.py` and `schema_to_html.py` exist | Dead-reference removal |
| `README.md` § Module Docs (new subsection) | Explain that `verify_module_docs.py` is a contributor tool run manually before opening a PR, not a pre-commit gate; include the exact command | Contributor tool |
| `.githooks/run-verify.sh` | Add an explicit comment: `# verify_module_docs.py is a contributor tool, not a pre-commit gate — see README § Module Docs` | Documentation in code |

`verify_module_docs.py` is intentionally **not** added to the pre-commit gate. The check is slow and produces noisy output on work-in-progress modules; it is better suited as a manual pre-PR step. The README addition makes this decision visible rather than leaving the script undiscoverable.

**Verification:** `grep -r "translate_docs" .` returns zero results; `docs/contributing-adapters.md` appears in README tree; README contains a § Module Docs section explaining when and how to run `verify_module_docs.py`.

---

## Phase 56 — Code Quality Sweep

**Discovered in post-Phase-48 audit.**

A collection of minor code quality issues across multiple files, none individually blocking but collectively lowering the codebase's internal consistency bar.

### Issues

| Location | Issue |
|---|---|
| `adapters/claude/stop-hook.sh` embedded Python | Two bare `except Exception: pass` blocks silently swallow all errors; telemetry corruption is invisible |
| `verify_spec_code.py` `_item_fields()` | `sys.path.insert(0, str(_ADAPTER_DIR))` runs inside the function body on every call; should be at module level (already done for other functions) |
| `_spec_code_adapters/semantic.py` | Model ID `'claude-haiku-4-5-20251001'` is hardcoded inline; should be a named constant with a comment explaining the model-tier choice |
| `templates/script/generators/build_pdf.py` | `import sys, os, re, glob` — multiple names on one import line (PEP 8) |
| `templates/script/generators/schema_to_html.py` | `import sys, re, os, json, math` — same PEP 8 violation |
| `templates/init/document-matrix.md` | `event-catalog.md` row has a trailing extra cell beyond the 10-column table definition; any programmatic parser will misalign this row |

### Changes

| File | Change |
|---|---|
| `adapters/claude/stop-hook.sh` | Replace bare `except Exception: pass` with `except Exception as e: print(f"telemetry error: {e}", file=sys.stderr, flush=True)` |
| `verify_spec_code.py` | Move `sys.path.insert(0, str(_ADAPTER_DIR))` to module level alongside `_ADAPTER_DIR` declaration |
| `_spec_code_adapters/semantic.py` | Extract `_SEMANTIC_MODEL = 'claude-haiku-4-5-20251001'` constant; add comment: `# Haiku: lowest cost for single-label classification` |
| `build_pdf.py` | Split into one import per line |
| `schema_to_html.py` | Split into one import per line |
| `templates/init/document-matrix.md` | Remove trailing extra cell from `event-catalog.md` row |

**Verification:** `python3 -m py_compile` on all modified Python files; manually inspect document-matrix.md table column counts.
