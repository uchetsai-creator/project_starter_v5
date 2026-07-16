# Document Purposes

<!--
  Reference only. Not read every task.
  Per-task doc updates are driven by current-state.md → Doc Checklist (filtered at task setup).
  The full Document Update Checklist lives in AGENTS.md → Sprint Documentation Sync and runs at sprint end.
  This file explains WHY and details each document's purpose, update triggers, and
  which diagram script to run after updating.
-->

## How to use this file

Each entry below lists which project type(s) it applies to.

**Single project type:** create a document only if your declared type appears in its `Applies to` line.

**Mixed / Hybrid project types** (e.g., `Project Type: Data Pipeline + Web App`):
create a document if ANY of your declared types appears in its `Applies to` line.
Skip only documents where ALL your declared types are absent from the `Applies to` line.

Example: for `Data Pipeline + Web App`, `api-contract.md` (Applies to: Web App, Microservices)
should be created because Web App is one of your declared types.

---

## Specs (docs/specs/)

### research.md
**Applies to: All project types**

Update when (if listed in current-state.md → Doc Checklist, update at task level; otherwise defer to Sprint Documentation Sync):
* New technology decisions are made
* NEEDS CLARIFICATION items are resolved
* Architecture decisions change

### data-model.md
**Applies to: Web App, Data Pipeline, ML Pipeline, Microservices (per-service)**

Update when (if listed in current-state.md → Doc Checklist, update at task level; otherwise defer to Sprint Documentation Sync):
* Schema changes
* New entities are added
* Relationships change
* Indexes are added or removed
* State transitions change in any `docs/business/*-object.md` — update the ENUM mapping here to match, but do not redefine transitions (object file is canonical)

After updating, regenerate both diagrams:
* ERD: `Edit the ```plantuml block in the file, then run build_pdf.py`
  (output must go inside docs/ so build_pdf.py can find it)
* State diagram: `Edit the ```plantuml block in the file, then run build_pdf.py`

### api-contract.md
**Applies to: Web App, Microservices (external API)**

Purpose:
Describes the full specification for every API endpoint and real-time event.
Default format assumes REST as the primary protocol. If the project also uses
WebSocket, Socket.IO, GraphQL, gRPC, or CLI — add a section for each protocol.
Do not omit a protocol because it was not in the original template.

Update when (if listed in current-state.md → Doc Checklist, update at task level; otherwise defer to Sprint Documentation Sync):
* New endpoints are added
* New WebSocket / Socket.IO events are added or changed
* Request/response/payload format changes
* Error codes are added
* Validation rules change

### cli-contract.md
**Applies to: CLI Tool**

Purpose:
Documents every subcommand, flag, positional argument, output format, exit code, and
stdin/stdout contract. This is the CLI equivalent of api-contract.md.

Update when (if listed in current-state.md → Doc Checklist, update at task level; otherwise defer to Sprint Documentation Sync):
* A subcommand is added or removed
* A flag or argument is added, renamed, or removed
* Output format (stdout schema) changes
* Exit codes change
* Config file schema changes

### public-api.md
**Applies to: Library / SDK**

Purpose:
Documents the public-facing interface — all public functions, classes, types, and constants.
Internal symbols are excluded. This is the library equivalent of api-contract.md.
This file is the canonical source for stability tier declarations and the deprecation log.

Update when (if listed in current-state.md → Doc Checklist, update at task level; otherwise defer to Sprint Documentation Sync):
* A public function, class, type, or constant is added or changed
* A symbol is deprecated (add entry to Deprecation Log with target removal version)
* A symbol is removed (must already be in Deprecation Log)
* Stability tier changes

### pipeline-contract.md
**Applies to: Data Pipeline, ML Pipeline**

Purpose:
Documents every inter-stage data contract — what format each stage expects as input,
what it produces as output, naming conventions, lifecycle (archive / retain / overwrite),
and how each stage handles errors. This is the pipeline equivalent of api-contract.md.
The Cross-Stage Consistency Check table is the authoritative record of verified stage boundaries.

