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

## Scripts (docs/script/)

### pdf_allowlist.py
Purpose:
Single source of truth for which files appear in the PDF, in what order, and under which section.
`build_pdf.py` imports from this file.

Update when:
* A new permanent document is added to `docs/` and should appear in the PDF

Do not edit `build_pdf.py` for this purpose — edit only this file.

### module-completion.md

Purpose:
Full Module Completion Check procedure. Extracted from AGENTS.md to keep the mandatory startup
payload lean — load only when a module is confirmed 100% complete.

Load when: a module's final task is done and all tasks for that module are marked complete in project-plan.md.
Never needed for mid-module tasks.
Update when: the module completion procedure changes (logging rules, PDF rebuild criteria).

### task-completion.md

Purpose:
Full mandatory post-task steps: Doc Checklist application, verification table, sprint-change-log entry,
task-log row. Extracted from AGENTS.md to keep the mandatory startup payload lean.

Load when: the inline Closeout summary in `docs/current-state.md` is insufficient — e.g., unfamiliar
with the verification table or the exact sprint-change-log entry format.
For standard closeouts, the Closeout section in current-state.md is sufficient.
Update when: the post-task procedure changes.

### .githooks/pre-commit
**Applies to: All project types**

Purpose:
Shell script that enforces process rules on every `git commit` — no AI tool dependency.
Runs the following checks on every commit:

**Quality verifiers** (4 scripts — Phase 17 + Phase 23 + Phase 24):
- `verify_docs.py --content` — document presence and fill quality
- `verify_logs.py` — log documentation coverage
- `verify_tests.py` — test coverage and report currency
- `verify_content.py` — spec content quality

**Process checks** (5 rules — Phase 21):
- `verify_framework.py` — framework file integrity
- AGENTS.md token budget — keeps startup context below limit
- Changelog audit trail — sprint-change-log entry required before commit
- Closeout completeness — current-state.md must be properly closed out
- Writing Audience violations — no task/sprint refs in spec-facing documents
Blocks the commit and shows output on failure. Works with Claude Code, Codex, Cursor, or manual commits.
Optional Claude Code Stop hook (`.claude/settings.json`) calls the same scripts for
mid-session fast feedback, writing results to `logs/verify-{timestamp}.json`.

**Note:** Process rules declared in `AGENTS.md` are enforced by this pre-commit hook,
not by agent memory. An AI tool or developer can silently violate them without the hook — install it.

Install: `cp .githooks/pre-commit .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit`
Requires `.project-starter.yml` at the project root with `project_type` set.
Update when: a new verifier is added — add an `if [ -f "docs/script/validators/[script].py" ]` block.
**Note:** The context builder (`build-context.py`) runs as pre-task setup — it is not part of this hook chain and does not run on commit.

### build-context.py
**Applies to: All project types**

Purpose:
Context Builder — generates `.ai/AI_CONTEXT.md`, a deterministic read list for the current task.
Reads `.project-starter.yml` (project_type, task_type) and `docs/current-state.md` (Task Type field),
then queries `document-registry.yaml` to produce three sections:
- **Read (Required)** — Required documents for the declared project type, sorted high → medium → low priority
- **Read (If Present)** — Optional documents relevant to the current task type
- **Skip** — everything else (N/A for type, or Optional but not relevant to this task)

`current-state.md` is always injected at the top of Read (Required).

The `Task Type:` field in `docs/current-state.md` overrides the `task_type` field in `.project-starter.yml`.
If neither is set, all Required documents for the project type are listed.

```bash
python3 build-context.py                          # generate for current task
python3 build-context.py --task-type sprint-end   # override task type
python3 build-context.py --dry-run                # preview without writing
```

`.ai/AI_CONTEXT.md` is gitignored — not committed. Regenerate whenever the task changes.
**Note:** `build-context.py` runs as part of pre-task setup, not the `.githooks/pre-commit` chain.

Update when: new task type mappings are needed, or `TASK_TYPE_DOCS` entries change.

### orchestrator.py
**Applies to: All project types**

Purpose:
Workflow Manager — generates `.ai/WORKFLOW.md`, a deterministic workflow plan for the current task.
Reads `.project-starter.yml` (project_type, task_type) and `docs/current-state.md` (Task Type field),
selects the matching validator sequence from `workflow-registry.yaml`, then calls `build-context.py`
internally so both context and workflow always reflect the same project type and task type.

