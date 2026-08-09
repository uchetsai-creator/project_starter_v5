# Document Purposes — Common (All Project Types)

<!--
  Reference only. Not read every task.
  Load this file together with document-purposes-[your-type].md.
  This file covers documents that apply to all project types.
  See document-purposes.md for the type-to-file lookup table.
-->

## Specs (docs/specs/)

### research.md
**Applies to: All project types**

Update when (if listed in current-state.md → Doc Checklist, update at task level; otherwise defer to Sprint Documentation Sync):
* New technology decisions are made
* NEEDS CLARIFICATION items are resolved
* Architecture decisions change

### specs/quickstart.md
**Applies to: All project types**
For Library / SDK: covers local dev setup and running tests, not a server startup.
For CLI Tool: covers installation and first-run verification.

Purpose:
Step-by-step guide for setting up and running the project locally.
Covers prerequisites, environment variables, startup commands, and verification steps.

Update when (if listed in current-state.md → Doc Checklist, update at task level; otherwise defer to Sprint Documentation Sync):
* Setup steps change
* New prerequisites are added
* Verification steps change
* Environment variable requirements change

### specs/test-plan.md
**Applies to: All project types**
For Data Pipeline / ML Pipeline: use Contract (GE/pandera), Integration (dbt test), E2E (full pipeline run), and Fault Injection levels instead of Unit/Component.
For IaC / DevOps: use policy unit tests, terraform plan (integration), and full apply-verify-destroy (E2E).
For Mobile App: use unit (business logic), component (single screen), integration (screen + backend), and E2E (Detox / Maestro).

Purpose:
Describes the testing strategy — what will be tested, at which levels, with which tools, and what the CI gate requires.
Actual test results go in test-report.md.

Update when (defer to Sprint Documentation Sync):
* Testing strategy, tool choices, or test levels change
* CI gate configuration changes
* Test environment changes
* Coverage targets change

### specs/test-report.md
**Applies to: All project types**

Purpose:
Records the actual results of each test run — pass/fail counts, coverage, known issues.
For Data Pipeline / ML Pipeline: records GE checkpoint results, dbt schema test counts, E2E pipeline task results, and fault injection (break-kit) outcomes.
This file describes WHAT was found, not the plan; the plan lives in test-plan.md.

Update when (defer to Sprint Documentation Sync):
* A new test run is completed
* Bugs are found and fixed
* Coverage changes significantly
* Known Issues / Known Gaps section changes

### specs/glossary.md
**Applies to: All project types (Optional — create on demand)**

Purpose:
Shared definition of domain terms, business concepts, technical abbreviations, and naming conventions
used across the project. Prevents terminology drift between the codebase, specs, and stakeholder documents.
Useful when the project introduces concepts that are non-obvious to a new team member or external reviewer.

Create when: the project's domain vocabulary is non-trivial — e.g., the team disagrees on what a term means,
or a concept appears in multiple specs without a single authoritative definition.
Do not create it just because a project exists — only create when there are actual terms to define.

Update when (defer to Sprint Documentation Sync):
* A new domain term is introduced or an existing definition changes

### specs/dependencies.md
**Applies to: All project types (Optional — create on demand)**

Purpose:
Track external dependency versions, upgrade policy, and known compatibility constraints.
Covers runtime packages, dev tools, infrastructure clients, and external service SDKs.
Complements the project's package manager lock files by documenting the *why* behind
version constraints and the policy for when and how to upgrade.

Create when: the project has non-trivial version constraints (e.g., locked to a specific major version
due to a breaking change), or when multiple team members need to agree on an upgrade cadence.

Update when (defer to Sprint Documentation Sync):
* A dependency is upgraded or a constraint is added
* A known incompatibility is discovered or resolved

### logging-spec.md
**Applies to: Web App, CLI Tool, Data Pipeline, ML Pipeline, Microservices, AI / LLM Application**
Not applicable to Library / SDK (libraries should not configure logging; callers own that).
Not applicable to IaC / DevOps (no application logging layer).

Purpose:
Define logging rules, format, and module naming conventions.
Logger instantiation pattern is documented here in a language/framework-agnostic way —
use whatever the project's logging library provides.
All modules must follow this spec.

Update when (if listed in current-state.md → Doc Checklist, update at task level; otherwise defer to Sprint Documentation Sync):
* New modules are added (add one line to the Module Naming Convention table)
* Log format changes
* Logger instantiation pattern changes

This file is the rule definition only — do not add module-specific logging content here.
Module-specific log points live in docs/modules/[module]/log-[module].md.

---

## Architecture (docs/architecture/)

### architecture.md
**Applies to: All project types**
For Microservices: also create a system-level architecture.md showing all services together.

Purpose:
Describe system component overview and data flow.
Contains a ```plantuml component diagram block rendered automatically by build_pdf.py.
Component type is a free-form label — use whatever best describes the component's role.

Update when (if listed in current-state.md → Doc Checklist, update at task level; otherwise defer to Sprint Documentation Sync):
* New components are added
* Data flows change
* Integration changes

After updating, regenerate diagram:
`Edit the ```plantuml block in the file, then run build_pdf.py`

