# AGENTS

## Path Convention

Module flow files live in: `docs/modules/`
Codebase map lives in: `docs/codebase-map.md`
Document purposes reference lives in: `guidance/document-purposes-common.md` + `guidance/document-purposes-[type].md`; see `guidance/document-purposes.md` for the type-to-file lookup table

If your project uses different folder names, search-replace the paths in this file
before starting. For example, if you use `docs/flows/` instead of `docs/modules/`:
  - Search: `docs/modules/`
  - Replace: `docs/flows/`
  - Also update `pdf_allowlist.py` to match.

---

## Project Type

Declare the project type at the top of your project's AGENTS.md.
The type gates which documents are required and which are N/A — do not create N/A documents.

**Supported types:**

| Type | Description |
|---|---|
| **Web App** | Backend + optional frontend, HTTP/GraphQL API, user auth, persistent DB |
| **CLI Tool** | Command-line interface, subcommands, flags, stdin/stdout; no persistent server |
| **Library / SDK** | Reusable package published to a registry; callers import it; no deployment |
| **Data Pipeline** | ETL/ELT batch or streaming; data in → data out; no user-facing API |
| **ML Pipeline** | Training → evaluation → serving; model artifact is the primary output |
| **Microservices** | Multiple independently deployed services communicating via API or events |
| **AI / LLM Application** | Chatbot, copilot, or agent built on a foundation model; prompt-driven, no model training |
| **IaC / DevOps** | Infrastructure-as-Code or DevOps tooling; Terraform, Pulumi, Ansible, Helm; resource topology, runbooks, drift policy |
| **Mobile App** | Native or cross-platform mobile app (React Native, Flutter, iOS/Swift, Android/Kotlin); screen-based, app-store distributed |

### Mixed / Hybrid Project Types

Some projects genuinely span more than one type. Declare both using `+` (e.g. `Project Type: Data Pipeline + Web App`).

**Document rule for hybrid projects:** create all documents that are Required (✅) or Optional (⚠️) for ANY of the declared types. Skip only documents that are N/A (❌) for ALL declared types.

**Common combinations:**

| Combination | What the second type adds |
|---|---|
| Data Pipeline + Web App | `api-contract.md`, `permissions.md`, `frontend.md` (dashboard/admin UI) |
| CLI Tool + Library | `public-api.md`, `compatibility-matrix.md` (the tool also ships as an importable package) |
| ML Pipeline + Web App | `api-contract.md`, `permissions.md` (model served via REST endpoint) |
| AI / LLM App + Web App | `api-contract.md`, `frontend.md`, `deployment.md` (hosted chatbot with UI) |

**Document matrix (Required/Optional/N/A by project type):** `templates/init/document-matrix.md`
Load only when initializing or retrofitting — not during normal task work.

---

## Project Initialization

Read the init file that matches your project type — it contains the full step-by-step setup sequence.
**Load only the one file that matches your type. Do not load the others.**

| Project type | Init file |
|---|---|
| Web App | `templates/init/web-app.md` |
| CLI Tool | `templates/init/cli-tool.md` |
| Library / SDK | `templates/init/library.md` |
| Data Pipeline | `templates/init/data-pipeline.md` |
| ML Pipeline | `templates/init/ml-pipeline.md` |
| Microservices | `templates/init/microservices.md` |
| AI / LLM Application | `templates/init/llm-app.md` |
| IaC / DevOps | `templates/init/iac.md` |
| Mobile App | `templates/init/mobile-app.md` |

For mixed / hybrid types, load each relevant init file and union the step lists (skip duplicates).

---

## Retrofitting an Existing Project

Load `templates/init/retrofit.md` for the full step-by-step retrofit procedure (Steps 1–5).
Not needed during normal task work on an established project.

---

If continuing an existing project:

**Startup sequence — read in this order, stop as soon as you have enough context:**

1. `docs/current-state.md` — this is the only mandatory read at startup.
   It tells you the current task AND lists exactly which other documents to read.