The generated WORKFLOW.md lists pre-task setup, implementation guidance, post-task validators
(in execution order), and closeout steps — eliminating the need for AI agents to reason about
validator sequencing from AGENTS.md.

```bash
python3 orchestrator.py                          # generate workflow + context for current task
python3 orchestrator.py --task-type sprint-end   # override task type
python3 orchestrator.py --dry-run                # preview WORKFLOW.md without writing
```

`.ai/WORKFLOW.md` is gitignored — not committed. Regenerate whenever the task changes.

Update when: new task type mappings are needed, or validator sequences in `workflow-registry.yaml` change.

### workflow-registry.yaml
**Applies to: All project types**

Purpose:
Maps each `task_type` to an ordered validator sequence with extra flags.
Read by `orchestrator.py` at runtime to select the correct post-task validators.
The orchestrator injects `--project-type <type>` automatically — only extra flags (e.g. `--content`,
`--strict`) belong in the registry.

Contains one entry per task type plus a `default` fallback used when the task type is unset
or has no explicit mapping.

```yaml
workflows:
  feature:
    validators:
      - script: docs/script/validators/verify_docs.py
        args: [--content]
      - script: docs/script/validators/verify_content.py
        args: [--strict]
  default:
    validators:
      - script: docs/script/validators/verify_docs.py
        args: [--content]
```

Update when: a new task type is introduced, or the required validator set for an existing type changes.

### .ai/AI_CONTEXT.md
**Applies to: All project types**

Purpose:
Generated file — the ordered context list for the current task. Written by `build-context.py`.
AI tools read this file at startup instead of inferring context from AGENTS.md rules.

Not committed (excluded by `.gitignore`). Recreate with `python3 orchestrator.py` (or `python3 build-context.py` directly).

Do not edit manually — it is overwritten on each run.

### .ai/WORKFLOW.md
**Applies to: All project types**

Purpose:
Generated file — the deterministic workflow plan for the current task. Written by `orchestrator.py`.
Lists pre-task setup, implementation guidance, post-task validators (in execution order with exact
commands), and closeout steps. AI agents read this file to follow a mechanical plan rather than
reasoning about validator sequencing from AGENTS.md.

Not committed (excluded by `.gitignore`). Recreate with `python3 orchestrator.py`.

Do not edit manually — it is overwritten on each run of `orchestrator.py`.

### .project-starter.yml
**Applies to: All project types**

Purpose:
Single config file at the project root. Stores `project_type`, `docs_path`, and optional `task_type`.
Used by `.githooks/pre-commit`, all verify scripts, and `build-context.py` so type/path flags do not
need to be passed on every manual invocation.

```yaml
project_type: data-pipeline
docs_path: docs/
task_type:          # optional: feature | pipeline-stage | bug-fix | sprint-end | eval-run | iac-change
```

Created at project initialization (last step in each `init/[type].md`).
Do not rename — all scripts read this exact filename.


### verify_docs.py
Purpose:
Cross-references the declared project type against the document matrix and reports which
Required and Optional documents exist, are missing, or are inapplicable. Also flags Orphan
files — documents that exist in docs/ but are N/A for the declared type, or are not in the
matrix at all. Works in any project that copied the framework's scripts; has no runtime
dependency on the template files (matrix is hardcoded at implementation time).

Run after retrofitting, after Sprint Documentation Sync, or any time you want to confirm
the project's docs/ folder matches what the declared type requires.

```bash
python3 docs/script/validators/verify_docs.py --project-type web-app
python3 docs/script/validators/verify_docs.py --project-type data-pipeline+web-app
python3 docs/script/validators/verify_docs.py --project-type web-app --strict   # exits 1 if Required missing
python3 docs/script/validators/verify_docs.py --project-type web-app --json     # machine-readable output
python3 docs/script/validators/verify_docs.py --project-type web-app --content  # also check fill quality
```

Output statuses: ✅ Present · ❌ Missing Required · ⚠️ Missing Optional · — N/A · 🔍 Orphan

