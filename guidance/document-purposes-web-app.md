# Document Purposes — Web App

<!--
  Reference only. Load together with document-purposes-common.md.
  This file covers documents specific to Web App projects.
  See document-purposes.md for the type-to-file lookup table.
-->

Load together with `document-purposes-common.md`.

---

## Specs (docs/specs/)

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
→ See `document-purposes-common.md § Specs — logging-spec.md`

---

## Architecture (docs/architecture/)

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