Update when (if listed in current-state.md → Doc Checklist, update at task level; otherwise defer to Sprint Documentation Sync):
* A stage's input path, format, or naming convention changes
* A stage's output path, format, or lifecycle changes
* A stage's error / skip handling policy changes
* A new stage is added

### service-catalog.md
**Applies to: Microservices**

Purpose:
Single source of truth for every service in the system — purpose, owner, port, base URL,
and inter-service dependencies. The dependency graph diagram shows how services connect.

Update when (if listed in current-state.md → Doc Checklist, update at task level; otherwise defer to Sprint Documentation Sync):
* A service is added, removed, or renamed
* Ownership, port, or base URL changes
* A major dependency relationship changes

After updating the dependency graph block, regenerate the diagram:
`Edit the \`\`\`plantuml block in the file, then run build_pdf.py`

### service-contract.md
**Applies to: Microservices**

Purpose:
Documents inter-service REST contracts and event schemas — request/response format,
authentication, resilience policy (timeout / retry / circuit breaker), and event
schema evolution rules. One file covers all inter-service contracts in the system.

Update when (if listed in current-state.md → Doc Checklist, update at task level; otherwise defer to Sprint Documentation Sync):
* A REST contract between services changes (endpoint, request/response format, auth)
* An event schema changes (field added, removed, or type changed)
* A resilience policy changes (timeout, retry, circuit breaker)
* Schema evolution rules change

### model-contract.md
**Applies to: ML Pipeline**

Purpose:
Defines what a trained model accepts as input (feature schema), what it produces as output
(prediction format), and what quality thresholds it must meet before being promoted to production.
This is the authoritative contract between the training pipeline and the serving layer.

Update when (if listed in current-state.md → Doc Checklist, update at task level; otherwise defer to Sprint Documentation Sync):
* Input feature schema changes (field added, removed, or type changed)
* Output format changes
* Production thresholds change
* Retraining policy changes
* A known limitation is discovered

### experiment-log.md
**Applies to: ML Pipeline**

Purpose:
Records each training experiment — hypothesis, configuration, results, and decision.
One entry per completed experiment run. Newest entry at the top.
Not a sprint-change-log (which tracks code changes); this tracks model behaviour across runs.

Update when:
* A training run is completed — add one entry with hypothesis, config, results, and decision.
  Do not add an entry without a decision. "No conclusion yet — running follow-up" is a valid decision.

### llm-contract.md
**Applies to: AI / LLM Application**

Purpose:
Single source of truth for how the LLM is invoked — model ID, system prompt (full text),
inference parameters (temperature, top_p, max_tokens), tool/function schemas, context window
strategy, and retry/fallback behaviour. Version this document whenever the system prompt or
model changes so prompt iterations can be compared against a known baseline.

Update when (update at task level — this is a core spec for LLM applications):
* The model or provider is changed
* The system prompt is modified (bump version, keep old version in Version history)
* Inference parameters (temperature, max_tokens, etc.) are tuned
* A tool / function schema is added, changed, or removed
* The context window or retry strategy changes

### prompt-library.md
**Applies to: AI / LLM Application**

Purpose:
Index of all prompt templates — lists what exists and defines the naming rules.
Does not contain prompt content. Actual prompt content lives in individual
`docs/specs/prompts/[prompt-id]-prompt.md` files so the index stays small
and the agent does not need to load all prompt text on every task.

Update when (update at task level):
* A new prompt file is created — add a row to the Active Prompts table
* A prompt's current version changes — update the version column
* A prompt is retired — move its row to the Retired Prompts table

### [prompt-id]-prompt.md
**Applies to: AI / LLM Application**
**Location: `docs/specs/prompts/[prompt-id]-prompt.md`**

Purpose:
One file per prompt. Contains the full prompt template text, input variable definitions,
an example input/output pair, test cases, and version history.
Agent loads only the specific prompt file it needs — not the whole library.
When a prompt changes, a new version entry is added to the Version History table;
old version text is kept so changes can be audited and rolled back.