`--content` adds per-document fill score: placeholder detection, required section presence,
fill ratio (non-placeholder content lines / total content lines). Summary line: "Spec fill: N / M
documents fully filled". Use at sprint end before spec-review.md to identify which documents
need the LLM Judge rubric.

Update when: a new document is added to the framework and its Required/Optional/N/A status
per project type is defined — update the MATRIX dict in the script to match document-matrix.md.

### verify_logs.py
**Applies to: All project types where logging-spec.md is Required or Optional**
(web-app, cli-tool, data-pipeline, ml-pipeline, microservices, mobile-app, llm-app — not library or iac)

Purpose:
Audits log documentation quality. Checks two things:
(1) `docs/specs/logging-spec.md` has required sections filled (Log Output Format, Required Log Points,
Module Naming Convention) and documents trace_id for types that need request tracing.
(2) Each `docs/modules/[module]/log-[module].md` file documents trace_id, structured JSON/key=value fields,
and no raw print/console.log statements. Per-type addenda: pipeline row count field (data-pipeline, ml-pipeline),
LLM call log fields (llm-app).

Run at sprint end as part of the quality gate (step 4 of Sprint Documentation Sync).
Also runs automatically on `git commit` if `docs/script/validators/verify_logs.py` is present.

```bash
python3 docs/script/validators/verify_logs.py --project-type web-app
python3 docs/script/validators/verify_logs.py --project-type data-pipeline --strict
python3 docs/script/validators/verify_logs.py --project-type web-app --json
```

Output statuses: ✅ pass · ⚠️ warn · ❌ fail. Per-file: trace_id, structured format, per-type fields.
Verdict: PASS · WARN · FAIL. `--strict` exits 1 on any FAIL.

Update when: new per-type log field requirements are added (e.g., a new project type is introduced).

### verify_tests.py
**Applies to: All project types** (test-report.md is Required for all types)

Purpose:
Audits test report quality. Checks that `docs/specs/test-report.md` contains real results:
test count > 0, overall pass/fail status recorded, Results by Module populated with actual rows.
For Data Pipeline and ML Pipeline: also checks that the Contract Tests (quality gate) section
and Fault Injection Tests section are non-empty.

Run at sprint end as part of the quality gate (step 4 of Sprint Documentation Sync).
Also runs automatically on `git commit` if `docs/script/validators/verify_tests.py` is present.

```bash
python3 docs/script/validators/verify_tests.py --project-type web-app
python3 docs/script/validators/verify_tests.py --project-type data-pipeline --strict
python3 docs/script/validators/verify_tests.py --project-type web-app --json
```

Output: fill score (N / M checks passed), missing sections, Verdict PASS / WARN / FAIL.
`--strict` exits 1 on any FAIL.

Update when: the test-report.md template gains a new required section that should be enforced.

### verify_content.py
**Applies to: All project types**

Purpose:
Full document content quality gate. For every Required document in the project's declared type,
checks that each document's required sections contain real content — not placeholders — gated by
document × project type. Delegates module flow file audits to `verify_module_docs.py` internally.

Documents already covered by `verify_logs.py` (`logging-spec.md`) and `verify_tests.py`
(`test-report.md`) are skipped here to avoid duplication.

**Per-document quality rules:**

Universal (all types):
- `architecture.md` — plantuml component block non-empty; ≥1 real component (not placeholder `[Component]`); Mobile App: ≥1 screen/view component in diagram
- `quickstart.md` — Prerequisites ≥1 real item; ≥1 numbered setup step with real content; Verification step present
- `research.md` — ≥1 Decision entry non-placeholder; ≥1 Rationale entry non-placeholder
- `test-plan.md` — Testing Strategy section ≥3 lines; ≥1 test level (unit/integration/e2e) defined

Web App + Microservices:
- `api-contract.md` — ≥1 endpoint row with real Method + Path
- `permissions.md` — Role table ≥1 real role row; ≥1 permission described
- `data-model.md` — plantuml ER block with ≥1 entity defined
- `backend.md` — Stack section non-empty

Data Pipeline + ML Pipeline:
- `pipeline-contract.md` — Cross-stage table ≥1 row with non-placeholder Input + Output formats
- `pipeline-debug.md` — ≥1 scenario with real Symptom + Root cause
- `data-model.md` — same as above
- `backend.md` — same as above

