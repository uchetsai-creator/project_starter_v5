# AGENTS

## Constitution

These rarely change — everything else in this file is operational mechanics built on top
of them. When a task pressures you to bend one of these, stop and ask instead of bending it.

- **Maintainability First** — prefer readable, changeable architecture over temporary shortcuts
- **Package First** — use existing packages, utilities, and framework conventions before writing custom code
  - Priority: existing package → existing utility → framework convention → custom code
  - Custom code only for: business logic, domain rules, data mapping, system integration
- **Glue Code** — keep integration code thin; logic belongs in packages, not connectors
- **Incremental Changes** — make the smallest change that achieves the goal
- **No Unrelated Refactor** — do not clean up code outside the current task scope
- **Type gates documents** — the declared project type decides which documents are required
  vs N/A; never create an N/A document "just in case"
- **No internal references in spec-facing docs** — no task numbers (Task 22), no sprint
  references (Sprint 8, S9); those belong in `changelog.md`, not in documents external
  stakeholders read (see Writing Audience below for the full file list)

---

## Path Convention

Module flow files live in: `docs/modules/`
Codebase map lives in: `docs/codebase-map.md`
Document purposes reference lives in: `guidance/document-purposes/common.md` + `guidance/document-purposes/[type].md`; see `guidance/document-purposes/index.md` for the type-to-file lookup table

If your project uses different folder names, search-replace the paths in this file
before starting. For example, if you use `docs/flows/` instead of `docs/modules/`:
  - Search: `docs/modules/`
  - Replace: `docs/flows/`
  - Also update `pdf_allowlist.py` to match.

---

## Project Type

Declare the project type at the top of your project's AGENTS.md.
The type gates which documents are required and which are N/A — do not create N/A documents.

> **Not sure which type fits?** Run `python3 detect_type.py` (or `bash setup.sh --detect`) to infer the type from your codebase or a plain-text description. It supports hybrid output (e.g. `web-app+llm-app`).

**Supported types:** Web App, CLI Tool, Library/SDK, Data Pipeline, ML Pipeline,
Microservices, AI/LLM Application, IaC/DevOps, Mobile App — see `guidance/project-types.md`
for the full description table.

### Mixed / Hybrid Project Types

Some projects genuinely span more than one type. Declare both using `+` (e.g. `Project Type: Data Pipeline + Web App`).

**Document rule for hybrid projects:** create all documents that are Required (✅) or Optional (⚠️) for ANY of the declared types. Skip only documents that are N/A (❌) for ALL declared types.

**Guidance file rule for hybrid projects:** `guidance/document-purposes/[type].md` and
`guidance/learning-checkpoints/[type].md` only exist per single type — for `A + B`, load
both `.../A.md` and `.../B.md` and union them, the same as the init-file rule below. There
is no `A+B.md` file to look for.

**Common combinations:** see `guidance/project-types.md` for illustrative examples
(Data Pipeline + Web App, CLI Tool + Library, ML Pipeline + Web App, AI/LLM App + Web App).

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

## Writing Audience

Spec PDF documents are read by external stakeholders — the Constitution's "no internal
references" rule applies to these files specifically:
`business/business-rules.md`, `specs/pipeline-contract.md`, `specs/research.md`,
`architecture/*.md`, `modules/*/*-module-data-flow.md`, `specs/quickstart.md`

Record WHEN a rule changed in `changelog.md` — not in spec documents.

---

## Learning Checkpoint

Runs every task, independent of doc/validator sync timing (see Sprint Documentation Sync
below) — this is live discussion during the task, not a file to write and defer.

- **Unfamiliar technology** (never used before) → run Checkpoint 0 first.
- **Modifying existing code** → run Checkpoint A before implementing.
- **New feature / no existing code** → run Checkpoint B before implementing.
- **Always, before Closeout** → run Checkpoint C (post-implementation review).

Load `guidance/learning-checkpoints/common.md` for triggers + question templates, and
`guidance/learning-checkpoints/[your-declared-type].md` for type-specific angles.

---

## Current State

docs/current-state.md is the active task. It is self-contained — reading it should give you
everything needed to start work and to close out the task when done.

### New requirement from the user

If the user describes a new requirement/feature in conversation that is NOT already a scoped
Current Task in `docs/current-state.md`, do not silently start implementing and do not
silently write a task breakdown from your own assumptions. Ask clarifying questions first —
scope, edge cases, acceptance criteria (see Learning Checkpoint B below) — then, with the
user's answers, update `docs/project-plan.md` and set `docs/current-state.md → Current Task`
before proceeding to "Starting work." A one-line request is rarely a fully-scoped task; treat
brevity from the user as a prompt to ask, not as permission to guess.

**Resolve project type before any of the above** if `.project-starter.yml`'s `project_type`
is missing or still `[your-project-type]` — every downstream step (which docs, which
validators, which guidance files) is selected by this value alone. Run
`python3 detect_type.py --requirements "<the user's description>"` for a ranked guess, confirm
it with the user, then write it into `.project-starter.yml` before asking anything else.

### Starting work

Run `python3 orchestrator.py` → read `.ai/WORKFLOW.md` and `.ai/AI_CONTEXT.md` → follow the Read list.

`orchestrator.py` calls `build-context.py` internally — both read the same `.project-starter.yml`.

Optional: run with `--adapter claude` (or `codex`) to also render the tool-native instruction file (`.claude/commands/start-task.md` / `.codex/`).

### Closing out a task

current-state.md is a state machine with two fields:

- **Current Task** → the task being worked on now
- **Next Task** → pre-filled when current task was set up; becomes the new Current Task on closeout

**When setting up a new Current Task** (not at closeout):
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

> Trigger is a count, not a calendar: after appending a `sprint-change-log.md` entry at
> Closeout, check how many entries are `Status: Pending documentation synchronization`.
> At 3, load `templates/sprint-sync.md` and run it now, before starting the next task —
> do not wait for a "sprint end" that may never arrive in a solo/small project.