Update when (update at task level):
* The prompt template text is changed — add a new version row, do not overwrite old text
* Input variables are added, removed, or renamed
* A test case is added (never remove existing test cases)
* After updating: verify the row in prompt-library.md shows the new current version

### eval-spec.md
**Applies to: AI / LLM Application**

Purpose:
Stable configuration for LLM-as-a-judge evaluation: judge model, scoring criteria with
rubrics (1–5 scale), the judge prompt template, and the fixed test case set.
This file changes rarely — only when criteria or the judge model change.
Eval run results are appended to eval-log.md, not here.

Update when (update at task level):
* A new eval criterion is added or an existing rubric is changed
* The judge model is changed
* Test cases are added to the fixed set (never remove existing cases)

### eval-log.md
**Applies to: AI / LLM Application**

Purpose:
Append-only log of every eval run result — one row per run.
Kept separate from eval-spec.md so the agent does not need to load the growing
run history on every task; it loads this file only when comparing prompt versions.

Update when:
* An eval run completes — append one row with date, prompt version, scores, and pass/fail.
  Never edit existing rows.

### rag-contract.md
**Applies to: AI / LLM Application (optional — only when using Retrieval-Augmented Generation)**

Purpose:
Documents the retrieval pipeline end-to-end: knowledge sources and their update frequency,
chunking strategy, embedding model, vector store configuration (similarity metric, threshold,
top-K), how retrieved chunks are formatted and injected into the prompt, and failure handling
when retrieval returns nothing or the vector store is unavailable.

Update when (if listed in current-state.md → Doc Checklist, update at task level; otherwise defer to Sprint Documentation Sync):
* A new knowledge source is added or an existing one is changed
* Chunking strategy or chunk size is changed
* The embedding model is changed (triggers full re-embedding)
* Similarity threshold or top-K is tuned
* A retrieval failure mode is discovered and handled

### mcp-contract.md
**Applies to: AI / LLM Application (optional — only when connecting to one or more MCP servers)**

Purpose:
Documents every MCP (Model Context Protocol) server this app connects to: transport type
(stdio command or SSE/HTTP URL), each server's exposed tools (with JSON Schema), resources
(URI templates), and prompt templates. Also records the tool-use policy (max calls per turn,
which tools need user confirmation) and failure handling per scenario.
Kept separate from llm-contract.md so server connection details can change independently
of the model config and system prompt.

Update when (if listed in current-state.md → Doc Checklist, update at task level; otherwise defer to Sprint Documentation Sync):
* An MCP server is added, removed, or its package version is pinned
* A tool schema changes (new parameter, renamed field, changed type)
* Transport changes (stdio → SSE, command args change)
* Tool-use policy is tuned (call limits, confirmation requirements)
* A new failure mode is discovered and handled

### release-guide.md
**Applies to: Library / SDK, CLI Tool**

Purpose:
Documents the versioning policy (semver rules), release checklist, publish process,
changelog format, and deprecation policy. This is the library/CLI equivalent of deployment.md.

Update when (if listed in current-state.md → Doc Checklist, update at task level; otherwise defer to Sprint Documentation Sync):
* The release process changes
* A new registry or publish target is added
* The versioning or deprecation policy changes

### compatibility-matrix.md
**Applies to: Library / SDK, CLI Tool (optional)**

Purpose:
Documents which runtime versions and peer dependency version ranges are supported,
which platform/OS combinations are tested, and any known incompatibilities.

Update when (if listed in current-state.md → Doc Checklist, update at task level; otherwise defer to Sprint Documentation Sync):
* Support for a runtime version is added or dropped
* A peer dependency version range changes
* A known incompatibility is discovered or resolved

### permissions.md
**Applies to: Web App, Microservices**

Update when (if listed in current-state.md → Doc Checklist, update at task level; otherwise defer to Sprint Documentation Sync):
* New roles are added
* Permission matrix changes
* New endpoints are added to API contract
* New features are added to the system
* Any `*-process.md` assigns a new "Responsible role" — cross-check that role has the required endpoint access
* Role permission defaults are seeded or changed via a Role Management feature — mark the row "(Default)", do not promote it to business-rules.md