ML Pipeline (additional):
- `model-contract.md` — Input schema ≥1 real field; Output format non-placeholder; ≥1 production threshold
- `experiment-log.md` — ≥1 entry with real Hypothesis + Result

CLI Tool:
- `cli-contract.md` — ≥1 subcommand defined; ≥1 flag or argument documented
- `release-guide.md` — Versioning policy non-empty; ≥1 publish step

Library / SDK:
- `public-api.md` — ≥1 real public function or class signature
- `release-guide.md` — same as CLI Tool
- `compatibility-matrix.md` — ≥1 runtime version row with Support status

Microservices (additional):
- `service-catalog.md` — ≥1 service row with real name, port, owner
- `service-contract.md` — ≥1 inter-service endpoint or event documented

AI / LLM App:
- `llm-contract.md` — Model name non-placeholder; System Prompt ≥1 real line; ≥1 parameter defined
- `eval-spec.md` — ≥1 evaluation criterion with non-placeholder content; ≥1 test case
- `prompt-library.md` — ≥1 prompt entry (name + file reference)

IaC / DevOps:
- `topology.md` — plantuml block with ≥1 real resource
- `runbook.md` — ≥1 runbook entry with real Steps
- `drift-policy.md` — Detection cadence non-placeholder; Remediation SLA defined

Mobile App:
- `mobile-contract.md` — ≥1 screen defined with non-placeholder title; Navigation structure described

Run at sprint end as part of the quality gate (step 4 of Sprint Documentation Sync).
Also runs automatically on `git commit` if `docs/script/validators/verify_content.py` is present.

```bash
python3 docs/script/validators/verify_content.py --project-type web-app
python3 docs/script/validators/verify_content.py --project-type data-pipeline+web-app --strict
python3 docs/script/validators/verify_content.py --project-type web-app --json
python3 docs/script/validators/verify_content.py --project-type web-app --docs path/to/docs
```

Output: per-document table (Required / Quality columns) followed by module flow results;
Documents and Quality summary lines.
`--strict` exits 1 if any document is missing or has a quality FAIL.

Update when: a new project type is added, or per-document quality rules change.

### spec-review.md
**Applies to: All project types**

Purpose:
Prompt template for LLM-as-a-Judge spec quality review. Load at sprint end for any Required
spec document that was updated during the sprint (especially those with ⚠️ or ❌ from
`verify_docs.py --content`). Scores the spec on five criteria (1–5 each) and returns a
structured PASS/FAIL verdict with evidence.

Criteria: Completeness · Ambiguity · Error Coverage · Testability · Consistency.
Per-type addenda: Data Pipeline/ML Pipeline (idempotency, schema contract, row-count expectation),
AI/LLM App (hallucination handling, retrieval failure, latency ceiling),
Microservices (service boundary, async contract, circuit breaker),
Mobile App (offline behaviour, OS permissions, deep link edge cases).

PASS requires all criteria ≥ 4. Any criterion below 4 → FAIL.
Record result in `docs/specs/test-report.md → Spec Review` section.

Do not include in PDF output — this is a process template, not a project document.

### spec-challenge.md
**Applies to: All project types**

Purpose:
Prompt template for QA simulation — the "Spec Challenge" layer. Where spec-review.md scores
what is written, spec-challenge.md finds what is missing. An LLM acts as the most demanding
QA engineer and solution architect, generating a list of Unresolved Questions the spec does
not answer. Questions are classified Critical / Major / Minor. The process iterates until a
round produces zero Critical questions.

Load when: sprint end, after spec-review.md PASS for a document. Run against each Required
spec document that passed Spec Review.
Never load during normal task work.
Record final round count in `docs/specs/test-report.md → Spec Challenge` section.
Do not include in PDF output — this is a process template, not a project document.

### scan_codebase.py
Purpose:
Scans the source directory and reports which modules are documented, undocumented,
or shared/infrastructure. Outputs a project tree (from project root) with `←` annotations
and documentation coverage icons.

