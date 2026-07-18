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

---

## Phase 21 — Complete Hook Coverage 🔲 Planned

Phase 20 covers the verification scripts (docs / logs / tests). Five additional AGENTS.md process rules are still instruction-only — any AI tool or developer can silently violate them with no catch. All five can be enforced at the git commit boundary, making them tool-agnostic.

**Goal:** Extend `.githooks/pre-commit` to cover all five remaining process rules. No Claude Code dependency.

### Checks added to pre-commit hook

| What git staged files indicate | Check | Catches |
|---|---|---|
| Any file in `project_starter_v4/` framework dirs changed | Run `verify_framework.py --strict` | Stale pointer, matrix gap, token budget violation created mid-Phase |
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

## Phase 22 — Self-Improving Framework via Auto-Fix PR 🔲 Planned

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
| `docs/templates/script/propose_framework_fix.py` | `--type`, `--document`, `--gap-description` | Creates branch on `project_starter_v4`, edits template, opens PR via `gh pr create` |

### PR format (auto-generated)

```
Title: [Auto-fix] {type} / {document}: add {gap description} guidance

Body:
Detected gap: {type} projects using {document} have no template
guidance for {gap description}.

Fix: added {section/example/row} to template.

Source: diagnosed from project spec quality check (no project
content included).
```

### Integration

| File | Change |
|---|---|
| `docs/templates/script/diagnose_spec.py` | New: takes spec quality check output → classifies each problem as project-level or framework-level → calls `propose_framework_fix.py` for framework gaps; accepts `--round 1\|2` flag; on round 2 writes remaining gaps to `logs/framework-gaps.md` instead of opening more PRs |
| `docs/templates/sprint-sync.md` | Add optional sprint-end step: run `diagnose_spec.py --round 1`, merge or skip PRs, then run `--round 2`; stop after round 2 |
| `README.md` | Add "Self-improving loop" section: diagram + iteration limit explanation + how to run `diagnose_spec.py` |

**Token impact:** zero — AGENTS.md unchanged.

---

## Phase 23 — Task / Sprint Quality Gate 🔲 Planned

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

## Phase 24 — Module Flow Coverage & Quality Check 🔲 Planned

`verify_docs.py` audits top-level spec files. `docs/modules/` has no equivalent: scan_codebase.py may surface 5 pipeline stages, but 2 may have no flow file, and the 3 that exist may have empty Input/Output contracts. No tool catches either gap today.

**Goal:** Add `verify_module_docs.py` — cross-reference the module list from scan_codebase.py against `docs/modules/`, then verify each flow file's required sections contain real content, gated by module type × project type.

### New script

```
docs/templates/script/verify_module_docs.py

Usage:
  python3 docs/script/verify_module_docs.py --project-type TYPE
  python3 docs/script/verify_module_docs.py --project-type TYPE --src PATH --docs PATH
  python3 docs/script/verify_module_docs.py --project-type TYPE --strict
  python3 docs/script/verify_module_docs.py --project-type TYPE --json
```

**Coverage check** — for every module returned by scan_codebase.py, confirm `docs/modules/[module]/[module]-module-data-flow.md` exists.

**Content quality check — required sections by module type:**

| Module type | Required content |
|---|---|
| **Pipeline Stage** | `Input` block: Source, Format, Schema non-empty; `Output` block: Destination, Format non-empty; `Error Handling` section: transient + missing-input entries (≥ 3 lines each) |
| **Feature** | At least one operation block with real `Function:` + `File:` values (not placeholder); every declared operation either filled or explicitly marked `Not Supported` |
| **Background Job** | `Trigger:` non-empty; success path (`→ acknowledge / commit`) present; `Error Handling` section: transient + permanent entries (≥ 3 lines each) |
| **Shared Utility** | `plantuml` class block present and non-empty; at least one method with real signature (not placeholder `[method]`); `Used by` table has ≥ 1 row with real module name and purpose |

**Project type → expected primary module type:**

| Project type | Primary module type |
|---|---|
| Data Pipeline, ML Pipeline | Pipeline Stage |
| Web App, LLM App | Feature, Background Job |
| CLI Tool | Feature (subcommand) |
| Microservices | Feature (per-service entry point) |
| Library / SDK | Shared Utility |

**Output format:**

```
Module Flow Coverage & Quality — data-pipeline
────────────────────────────────────────────────────────
Module            Type             Flow file    Quality
ge-validation     Pipeline Stage   ✅ Present   ⚠️  Missing Output contract
dbt-transform     Pipeline Stage   ✅ Present   ✅  Fully filled
datahub-ingest    Pipeline Stage   ✅ Present   ⚠️  Error Handling < 3 lines
model-training    Pipeline Stage   ❌ Missing   —

Coverage : 3 / 4 modules documented
Quality  : 1 / 3 existing flow files fully filled
```

### Integration

| File | Change |
|---|---|
| `docs/templates/sprint-sync.md` | Add checklist item `[Types: All]`: "Run verify_module_docs.py — all modules covered + quality PASS" |
| `document-purposes-common.md` | Add `verify_module_docs.py` entry: purpose, when to run, output interpretation |
| `docs/templates/script/verify_framework.py` | Add Check: per-type section rules in `verify_module_docs.py` cover all 9 project types and all 4 module types |
| Phase 20 / 21 `.githooks/pre-commit` (already planned) | Note: add `verify_module_docs.py` to hook chain once this Phase ships |

**Token impact:** zero — AGENTS.md unchanged. Script is not referenced at startup; entry in document-purposes-common.md is load-on-demand.

---