After updating, regenerate use case diagram:
`Edit the ```plantuml block in the file, then run build_pdf.py`

The use case diagram follows standard UML rules:
- Actors use `extends` for inheritance — only draw lines unique to each actor level
- Use cases must be verb-oriented user goals, not UI pages or domain objects
- UC→UC relationships use `..>` with `<<include>>` or `<<extend>>` only
- `-->` between two use cases is invalid UML and will be rejected with a warning

Source distinction: every row in the API Endpoint Access table must specify whether
access is a Hardcoded constraint (enforced in code, needs a deployment to change) or
a Seeded default (database starting value, changeable at runtime by an admin). Only
Hardcoded constraints belong in business-rules.md as permanent rules.

Cross-check rule: every role listed as a responsible actor in any `*-process.md` must have
at least the minimum API endpoint access to perform that responsibility. A gap is a logical
contradiction that must be resolved before implementation.

### logging-spec.md
**Applies to: Web App, CLI Tool, Data Pipeline, ML Pipeline, Microservices**
Not applicable to Library / SDK (libraries should not configure logging; callers own that).

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

### backend.md
**Applies to: Web App, CLI Tool, Data Pipeline, ML Pipeline, Microservices (per-service)**
Not applicable to Library / SDK (libraries have no runtime backend).

Purpose:
Describe backend structure — stack, layering, layer responsibilities, module pattern.
Use the actual layer names from the codebase — do not assume Controller/Service/Repository.
For pipeline projects: describe the pipeline stack and stage layering pattern instead.
Includes a component block for the backend module structure diagram.

Update when (if listed in current-state.md → Doc Checklist, update at task level; otherwise defer to Sprint Documentation Sync):
* Backend layering, stack, or module pattern changes

After updating, regenerate component diagram:
`Edit the ```plantuml block in the file, then run build_pdf.py`

### frontend.md
**Applies to: Web App (optional), Microservices (optional if UI service exists)**
Not applicable to CLI Tool, Library / SDK, Data Pipeline, ML Pipeline.

Purpose:
Describe frontend structure — stack, page structure, component strategy, API hook strategy.
Includes a component block for the frontend module structure diagram.

Update when (if listed in current-state.md → Doc Checklist, update at task level; otherwise defer to Sprint Documentation Sync):
* Frontend stack, page structure, or component strategy changes

After updating, regenerate component diagram:
`Edit the ```plantuml block in the file, then run build_pdf.py`

### database.md
**Applies to: Web App, Data Pipeline, ML Pipeline, Microservices (per-service)**
Not applicable to CLI Tool (unless it uses a persistent DB), Library / SDK.

Purpose:
Describe database structure at the conceptual level — main entities, main relationships,
important constraints. Not a field-by-field schema; that level of detail belongs in
docs/specs/data-model.md.

Update when (if listed in current-state.md → Doc Checklist, update at task level; otherwise defer to Sprint Documentation Sync):
* Main entities or relationships change

### deployment.md
**Applies to: Web App, Data Pipeline, ML Pipeline, Microservices**

Purpose:
Describe runtime structure — services, environment variables, local startup flow,
build/deploy flow, and deployment topology. Includes Cache Policy section for any
caching layer. The Deployment Diagram component block shows which service runs where
and how they connect in the actual deployment environment.

Update when (if listed in current-state.md → Doc Checklist, update at task level; otherwise defer to Sprint Documentation Sync):
* Services, env vars, or build/deploy flow changes
* Deployment topology changes (new service, new hosting platform, new network path)
* A caching layer is added or its TTL / invalidation strategy changes
* Cache boundary conditions or consumer behaviour is clarified

After updating the Deployment Diagram block, regenerate the diagram:
`Edit the \`\`\`plantuml block in the file, then run build_pdf.py`

### distribution.md
**Applies to: Library / SDK, CLI Tool**

Purpose:
Documents how the package is built, published to a registry, and installed by end users.
This is the library/CLI equivalent of deployment.md — libraries and CLIs are not "deployed"
to a server; they are distributed to callers.

