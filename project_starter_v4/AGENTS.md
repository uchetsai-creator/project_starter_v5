# AGENTS

## Path Convention

Module flow files live in: `docs/modules/`
Codebase map lives in: `docs/codebase-map.md`
Document purposes reference lives in: `document-purposes.md` (repo root)

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

### Mixed / Hybrid Project Types

Some projects genuinely span more than one type. Declare both types using `+`:

```
Project Type: Data Pipeline + Web App
Project Type: CLI Tool + Library
Project Type: ML Pipeline + Web App
Project Type: AI / LLM Application + Web App
```

**Document rule for hybrid projects:** create all documents that are Required (✅) or Optional (⚠️) for ANY of the declared types. Skip only documents that are N/A (❌) for ALL declared types.

**Common combinations:**

| Combination | What the second type adds |
|---|---|
| Data Pipeline + Web App | `api-contract.md`, `permissions.md`, `frontend.md` (dashboard/admin UI) |
| CLI Tool + Library | `public-api.md`, `compatibility-matrix.md` (the tool also ships as an importable package) |
| ML Pipeline + Web App | `api-contract.md`, `permissions.md` (model served via REST endpoint) |
| AI / LLM App + Web App | `api-contract.md`, `frontend.md`, `deployment.md` (hosted chatbot with UI) |

Documents are NOT split into separate folders — all docs live in the same `docs/` folder.
The second type's documents simply join the first type's `docs/specs/` or `docs/architecture/`.

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
   Nothing else.

Do NOT read docs/project-plan.md, docs/project-requirements.md, or docs/changelog.md
at startup unless docs/current-state.md explicitly lists them in Required Context.

If docs/current-state.md is missing, empty, or ambiguous — read AGENTS.md to orient yourself,
then determine the next step from project-plan.md. Do not read AGENTS.md otherwise.

Do not scan repository.

For what each document is for and when it changes, read document-purposes.md — reference only, not required every task.

---

## Development Principles

- Prefer maintainable architecture over temporary shortcuts
- Maintainability First
- Package First
- Glue Code
- Incremental Changes
- No Unrelated Refactor

---

## Package First

Priority:
1. Existing package
2. Existing utility
3. Framework convention
4. Custom code

Custom code only for:
- Business Logic
- Domain Rules
- Data Mapping
- System Integration

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
- If the task goal involves debugging a failure or investigating unexpected output, add the relevant debug guide to Required Context:
  - Pipeline stage failure / wrong row count / data quality issue → `docs/specs/pipeline-debug.md`
  - LLM wrong answer / low eval score / tool call failure / retrieval issue → `docs/specs/llm-debug.md`

**When all Steps are done and Verify passes**, follow **## Task Completion** below — all current-state.md edits happen there, once. No external files need to be read at closeout.

### Module Completion Check

Run this check after every task — most of the time the answer will be "no," but the check itself must not be skipped.

Do NOT create or update `[module]-module-data-flow.md` or `[module]-flow.md` during a task
unless the module is 100% complete (all tasks for this module are marked done in project-plan.md).
Creating these files mid-module causes repeated read/write cycles during review. Defer until completion.