---

## Flows (docs/modules/)

### module-data-flow.md
Purpose:
Index and rule definition for module-level code flows. Sits at `docs/modules/module-data-flow.md`.
Defines four module types — Feature, Background Job, Pipeline Stage, Shared Utility — each with its own flow format.
Pipeline Stage is used in Data Pipeline and ML Pipeline projects for stages that consume upstream data and produce downstream data.
Each module gets its own subfolder (`docs/modules/[module]/`) with its own flow file.

Update when (at module completion, together with the module's flow file — see AGENTS.md → Module Completion Check):
* A new module is created — add a row to the Module Flow Files table

### [module]-module-data-flow.md
Purpose:
Track code-level execution flow (function names, file paths) for a specific module.
Declare the module type at the top: Feature / Background Job / Pipeline Stage / Shared Utility.
Flow format follows the matching format defined in module-data-flow.md — do not assume
Controller/Service/Repository; use the real layer names from the codebase.
Also includes a class block describing the module's structure.

Location: `docs/modules/[module]/[module]-module-data-flow.md`
Examples: `docs/modules/order/order-module-data-flow.md`

Files matching this pattern are automatically included in the PDF.

Update when (only after the module is 100% complete — see AGENTS.md → Module Completion Check):
* Function names or file paths change for this module
* A new operation is implemented
* The module's class structure changes

After updating, regenerate class diagram:
`Edit the ```plantuml block in the file, then run build_pdf.py`

### module-flow.md
Purpose:
Index and rule definition for all module flow documents.
Each module has its own flow file: `docs/modules/[module]/[module]-flow.md`.

Update when (at module completion, together with the module's flow file — see AGENTS.md → Module Completion Check):
* A new module flow file is created — add a row to the Flow Files table

### [module]-flow.md
Purpose:
Describe cross-module service call sequences for a specific module.
Includes a Sequence Diagram for each cross-module process.
Business steps and decision branches belong in docs/business/[process-name]-process.md.

Location: `docs/modules/[module]/[module]-flow.md`
Example: `docs/modules/order/order-flow.md`

Files matching `*-flow.md` are automatically included in the PDF.

Update when (only after the module is 100% complete — see AGENTS.md → Module Completion Check):
* Cross-module service calls change
* A new cross-module process is added to this module

After updating, regenerate sequence diagram:
`Edit the ```plantuml block in the file, then run build_pdf.py`

### log-[module].md
Purpose:
Track every log point in a module, in call order. One file per module.
Not included in the PDF — this is an implementation detail reference for developers.

Location: `docs/modules/[module]/log-[module].md`
Generate and update at module completion only (see AGENTS.md → Module Completion Check).
Track function name or file path changes during development — apply all updates when the module reaches completion.

---

## Root-level (docs/)

### project-requirements.md
**Applies to: All project types**

Purpose:
Single source of truth for what the project must do — functional requirements (FR-XXX),
acceptance criteria (AC-XXX), scope boundaries, roles, non-functional requirements, and edge cases.
`verify_acceptance.py` reads this file to extract FR-XXX IDs and cross-references them against
`test-plan.md` (coverage) and `test-report.md` (results). A sprint cannot close out unless every
FR-XXX is covered in the test plan and the test report shows ✅ Pass.

Update when (if listed in current-state.md → Doc Checklist, update at task level; otherwise defer to Sprint Documentation Sync):
* A new feature or requirement is added — add an FR-XXX entry
* An acceptance criterion changes — update the matching AC-XXX entry
* Scope boundaries or roles change

### init/[type].md
**Applies to: All project types (one file per type)**

Purpose:
Per-type project initialization sequence. Contains the exact ordered list of files to create
when starting a new project of that type. Kept separate from AGENTS.md so the agent loads
only the one relevant file (~200–300 words) instead of all 7 sequences (~1,200 words).

Files: `init/web-app.md`, `init/cli-tool.md`, `init/library.md`, `init/data-pipeline.md`,
`init/ml-pipeline.md`, `init/microservices.md`, `init/llm-app.md`, `init/iac.md`, `init/mobile-app.md`

Load when: project is being initialized for the first time. Never needed for day-to-day tasks.
Update when: a new required document is added or removed for that project type.

### init/document-matrix.md
**Applies to: All project types**

Purpose:
Required / Optional / N/A table for every document, by project type. The single source of
truth for which files to create when initializing or retrofitting a project.
Extracted from AGENTS.md to keep AGENTS.md lean — agents load this only when initializing
or retrofitting, never during normal task work.

Load when: project is being initialized or retrofitted. Never needed for day-to-day tasks.
Update when: a new document template is added and its applicability per type needs recording.

### init/retrofit.md
**Applies to: All project types**

Purpose:
Step-by-step retrofit procedure (Steps 1–5) for applying this framework to an existing
codebase that has no prior documentation. Extracted from AGENTS.md to keep AGENTS.md lean.

Load when: retrofitting an existing project for the first time. Never needed otherwise.
Update when: the retrofit procedure changes.

### sprint-sync.md
**Applies to: All project types**

Purpose:
Sprint-end Document Update Checklist and Sprint Documentation Sync procedure. Kept separate
from AGENTS.md so it is never loaded during normal task work — only at sprint end.
Contains the full checklist with type filter, pre-filter quick-guide, per-item trigger conditions,
diagram regeneration commands, and consistency checks.

Load when: Sprint Documentation Sync runs (sprint end or when sprint-change-log.md has enough Pending entries).
During normal task work, use only the filtered `Doc Checklist` in `current-state.md` instead.
Update when: a new document type is added that needs a sprint-end check.

### current-state.md
Purpose:
The active task and the only file an Agent reads at startup. Self-contained — reading it
provides everything needed to start work and close out the task.

Contains:
- EXECUTION RULES comment block at the top (timeout rules, 5-minute stop rule)
- Current Task (name, goal, status)
- Required Context (only the files this task needs)
- Steps and Verify
- Next Task (pre-filled from project-plan.md so Agent does not need to re-read the plan)
- Doc Checklist (filtered per-task list of documents to check at completion)

Update when:
* Task starts — fill in Current Task, Required Context, Steps, Next Task; use the inline quick-filter guide in the current-state.md template to populate Doc Checklist (no other file needed for standard task types; load sprint-sync.md only for edge cases not covered by the guide)
* Task completes — apply Doc Checklist items, set Status to "Complete — Pending Sprint Doc Sync", mark steps [x], promote Next Task to Current Task, set Status to "In Progress" for new task

### changelog.md
Purpose:
Completed task history. Updated during Sprint Documentation Sync — not after every task.

Update when:
* Sprint Documentation Sync runs — move completed task summaries here from sprint-change-log.md

### task-log.md
Purpose:
Verification log — one row per completed task. AI agents must write a row here before
marking any task done, and every column must be ✅ before the row can be written.
This forces all post-task steps to be completed before reporting done.
Prevents AI from reporting completion without actual execution or without updating docs.

Format:
`| date | task | files changed | verification | ✅/❌ result | plan | changelog | current-state | sprint-log |`

Column meanings:
- **plan** ✅ — project-plan.md row marked complete
- **changelog** ✅ — sprint-change-log.md entry added with Status: Pending documentation synchronization
- **current-state** ✅ — current-state.md updated (Status set, steps marked, Next Task promoted)
- **sprint-log** ✅ — sprint-change-log.md entry confirms the task is in the pending sync queue

All checklist columns must be ✅ before the row can be written.
Result must confirm the feature works — not just "no errors":
- ✅ "endpoint returns expected data", "UI shows correct state", "output matches expected value"
- ❌ "no errors in log" alone is not sufficient

For validation / guard logic: also verify that invalid input is rejected.
- ✅ "Fed invalid data → guard correctly blocked it"
- ❌ "All checks passed on clean data" alone is not sufficient

Update when:
* Any task is completed — AI writes one row after completing ALL mandatory post-task steps

### sprint-change-log.md
Purpose:
Lightweight record of implementation changes during a sprint. Acts as memory between
development tasks and sprint-level documentation synchronization. The AI adds one entry
here per completed task instead of immediately updating all spec/architecture documents.
At sprint end, run Sprint Documentation Sync (see AGENTS.md) to process all Pending entries.

Format: one entry per task with implementation summary, technical impact flags
(Architecture/DB/API/Deployment/Module flow), potential documentation updates, and status.

Update when:
* Any task is completed — AI adds one entry with Status: Pending documentation synchronization
* Sprint Documentation Sync runs — AI updates Status to: Documentation synchronized — [date]

### codebase-map.md
Purpose:
Track which files are package usage vs custom logic, classified by layer (DB/BE/FE/MOD/JOB).
Includes a project tree (from project root) with documentation coverage status per module.
Used to verify the Package First principle is being followed.
Also serves as the project overview section in the PDF — a page structure component diagram
is injected here so readers get a visual of the frontend structure before diving into the file listing.

Update when:
* Sprint Documentation Sync runs — add files touched during the sprint, refresh tree view
* Re-run `python3 docs/script/scanners/scan_codebase.py <src_dir> --project-type <type> --update docs/codebase-map.md`
  to refresh the tree view and coverage summary
* Frontend page/screen structure changes — update the component block in this file

Do not update after every task — defer to Sprint Documentation Sync.

Do not scan the entire repository to regenerate this file. Update incrementally, one task at a time.

Diagram: Page structure component diagram — update the ```component block in codebase-map.md,
then run `Edit the ```plantuml block in the file, then run build_pdf.py` to regenerate.
The output (`codebase-map-component.html`) is picked up automatically by `build_pdf.py`.

---


## Scripts, Adapters & Diagram Tooling

Moved to `guidance/document-purposes/scripts-reference.md` -- covers every script
under `docs/script/`, the adapter files under `adapters/`, and the diagram-tooling
reference table. Load that file only when you need script/CLI-flag details, not for
normal document-purpose lookups.