Update when (if listed in current-state.md → Doc Checklist, update at task level; otherwise defer to Sprint Documentation Sync):
* Build process or output artifacts change
* A registry or publish target is added, removed, or changed
* Installation instructions change
* CI/CD pipeline stages change

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

## Business (docs/business/)

### business-process.md
**Applies to: Web App, Microservices, Data Pipeline (optional), CLI Tool (optional)**
Not applicable to Library / SDK, ML Pipeline.

Purpose:
Index file listing all business process documents.
Each business process has its own dedicated file: `docs/business/[process-name]-process.md`.

Update when (at task level, together with the new process file — confirm index is updated whenever a new *-process.md is created):
* A new business process file is created — add a row to the table

### [process-name]-process.md
**Applies to: Web App, Microservices, Data Pipeline (optional), CLI Tool (optional)**

Purpose:
Describe one business process — goal, steps, decision points, exceptions, and Activity Diagram.
Cross-module technical call sequences belong in docs/modules/[module]/[module]-flow.md.
Process Steps table includes a Prerequisites column — any access condition the Owner role
needs beyond the role itself (page access, permission, precondition state) must be noted
at the step level, not only in a separate Permission Note a reader could skip past.

Location: `docs/business/[process-name]-process.md`
Examples: `order-create-process.md`, `order-cancel-process.md`

Files matching `*-process.md` are automatically included in the PDF.

Update when (if listed in current-state.md → Doc Checklist, update at task level; otherwise defer to Sprint Documentation Sync):
* The business workflow, decision points, or exceptions change
* A step's access prerequisite changes — update the Prerequisites column, not just a footnote

After updating, regenerate activity diagram:
`Edit the ```plantuml block in the file, then run build_pdf.py`

### business-objects.md
**Applies to: Web App, Microservices**
Not applicable to CLI Tool, Library / SDK, Data Pipeline, ML Pipeline.

Purpose:
Index and rule definition for all business object documents.
Each business object has its own file: `docs/business/[object-name]-object.md`.
Not every entity needs an object file — configuration/seed entities with no business
lifecycle (Role, Permission, Category, etc.) are excluded; see the Configuration Entity
Exception in this file's Rules section. Excluded entities still appear in the
Relationships table with a note pointing to where they're actually documented.

Update when (at task level, together with the new object file — confirm index is updated whenever a new *-object.md is created):
* A new business object file is created — add a row to the table
* A relationship between objects changes — update the Relationships table
* An entity is identified as configuration-only — add a note under Relationships
  pointing to its real documentation location instead of creating an object file

### [object-name]-object.md
**Applies to: Web App, Microservices**

Purpose:
Describe one business entity — who owns it, who creates it, its lifecycle, and its
business-level state machine. Technical field-level detail belongs in docs/specs/data-model.md.
This file is the canonical source of truth for state transitions — `data-model.md` maps
ENUM values to these states but must not contradict them.

Location: `docs/business/[object-name]-object.md`
Examples: `order-object.md`, `inventory-object.md`

Files matching `*-object.md` are automatically included in the PDF.

Update when (if listed in current-state.md → Doc Checklist, update at task level; otherwise defer to Sprint Documentation Sync):
* The business entity's description, ownership, or lifecycle changes
* Status transitions or responsible roles change

After updating, regenerate state diagram:
`Edit the ```plantuml block in the file, then run build_pdf.py`

### business-rules.md
**Applies to: Web App, Data Pipeline, ML Pipeline, Microservices, CLI Tool (optional)**
Not applicable to Library / SDK.
For Data Pipeline and ML Pipeline: this covers data quality rules and validation constraints enforced in code, not user-facing business policies.

Purpose:
Describe business constraints and policies — approval rules, validation rules,
notification rules, audit rules. Each rule must declare its Enforcement Layer.
Only Hardcoded constraints belong here — Seeded defaults belong in permissions.md,
not here, since they can change without a deployment.

