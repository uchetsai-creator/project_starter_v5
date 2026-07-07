# Document Purposes

<!--
  Reference only. Not read every task.
  The mandatory per-task update check lives in AGENTS.md → Document Update Checklist.
  This file explains WHY and details each document's purpose, update triggers, and
  which diagram script to run after updating.
-->

## Specs (docs/specs/)

### research.md
Update when:
* New technology decisions are made
* NEEDS CLARIFICATION items are resolved
* Architecture decisions change

### data-model.md
Update when:
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
Purpose:
Describes the full specification for every API endpoint and real-time event.
Default format assumes REST as the primary protocol. If the project also uses
WebSocket, Socket.IO, GraphQL, gRPC, or CLI — add a section for each protocol.
Do not omit a protocol because it was not in the original template.

Update when:
* New endpoints are added
* New WebSocket / Socket.IO events are added or changed
* Request/response/payload format changes
* Error codes are added
* Validation rules change

### permissions.md
Update when:
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
Purpose:
Define logging rules, format, and module naming conventions.
Logger instantiation pattern is documented here in a language/framework-agnostic way —
use whatever the project's logging library provides.
All modules must follow this spec.

Update when:
* New modules are added (add one line to the Module Naming Convention table)
* Log format changes
* Logger instantiation pattern changes

This file is the rule definition only — do not add module-specific logging content here.
Module-specific log points live in docs/modules/[module]/log-[module].md.

### specs/quickstart.md
Purpose:
Step-by-step guide for setting up and running the project locally.
Covers prerequisites, environment variables, startup commands, and verification steps.

Update when:
* Setup steps change
* New prerequisites are added
* Verification steps change
* Environment variable requirements change

---

## Architecture (docs/architecture/)

### architecture.md
Purpose:
Describe system component overview and data flow.
Contains a ```plantuml component diagram block rendered automatically by build_pdf.py.
Component type is a free-form label — use whatever best describes the component's role.

Update when:
* New components are added
* Data flows change
* Integration changes

After updating, regenerate diagram:
`Edit the ```plantuml block in the file, then run build_pdf.py`

### backend.md
Purpose:
Describe backend structure — stack, layering, layer responsibilities, module pattern.
Use the actual layer names from the codebase — do not assume Controller/Service/Repository.
Includes a component block for the backend module structure diagram.

Update when:
* Backend layering, stack, or module pattern changes

After updating, regenerate component diagram:
`Edit the ```plantuml block in the file, then run build_pdf.py`

### frontend.md
Purpose:
Describe frontend structure — stack, page structure, component strategy, API hook strategy.
Includes a component block for the frontend module structure diagram.

Update when:
* Frontend stack, page structure, or component strategy changes

After updating, regenerate component diagram:
`Edit the ```plantuml block in the file, then run build_pdf.py`

### database.md
Purpose:
Describe database structure at the conceptual level — main entities, main relationships,
important constraints. Not a field-by-field schema; that level of detail belongs in
docs/specs/data-model.md.

Update when:
* Main entities or relationships change

### deployment.md
Purpose:
Describe runtime structure — services, environment variables, local startup flow,
build/deploy flow, and deployment topology. Includes Cache Policy section for any
caching layer. The Deployment Diagram component block shows which service runs where
and how they connect in the actual deployment environment.

Update when:
* Services, env vars, or build/deploy flow changes
* Deployment topology changes (new service, new hosting platform, new network path)
* A caching layer is added or its TTL / invalidation strategy changes
* Cache boundary conditions or consumer behaviour is clarified

After updating the Deployment Diagram block, regenerate the diagram:
`Edit the ```plantuml block in the file, then run build_pdf.py`

---

## Flows (docs/modules/)

### module-data-flow.md
Purpose:
Index and rule definition for module-level code flows. Sits at `docs/modules/module-data-flow.md`.
Defines three module types — Feature, Background Job, Shared Utility — each with its own flow format.
Each module gets its own subfolder (`docs/modules/[module]/`) with its own flow file.

Update when:
* A new module is created — add a row to the Module Flow Files table

### [module]-module-data-flow.md
Purpose:
Track code-level execution flow (function names, file paths) for a specific module.
Declare the module type at the top: Feature / Background Job / Shared Utility.
Flow format follows the matching format defined in module-data-flow.md — do not assume
Controller/Service/Repository; use the real layer names from the codebase.
Also includes a class block describing the module's structure.

Location: `docs/modules/[module]/[module]-module-data-flow.md`
Examples: `docs/modules/order/order-module-data-flow.md`

Files matching this pattern are automatically included in the PDF.

Update when:
* Function names or file paths change for this module
* A new operation is implemented
* The module's class structure changes

After updating, regenerate class diagram:
`Edit the ```plantuml block in the file, then run build_pdf.py`

