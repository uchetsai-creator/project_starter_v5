# Codebase Map

<!--
  Tracks which layer each file belongs to, and whether it is package usage or custom logic.
  Update incrementally after each task is completed.
  Do not scan the entire repository.

  Type must be: Package / Custom
  Layer must be one of: DB / BE / FE / MOD / JOB / STAGE / CLI / LIB

  Layer definitions:
    DB    — schema files, migrations, seed scripts
    BE    — backend application code (controller, service, repository, middleware, etc.)
    FE    — frontend application code (page, component, hook, store, etc.)
    MOD   — cross-layer shared logic (state machine, data mapper, shared utility used by multiple layers)
    JOB   — background jobs, queue consumers, scheduled tasks, event handlers (not part of request/response cycle)
    STAGE — pipeline stage (Data Pipeline / ML Pipeline: extract, transform, load, train, evaluate, etc.)
    CLI   — CLI entry point, command parser, flag definitions (CLI Tool)
    LIB   — public API surface, exported functions/classes (Library / SDK)

  Use only the layers that apply to your project type.
  Web App / Microservices: DB, BE, FE, MOD, JOB
  Data / ML Pipeline:      DB, STAGE, MOD, JOB
  CLI Tool:                CLI, MOD
  Library / SDK:           LIB, MOD
  AI / LLM App:            BE, MOD, JOB (or STAGE if pipeline-structured)

  Custom code should only appear in the following contexts
  (per the Package First principle in AGENTS.md):
  - Business Logic
  - Domain Rules
  - Data Mapping
  - System Integration

  If a Custom entry does not fall into one of these four contexts,
  flag it for review — it may be replaceable with a package.
-->

## Page Structure Overview

<!--
  This section provides a visual overview of the frontend page/screen structure.
  Rendered by build_pdf.py — no separate generation step needed.

  Fill in the actual pages/screens and their relationships from your project.
  If this project has no frontend, remove this section and the marker below.
-->

```component
title: Page Structure

component "[e.g., Auth Pages — Login / Register]" as Auth {
  provides: [e.g., login form, register form]
  requires: [e.g., API Client]
}

component "[e.g., Dashboard]" as Dashboard {
  provides: [e.g., overview, stats]
  requires: [e.g., API Client, Auth]
}

component "[e.g., [Feature] Pages]" as Feature {
  provides: [e.g., list view, detail view, form]
  requires: [e.g., API Client, Auth]
}

component "[e.g., API Client]" as API {
  provides: [e.g., HTTP calls, auth headers]
  requires: [e.g., Backend API]
}

Auth --> API : calls
Dashboard --> API : calls
Feature --> API : calls
```

<!-- diagram: codebase-map-component -->

---

## Project Structure

<!--
  Show the full project root — not just the source folder.
  Include docs/, config files, and any other top-level folders.
  Annotate every meaningful folder and file with ← description.

  For the source folder, annotate each module with its documentation status:
    ✅  fully documented (module-data-flow.md exists)
    ❌  not yet documented
    —   shared utility / infrastructure (does not need a flow file)

  To auto-generate and update this section, run:
    python3 docs/script/scanners/scan_codebase.py <src_dir> --update docs/codebase-map.md

  Re-run after every module is completed to keep coverage status current.
-->

```
[project-root]/
├── docs/                             ← planning, specs, architecture docs
│   ├── architecture/                 ← system structure docs
│   ├── business/                     ← business process and object docs
│   ├── modules/                      ← per-module flow and log files
│   ├── specs/                        ← data model, API contract, permissions, logging
│   └── script/                       ← diagram generators, PDF builder, scan tool
│
├── [src]/                            ← application source code
│   ├── [module-a]/        ✅         ← [short description, e.g., order management]
│   ├── [module-b]/        ❌         ← [short description]
│   ├── [jobs]/            ✅         ← [background jobs, queue consumers]
│   └── [lib]/             —          ← [shared utilities, no flow file needed]
│
├── [migrations/ or schema/]          ← database schema and migrations (omit for CLI/Library/LLM script)
├── [docker-compose.yml]              ← local infrastructure services
├── [package.json / go.mod / etc.]    ← dependency manifest
└── ...
```

---

## Coverage Summary

<!--
  Updated by scan_codebase.py --coverage, or manually after each module is documented.
  This table gives a quick view of what is and is not yet documented.
-->

| Module / Folder | Type | Status | Flow file |
|---|---|---|---|
| `[src/module-a]` | Feature | ✅ Documented | `docs/modules/module-a/module-a-module-data-flow.md` |
| `[src/jobs/order-consumer]` | Background Job | ✅ Documented | `docs/modules/order-consumer/order-consumer-module-data-flow.md` |
| `[src/module-b]` | Feature | ❌ Not documented | — |
| `[src/lib]` | Shared Utility | — Not required | — |

---

## [Feature / Module Name]

<!--
  Module type: Feature | Background Job | Shared Utility | Infrastructure
  Add one section per module as tasks are completed.
-->

| File | Layer | Type | Description |
|---|---|---|---|
| `[file path]` | DB | Custom | [e.g., Order schema migration] |
| `[file path]` | BE | Custom | [e.g., Order business logic] |
| `[file path]` | BE | Package | [e.g., framework router / CLI parser / DAG task wrapper] |
| `[file path]` | FE | Custom | [e.g., Order list page component] |
| `[file path]` | FE | Package | [e.g., data fetching / state management library] |
| `[file path]` | MOD | Custom | [e.g., Cross-layer order state machine] |

---

## [Background Job / Queue Consumer Name]

<!--
  Module type: Background Job
  Use JOB layer for all files that are not part of the HTTP request/response cycle.
-->

| File | Layer | Type | Description |
|---|---|---|---|
| `[file path]` | JOB | Custom | [e.g., Order event consumer — listens for OrderCreated] |
| `[file path]` | JOB | Package | [e.g., BullMQ worker setup] |
| `[file path]` | BE | Custom | [e.g., Order service called by the consumer] |

---