Update when (if listed in current-state.md → Doc Checklist, update at task level; otherwise defer to Sprint Documentation Sync):
* Business rules change
* A constraint moves from Seeded default to Hardcoded (or vice versa) — move the
  entry between business-rules.md and permissions.md accordingly

---

## Root-level (docs/)

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
* Task starts — fill in Current Task, Required Context, Steps, Next Task; filter AGENTS.md → Document Update Checklist into Doc Checklist (this is the only time AGENTS.md is opened during normal task work)
* Task completes — apply Doc Checklist items, set Status to "Complete — Pending Sprint Doc Sync", mark steps [x], promote Next Task to Current Task, set Status to "In Progress" for new task

### changelog.md
Purpose:
Completed task history. Updated during Sprint Documentation Sync — not after every task.

Update when:
* Sprint Documentation Sync runs — move completed task summaries here from sprint-change-log.md

---

### task-log.md
Purpose:
Verification log — one row per completed task. AI agents must write a row here before
marking any task done, and every column must be ✅ before the row can be written.
This forces all post-task steps to be completed before reporting done.
Prevents AI from reporting completion without actual execution or without updating docs.

Format:
`| date | task | files changed | command run | ✅/❌ result | current-state ✅ | sprint-log ✅ |`

All checklist columns must be ✅. The "sprint-log" column confirms an entry was added to sprint-change-log.md.
The "docs" column is removed — documentation sync now happens at sprint level, not task level.
Result must confirm the feature works — not just "no errors":
- ✅ "endpoint returns expected data", "UI shows correct state", "output matches expected value"
- ❌ "no errors in log" alone is not sufficient

For validation / guard logic: also verify that invalid input is rejected.
- ✅ "Fed invalid data → guard correctly blocked it"
- ❌ "All checks passed on clean data" alone is not sufficient

Update when:
* Any task is completed — AI writes one row after completing ALL mandatory post-task steps

---

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

---

### codebase-map.md
Purpose:
Track which files are package usage vs custom logic, classified by layer (DB/BE/FE/MOD/JOB).
Includes a project tree (from project root) with documentation coverage status per module.
Used to verify the Package First principle is being followed.
Also serves as the project overview section in the PDF — a page structure component diagram
is injected here so readers get a visual of the frontend structure before diving into the file listing.

Update when:
* Sprint Documentation Sync runs — add files touched during the sprint, refresh tree view
* Re-run `python3 docs/script/scan_codebase.py <src_dir> --update docs/codebase-map.md`
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

### scan_codebase.py
Purpose:
Scans the source directory and reports which modules are documented, undocumented,
or shared/infrastructure. Outputs a project tree (from project root) with `←` annotations
and documentation coverage icons.

Run at the start of a retrofit (Step 1b) to inventory all modules before documentation begins.
Run again after Step 3 to confirm full coverage.
Run with `--update docs/codebase-map.md` to write the tree and coverage table into codebase-map.md.

---

## Diagram Scripts Reference

| Script | Input format | Output suffix | Embedded in |
|---|---|---|---|
| `PlantUML (via build_pdf.py)` | yaml block in architecture.md | `.html` / `.svg` | `architecture/architecture.md` |
| `schema_to_html.py` | Prisma / SQL file | `.html` / `.svg` | `specs/data-model.md` |
| `PlantUML (via build_pdf.py)` | state block in any .md | `-state.html` / `.svg` | `specs/data-model.md`, `business/*-object.md` |
| `PlantUML (via build_pdf.py)` | usecase block in any .md | `-usecase.html` / `.svg` | `specs/permissions.md` |
| `PlantUML (via build_pdf.py)` | activity block in any .md | `-activity.html` / `.svg` | `business/*-process.md` |
| `PlantUML (via build_pdf.py)` | sequence block in any .md | `-sequence.html` / `.svg` | `modules/*/` flow files |
| `PlantUML (via build_pdf.py)` | class block in any .md | `-class.html` / `.svg` | `modules/*/*-module-data-flow.md` |
| `PlantUML (via build_pdf.py)` | component block in any .md | `-component.html` / `.svg` | `backend.md` / `frontend.md` |