### module-flow.md
Purpose:
Index and rule definition for all module flow documents.
Each module has its own flow file: `docs/modules/[module]/[module]-flow.md`.

Update when:
* A new module flow file is created — add a row to the Flow Files table

### [module]-flow.md
Purpose:
Describe cross-module service call sequences for a specific module.
Includes a Sequence Diagram for each cross-module process.
Business steps and decision branches belong in docs/business/[process-name]-process.md.

Location: `docs/modules/[module]/[module]-flow.md`
Example: `docs/modules/order/order-flow.md`

Files matching `*-flow.md` are automatically included in the PDF.

Update when:
* Cross-module service calls change
* A new cross-module process is added to this module

After updating, regenerate sequence diagram:
`Edit the ```plantuml block in the file, then run build_pdf.py`

### log-[module].md
Purpose:
Track every log point in a module, in call order. One file per module.
Not included in the PDF — this is an implementation detail reference for developers.

Location: `docs/modules/[module]/log-[module].md`
Generate when the module is complete (see AGENTS.md → Module Completion Check).
Update immediately if function names or file paths change.

---

## Business (docs/business/)

### business-process.md
Purpose:
Index file listing all business process documents.
Each business process has its own dedicated file: `docs/business/[process-name]-process.md`.

Update when:
* A new business process file is created — add a row to the table

### [process-name]-process.md
Purpose:
Describe one business process — goal, steps, decision points, exceptions, and Activity Diagram.
Cross-module technical call sequences belong in docs/modules/[module]/[module]-flow.md.
Process Steps table includes a Prerequisites column — any access condition the Owner role
needs beyond the role itself (page access, permission, precondition state) must be noted
at the step level, not only in a separate Permission Note a reader could skip past.

Location: `docs/business/[process-name]-process.md`
Examples: `order-create-process.md`, `order-cancel-process.md`

Files matching `*-process.md` are automatically included in the PDF.

Update when:
* The business workflow, decision points, or exceptions change
* A step's access prerequisite changes — update the Prerequisites column, not just a footnote

After updating, regenerate activity diagram:
`Edit the ```plantuml block in the file, then run build_pdf.py`

### business-objects.md
Purpose:
Index and rule definition for all business object documents.
Each business object has its own file: `docs/business/[object-name]-object.md`.
Not every entity needs an object file — configuration/seed entities with no business
lifecycle (Role, Permission, Category, etc.) are excluded; see the Configuration Entity
Exception in this file's Rules section. Excluded entities still appear in the
Relationships table with a note pointing to where they're actually documented.

Update when:
* A new business object file is created — add a row to the table
* A relationship between objects changes — update the Relationships table
* An entity is identified as configuration-only — add a note under Relationships
  pointing to its real documentation location instead of creating an object file

### [object-name]-object.md
Purpose:
Describe one business entity — who owns it, who creates it, its lifecycle, and its
business-level state machine. Technical field-level detail belongs in docs/specs/data-model.md.
This file is the canonical source of truth for state transitions — `data-model.md` maps
ENUM values to these states but must not contradict them.

Location: `docs/business/[object-name]-object.md`
Examples: `order-object.md`, `inventory-object.md`

Files matching `*-object.md` are automatically included in the PDF.

Update when:
* The business entity's description, ownership, or lifecycle changes
* Status transitions or responsible roles change

After updating, regenerate state diagram:
`Edit the ```plantuml block in the file, then run build_pdf.py`

### business-rules.md
Purpose:
Describe business constraints and policies — approval rules, validation rules,
notification rules, audit rules. Each rule must declare its Enforcement Layer.
Only Hardcoded constraints belong here — Seeded defaults belong in permissions.md,
not here, since they can change without a deployment.

Update when:
* Business rules change
* A constraint moves from Seeded default to Hardcoded (or vice versa) — move the
  entry between business-rules.md and permissions.md accordingly

---

## Root-level (docs/)

### current-state.md
Purpose:
The active task. Read first when continuing an existing project.

### changelog.md
Purpose:
Completed task history. Current Task moves here once finished.

### codebase-map.md
Purpose:
Track which files are package usage vs custom logic, classified by layer (DB/BE/FE/MOD/JOB).
Includes a project tree (from project root) with documentation coverage status per module.
Used to verify the Package First principle is being followed.
Also serves as the project overview section in the PDF — a page structure component diagram
is injected here so readers get a visual of the frontend structure before diving into the file listing.

Update when:
* A task is completed — add the files touched in that task
* Re-run `python3 docs/script/scan_codebase.py <src_dir> --update docs/codebase-map.md`
  to refresh the tree view and coverage summary
* Frontend page/screen structure changes — update the component block in this file

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