2. Required Context only — read the documents listed in `docs/current-state.md → Required Context`.
   Nothing else. Do not scan the repository.

Do NOT read docs/project-plan.md, docs/project-requirements.md, or docs/changelog.md
at startup unless docs/current-state.md explicitly lists them in Required Context.

If docs/current-state.md is missing, empty, or ambiguous — read AGENTS.md to orient yourself,
then determine the next step from project-plan.md. Do not read AGENTS.md otherwise.

For what each document is for and when it changes, read guidance/document-purposes-common.md + guidance/document-purposes-[your-type].md — reference only, not required every task. See guidance/document-purposes.md for the type-to-file lookup table.

---

## Writing Audience

Spec PDF documents are read by external stakeholders — no internal tracking references allowed:
- No task numbers: （Task 22）, (Task 15), etc.
- No sprint references: Sprint 8, S9, etc.

Spec-facing docs: `business/business-rules.md`, `specs/pipeline-contract.md`, `specs/research.md`,
`architecture/*.md`, `modules/*/*-module-data-flow.md`, `specs/quickstart.md`

Record WHEN a rule changed in `changelog.md` — not in spec documents.

---

## Development Principles

- **Maintainability First** — prefer readable, changeable architecture over temporary shortcuts
- **Package First** — use existing packages, utilities, and framework conventions before writing custom code
  - Priority: existing package → existing utility → framework convention → custom code
  - Custom code only for: business logic, domain rules, data mapping, system integration
- **Glue Code** — keep integration code thin; logic belongs in packages, not connectors
- **Incremental Changes** — make the smallest change that achieves the goal
- **No Unrelated Refactor** — do not clean up code outside the current task scope

---

## Current State

docs/current-state.md is the active task. It is self-contained — reading it should give you
everything needed to start work and to close out the task when done.

### Starting work

1. Read `docs/current-state.md`.
2. If **Current Task** is filled in:
   - Read the files listed under **Required Context**.
   - Start implementation.
3. If **Current Task** is empty or says "See project-plan.md":
   - Read `docs/project-plan.md` (this is the only time you need to).
   - Copy the next incomplete task's name, goal, required context, and the task after that into current-state.md.
   - Start implementation.

### Closing out a task

current-state.md is a state machine with two fields:

- **Current Task** → the task being worked on now
- **Next Task** → pre-filled when current task was set up; becomes the new Current Task on closeout

**When setting up a new Current Task** (not at closeout):
- Use the quick filter guide in `docs/current-state.md → Doc Checklist` comment block to populate the checklist.
  For task types not covered by the quick filter, load `templates/sprint-sync.md → Document Update Checklist`.
- Write the filtered list into `docs/current-state.md → Doc Checklist`.
- Do not re-open AGENTS.md at task closeout — the filtered list in current-state.md is sufficient.
- If the task adds or removes files, add any ASCII file-tree diagrams in README.md (or equivalent docs) to the Doc Checklist — update the tree to reflect the new layout.
- If the task goal involves debugging a failure or investigating unexpected output, add the relevant debug guide to Required Context:
  - Pipeline stage failure / wrong row count / data quality issue → `docs/specs/pipeline-debug.md`
  - LLM wrong answer / low eval score / tool call failure / retrieval issue → `docs/specs/llm-debug.md`

**When all Steps are done and Verify passes**, follow the **Closeout** section in `docs/current-state.md` — all steps are listed there. Load `templates/task-completion.md` only if you need the full verification table or step detail.

### Module Completion Check

> Load `templates/module-completion.md` when a module is confirmed 100% complete. Skip otherwise.

---

## Task Completion

> For standard closeouts, follow the **Closeout** section in `docs/current-state.md` — no extra file load needed.
> Load `templates/task-completion.md` only if you need the full verification table or step detail.

---

## Sprint Documentation Sync

> Load `templates/sprint-sync.md` only at sprint end — not during normal task work. It contains the full sprint sync procedure and Document Update Checklist.