Pass `--project-type <type>` to use project-appropriate vocabulary in labels and coverage output
(e.g. "Pipeline Stage" for data-pipeline / ml-pipeline, "Command" for cli-tool,
"Namespace" for library, "Service" for microservices, "Feature" for web-app / llm-app).
Valid values: `web-app` | `cli-tool` | `library` | `data-pipeline` | `ml-pipeline` | `microservices` | `llm-app` | `iac` | `mobile-app`.
Without `--project-type`, the script falls back to heuristic folder-name detection.

**Flags:**
- `--depth N` — scan N levels deep (default 1); use 2+ for monorepos or per-service `src/` layouts
- `--format json` — machine-readable output (type, status, flow_file per module + summary object)
- `--scaffold` — auto-generate stub `[module]-module-data-flow.md` for undocumented modules; skips existing files
- `--coverage` — print coverage summary only (no tree)
- `--update docs/codebase-map.md` — write tree and coverage table into codebase-map.md

**Pipeline confidence labels** (data-pipeline / ml-pipeline only):
- `Pipeline Stage (detected)` — directory contains `*_stage.py`, `step_*.py`, or `run_*.py`
- `Pipeline Stage` — folder name matches a known stage pattern
- `Pipeline Stage (inferred)` — non-shared folder with no name match or file evidence

Run at the start of a retrofit (Step 1b) to inventory all modules before documentation begins.
Run again after Step 3 to confirm full coverage.
Run with `--update docs/codebase-map.md` to write the tree and coverage table into codebase-map.md.

### verify_module_docs.py
**Applies to: All project types**
**Internal** — called automatically by `verify_content.py`. Direct use required only for `--src` coverage checks.

Purpose:
Module flow coverage & quality audit. Cross-references `docs/modules/` against the module list
from `scan_codebase.py` (when `--src` is provided) and verifies each flow file has required
sections filled, gated by module type × project type.

**Coverage check** (requires `--src`): confirms every module found in the source directory has
a matching `docs/modules/[module]/[module]-module-data-flow.md` file.

**Quality check** (always runs): verifies that each existing flow file has its required content
sections filled with real values — not placeholders — for the declared module type:
- **Pipeline Stage** — Input block (Source, Format, Schema), Output block (Destination, Format),
  Error Handling (transient + missing-input cases, ≥ 3 lines)
- **Feature** — at least one real `Function:` + `File:` pair; operations filled or `Not Supported`
- **Background Job** — `Trigger:` filled; success path present; Error Handling (transient + permanent)
- **Shared Utility** — plantuml class block with real methods; `Used by` table ≥ 1 real row

Called internally by `verify_content.py` for the module flow section of the quality gate.
For source-code coverage checks, run directly with `--src`. See `templates/sprint-sync.md → Step 4`.

```bash
# Coverage + quality (cross-reference against source code):
python3 docs/script/validators/verify_module_docs.py --project-type TYPE --src src --docs docs
# Quality only (audits existing docs/modules/ files):
python3 docs/script/validators/verify_module_docs.py --project-type TYPE --strict
python3 docs/script/validators/verify_module_docs.py --project-type TYPE --json
```

Output: per-module table with flow file status and quality verdict; Coverage and Quality summary lines.
`--strict` exits 1 if any module is missing a flow file or has a quality FAIL.

Update when: a new module type is added, or required sections for an existing module type change.

### verify_framework.py
Purpose:
Framework self-audit — checks internal consistency of the project_starter_v4 framework itself.
Run after each Phase completes, before merging.

Eleven checks performed:
1. **Stale pointer** — every `.md` reference in AGENTS.md resolves to an existing file
2. **Token budget** — AGENTS.md is ≤ 200 lines
3. **Matrix ↔ template** — every matrix row has a template file; every template has a matrix row
4. **Sprint-sync coverage** — every non-exempt R/O document has a sprint-sync checklist item
5. **Purposes coverage** — every Required document appears in the matching document-purposes file
6. **Cross-reference integrity** — every `### X.md` header in document-purposes-*.md has a template file
7. **Type completeness** — every type slug in AGENTS.md's init table has an init file and is registered in PURPOSES_FILES
8. **Script type sync** — `scan_codebase.py` and `verify_docs.py` declare the same set of project types
9. **build_pdf type sync** — `build_pdf.py` VALID_PROJECT_TYPES matches PURPOSES_FILES (all 9 types)
10. **Content coverage** — `verify_content.py` TYPE_DOCS covers all 9 project types and all document checker functions exist
11. **Registry ↔ matrix sync** — every `document-registry.yaml` entry has a row in `document-matrix.md`, and vice versa

