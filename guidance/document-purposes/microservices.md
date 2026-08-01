# Document Purposes — Microservices

<!--
  Reference only. Load together with document-purposes-common.md.
  This file covers documents specific to Microservices projects.
  See document-purposes.md for the type-to-file lookup table.
-->

Load together with `document-purposes-common.md`.

---

## Specs (docs/specs/)

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
Documents inter-service synchronous REST contracts — request/response format,
authentication, and resilience policy (timeout / retry / circuit breaker).
Async event schemas belong in event-catalog.md, not here. service-contract.md
may reference event-catalog.md entries but does not duplicate them.

Update when (if listed in current-state.md → Doc Checklist, update at task level; otherwise defer to Sprint Documentation Sync):
* A REST contract between services changes (endpoint, request/response format, auth)
* A resilience policy changes (timeout, retry, circuit breaker)

### event-catalog.md
**Applies to: Microservices (Optional — Required if system uses async messaging)**

Purpose:
Canonical source for all async messaging contracts — event name, payload schema,
publisher, subscriber(s), broker/topic, retention, dead-letter policy, and schema
evolution rules. Covers Kafka, RabbitMQ, SQS, Pub/Sub, and similar brokers.
Decoupled from service-contract.md (synchronous REST) and api-contract.md (external API).

Create when: the system introduces asynchronous messaging between services.
Load when: adding or changing an event type, or auditing async contracts.

Update when (if listed in current-state.md → Doc Checklist, update at task level; otherwise defer to Sprint Documentation Sync):
* A new event type is added or retired
* A payload schema changes (field added, removed, or type changed)
* A publisher or subscriber changes
* Retention or dead-letter policy changes
* Schema evolution rules change

After updating: if the event was also referenced in service-contract.md, update the reference there to point to this file as the canonical source.
Regenerate sequence diagram: `Edit the \`\`\`plantuml block in event-catalog.md, then run build_pdf.py`

### api-contract.md
**Applies to: Web App, Microservices (external API)**

Purpose:
Describes the full specification for every externally-facing API endpoint and real-time event.
Default format assumes REST as the primary protocol. If the project also uses
WebSocket, Socket.IO, GraphQL, or gRPC — add a section for each protocol.

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

After updating, regenerate use case diagram:
`Edit the ```plantuml block in the file, then run build_pdf.py`

The use case diagram follows standard UML rules:
- Actors use `extends` for inheritance — only draw lines unique to each actor level
- Use cases must be verb-oriented user goals, not UI pages or domain objects
- UC→UC relationships use `..>` with `<<include>>` or `<<extend>>` only

Source distinction: every row in the API Endpoint Access table must specify whether
access is a Hardcoded constraint or a Seeded default. Only Hardcoded constraints belong
in business-rules.md as permanent rules.

### data-model.md
**Applies to: Web App, Data Pipeline, ML Pipeline, Microservices (per-service)**

Update when (if listed in current-state.md → Doc Checklist, update at task level; otherwise defer to Sprint Documentation Sync):
* Schema changes
* New entities are added
* Relationships change
* Indexes are added or removed
* State transitions change in any `docs/business/*-object.md`

After updating, regenerate both diagrams:
* ERD: `Edit the ```plantuml block in the file, then run build_pdf.py`
* State diagram: `Edit the ```plantuml block in the file, then run build_pdf.py`

### logging-spec.md
→ See `document-purposes-common.md § Specs — logging-spec.md`

---

## Architecture (docs/architecture/)

### backend.md
→ See `document-purposes-web-app.md § Architecture — backend.md`.
Microservices note: one `backend.md` per service (not one for the whole system).

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
important constraints.

Update when (if listed in current-state.md → Doc Checklist, update at task level; otherwise defer to Sprint Documentation Sync):
* Main entities or relationships change

### deployment.md
**Applies to: Web App, Data Pipeline, ML Pipeline, Microservices**

Purpose:
Describe runtime structure — services, environment variables, build/deploy flow,
and deployment topology. For Microservices: covers cross-service deployment topology.

Update when (if listed in current-state.md → Doc Checklist, update at task level; otherwise defer to Sprint Documentation Sync):
* Services, env vars, or build/deploy flow changes
* Deployment topology changes (new service, new hosting platform, new network path)

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
For Microservices, business-process.md documents cross-service user workflows —
e.g., an order fulfilment flow that spans Order Service → Inventory Service → Notification Service.
Intra-service technical call sequences belong in docs/modules/[module]/[module]-flow.md.
Inter-service contracts belong in service-contract.md or event-catalog.md.

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

Files matching `*-process.md` are automatically included in the PDF.

Update when (if listed in current-state.md → Doc Checklist, update at task level; otherwise defer to Sprint Documentation Sync):
* The business workflow, decision points, or exceptions change

After updating, regenerate activity diagram:
`Edit the ```plantuml block in the file, then run build_pdf.py`

### business-objects.md
**Applies to: Web App, Microservices**
Not applicable to CLI Tool, Library / SDK, Data Pipeline, ML Pipeline.

Purpose:
Index and rule definition for all business object documents.
Each business object has its own file: `docs/business/[object-name]-object.md`.

Update when (at task level, together with the new object file):
* A new business object file is created — add a row to the table
* A relationship between objects changes — update the Relationships table

### [object-name]-object.md
**Applies to: Web App, Microservices**

Purpose:
Describe one business entity — who owns it, who creates it, its lifecycle, and its
business-level state machine.
This file is the canonical source of truth for state transitions.

Location: `docs/business/[object-name]-object.md`

Files matching `*-object.md` are automatically included in the PDF.

Update when (if listed in current-state.md → Doc Checklist, update at task level; otherwise defer to Sprint Documentation Sync):
* The business entity's description, ownership, or lifecycle changes
* Status transitions or responsible roles change

After updating, regenerate state diagram:
`Edit the ```plantuml block in the file, then run build_pdf.py`

### business-rules.md
**Applies to: Web App, Data Pipeline, ML Pipeline, Microservices, CLI Tool (optional)**
Not applicable to Library / SDK.

Purpose:
Describe business constraints and policies — approval rules, validation rules,
notification rules, audit rules. Each rule must declare its Enforcement Layer.
Only Hardcoded constraints belong here.

Update when (if listed in current-state.md → Doc Checklist, update at task level; otherwise defer to Sprint Documentation Sync):
* Business rules change
* A constraint moves from Seeded default to Hardcoded (or vice versa)