* Does completing this task finish all work for its module in docs/project-plan.md?
  * If no: this module is not yet complete. Skip the rest of this section.
  * If yes: this module is now complete. Do all of the following:
    1. Insert logger calls into the module's code, following the rules in docs/specs/logging-spec.md.
       Use the logger instantiation pattern defined in logging-spec.md for this project's language/framework.
       Direct print/console statements are not allowed.
       logging-spec.md itself is the rule definition — do not add module-specific content to it.
       Create or update docs/modules/<module-name>/log-<module-name>.md to list every log point added, in call order.
    2. Ask: "Would you like to add debug instrumentation to this module? (follows debug-instrumentation-rules.md)"
       * If yes: follow debug-instrumentation-rules.md and instrument the module.
       * If no: continue.
    3. If the module flow file contains multiple sequence or class blocks, each block
       generates its own diagram file (named by title slug). All are picked up automatically
       by build_pdf.py — no extra configuration needed.
    4. Rebuild the PDF only if ANY of the following conditions are met:
       - This is a Sprint Documentation Sync (always rebuild at sprint end), OR
       - 3 or more diagram blocks (plantuml) have changed since the last PDF build.
       If neither condition is met, skip the PDF rebuild — it will happen at sprint end.

       When rebuilding:
       `python3 docs/script/build_pdf.py docs --lang en -o docs/project-documentation-en.pdf`
       Chinese PDF is manual only — run when requested:
       `python3 docs/script/build_pdf.py docs-zh --lang zh -o docs/project-documentation-zh.pdf`
       Note: to add a new doc to the PDF, add it to docs/script/pdf_allowlist.py only —
       do not edit build_pdf.py for this purpose.


---

## Task Completion

**Workflow: Task completed → minimal writes only. Sprint completed → synchronize all documentation.**

Do NOT update changelog.md, project-plan.md, codebase-map.md, or any spec/architecture/business document after a single task — defer to Sprint Documentation Sync.

### Mandatory post-task steps (every task)

1. **Apply Doc Checklist, then update `docs/current-state.md`** (1 edit block, in this order):
   a. Apply each item in `docs/current-state.md → Doc Checklist` — update the listed doc files now.
      These are the only doc updates that happen at task level. Do not open the full Document Update Checklist in AGENTS.md.
   b. In `docs/current-state.md`, while Current Task is still the old task:
      - Set **Status** to `Complete — Pending Sprint Doc Sync`
      - Mark completed steps `[x]`
   c. Now promote Next Task → Current Task:
      - Copy **Next Task** → **Current Task** (name, goal)
      - Look up the task after upcoming in project-plan.md → write it into **Next Task**
        (upcoming → Current Task; the task after upcoming → Next Task)
      - Update **Required Context** for the new current task
      - Update **Doc Checklist** → already filtered when this task was set up; replace with filtered list for the new task
      - Set **Status** to `In Progress`

2. **Run verification** for what was changed:

| Changed artifact | Required verification |
|---|---|
| New feature / endpoint | Call the endpoint, confirm expected response |
| Database migration / schema | Run migration, confirm schema matches expected state |
| Config / environment | Start affected service, confirm healthy |
| Network / infrastructure config | Verify connectivity between affected services (e.g. `docker exec serviceA ping serviceB`) |
| Script / utility | Run the script, confirm expected output |
| Documentation only | `python3 docs/script/build_pdf.py docs --lang en -o /tmp/test.pdf` |
| Diagram (plantuml block) | Rebuild PDF, confirm diagram renders correctly |

Verification must confirm the feature works — not just that no errors occurred.
- ❌ "No errors in log" is not sufficient
- ✅ "Endpoint returns expected data", "UI shows correct state", "output matches expected value"

For validation / guard logic: verify that invalid input is correctly rejected.
- ❌ "All checks passed on clean data" alone is not sufficient
- ✅ "Fed invalid data → check correctly returned failure"

3. **Add one entry to `docs/sprint-change-log.md`** (1 edit):
   - Implementation summary, technical impact flags (Architecture/DB/API/Deployment/Module flow), potential documentation updates.
   - Status: **Pending documentation synchronization**
   - Insert chronologically — append after the last existing entry, not at the top.

4. **Write one row to `docs/task-log.md`** (1 edit):

`| [date] | [task] | [files changed] | [command run] | ✅/❌ [result] | current-state ✅ | sprint-log ✅ |`

---

## Sprint Documentation Sync

> **Load `templates/sprint-sync.md` now.** It contains the full sprint sync procedure and Document Update Checklist.
> Do not load it during normal task work — only at sprint end.

### Document Update Checklist

> Full checklist is in `templates/sprint-sync.md` — load it now if running Sprint Documentation Sync.
> During normal task work, use only the filtered list in `docs/current-state.md → Doc Checklist`.