```bash
python3 templates/script/framework/verify_framework.py
python3 templates/script/framework/verify_framework.py --strict   # exits 1 if any check fails or warns
python3 templates/script/framework/verify_framework.py --json     # machine-readable output
```

Output statuses: ✅ Pass · ❌ Fail · ⚠️ Warning

This script audits the framework, not a user project. Run it from the framework repo root.
Update when: the set of checks should change — e.g., a new consistency invariant is introduced.

---

## Adapter Files (adapters/)

### adapters/claude/start-task.md
**Applies to: All project types (Claude Code users)**

Purpose:
Template for the `/start-task` Claude Code slash command. When rendered by `orchestrator.py --adapter claude`,
the `{{WORKFLOW_CONTENT}}` placeholder is replaced with the current `.ai/WORKFLOW.md` snapshot and the result
is written to `.claude/commands/start-task.md` in the target project.

The slash command instructs Claude to run `orchestrator.py`, read `.ai/AI_CONTEXT.md` and `.ai/WORKFLOW.md`,
and present the workflow steps.

Update when: the slash command instructions or the WORKFLOW.md injection format change.

### adapters/claude/stop-hook.sh
**Applies to: All project types (Claude Code users)**

Purpose:
Shell script invoked by Claude Code's Stop hook on session end. Reads `docs/current-state.md` to extract
the current task name and appends one row to `docs/task-log.md` with a UTC timestamp.

Install by adding to the `Stop` hook list in `.claude/settings.json`. No orchestrator involvement — install once per project clone.

Update when: the task-log row format changes or `current-state.md` field names change.

### adapters/codex/setup.md
**Applies to: All project types (Codex users)**

Purpose:
Codex setup instructions. Explains how to run `orchestrator.py` before starting work and how to regenerate
the adapter output. Written to `.codex/setup.md` in the target project by `orchestrator.py --adapter codex`.

Update when: the orchestrator invocation pattern or setup steps change.

### adapters/codex/task-instructions.md
**Applies to: All project types (Codex users)**

Purpose:
Task instructions template for Codex. Contains a `{{WORKFLOW_CONTENT}}` placeholder that is replaced with the
current WORKFLOW.md snapshot at render time. Written to `.codex/task-instructions.md` by `orchestrator.py --adapter codex`.

Update when: the task instructions framing changes or the injection placeholder format changes.

### adapters/cursor/.cursorrules
**Applies to: All project types (Cursor users)**

Purpose:
Cursor rules template. Contains the workflow constraint (run orchestrator before starting work, run validators
before committing) and a `{{WORKFLOW_CONTENT}}` placeholder injected at render time. Written to `.cursorrules`
at the project root by `orchestrator.py --adapter cursor`.

Update when: the workflow rules or the WORKFLOW.md injection format change.

---

## Diagram Scripts Reference

| Script | Input format | Output suffix | Embedded in |
|---|---|---|---|
| `PlantUML (via build_pdf.py)` | plantuml block in architecture.md | `.html` / `.svg` | `architecture/architecture.md` |
| `schema_to_html.py` | Prisma / SQL file | `.html` / `.svg` | `specs/data-model.md` |
| `PlantUML (via build_pdf.py)` | state block in any .md | `-state.html` / `.svg` | `specs/data-model.md`, `business/*-object.md` |
| `PlantUML (via build_pdf.py)` | usecase block in any .md | `-usecase.html` / `.svg` | `specs/permissions.md` |
| `PlantUML (via build_pdf.py)` | activity block in any .md | `-activity.html` / `.svg` | `business/*-process.md` |
| `PlantUML (via build_pdf.py)` | sequence block in any .md | `-sequence.html` / `.svg` | `modules/*/` flow files |
| `PlantUML (via build_pdf.py)` | class block in any .md | `-class.html` / `.svg` | `modules/*/*-module-data-flow.md` |
| `PlantUML (via build_pdf.py)` | component block in any .md | `-component.html` / `.svg` | `backend.md` / `frontend.md` |
