# Document Purposes — Data Pipeline

<!--
  Reference only. Load together with document-purposes-common.md.
  This file covers documents specific to Data Pipeline projects.
  See document-purposes.md for the type-to-file lookup table.
-->

Load together with `document-purposes-common.md`.

---

## Specs (docs/specs/)

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

### pipeline-debug.md
**Applies to: Data Pipeline, ML Pipeline**

Purpose:
Step-by-step debug guide for pipeline failures and data quality issues.
Covers how to identify the failing stage, check input data, read stage logs,
interpret data quality reports, and trace lineage to find where data went bad.
Load this file only when debugging an active incident — not during normal task work.

Update when:
* A new failure pattern is discovered and confirmed — add a row to the Common failure patterns table.
* The orchestrator tool, validation tool, or lineage tool changes — update the relevant steps.

### data-model.md
**Applies to: Web App, Data Pipeline, ML Pipeline, Microservices (per-service)**

Update when (if listed in current-state.md → Doc Checklist, update at task level; otherwise defer to Sprint Documentation Sync):
* Schema changes
* New entities are added
* Relationships change
* Indexes are added or removed

After updating, regenerate both diagrams:
* ERD: `Edit the ```plantuml block in the file, then run build_pdf.py`
* State diagram: `Edit the ```plantuml block in the file, then run build_pdf.py`

### logging-spec.md
→ See `document-purposes-common.md § Specs — logging-spec.md`

---

## Architecture (docs/architecture/)

### backend.md
**Applies to: Web App, CLI Tool, Data Pipeline, ML Pipeline, Microservices (per-service)**
Not applicable to Library / SDK (libraries have no runtime backend).

Purpose:
Describe pipeline stack and stage layering pattern.
Use the actual layer names from the codebase — do not assume Controller/Service/Repository.
Includes a component block for the backend module structure diagram.

Update when (if listed in current-state.md → Doc Checklist, update at task level; otherwise defer to Sprint Documentation Sync):
* Pipeline stack, stage layering, or module pattern changes

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
Describe runtime structure — services, environment variables, orchestration flow,
and deployment topology.

Update when (if listed in current-state.md → Doc Checklist, update at task level; otherwise defer to Sprint Documentation Sync):
* Services, env vars, or orchestration flow changes
* Deployment topology changes

After updating the Deployment Diagram block, regenerate the diagram:
`Edit the \`\`\`plantuml block in the file, then run build_pdf.py`

---

## Business (docs/business/)

### business-process.md
**Applies to: Web App, Microservices, Data Pipeline (optional), CLI Tool (optional)**

Purpose:
Index file listing all business process documents.
Each business process has its own dedicated file: `docs/business/[process-name]-process.md`.
Create only if the pipeline has identifiable business-stakeholder workflows worth documenting —
e.g., a data ingestion approval flow, a report delivery sign-off process, or a data quality
escalation workflow. Pure technical pipeline stages belong in pipeline-contract.md, not here.

Update when (at task level, together with the new process file — confirm index is updated whenever a new *-process.md is created):
* A new business process file is created — add a row to the table

### [process-name]-process.md
**Applies to: Web App, Microservices, Data Pipeline (optional), CLI Tool (optional)**

Purpose:
Describe one business process — goal, steps, decision points, exceptions, and Activity Diagram.
Cross-module technical call sequences belong in docs/modules/[module]/[module]-flow.md.
Process Steps table includes a Prerequisites column — any access condition the Owner role
needs beyond the role itself (approval rights, data access, precondition state) must be noted
at the step level, not only in a separate Permission Note a reader could skip past.

Location: `docs/business/[process-name]-process.md`

Files matching `*-process.md` are automatically included in the PDF.

Update when (if listed in current-state.md → Doc Checklist, update at task level; otherwise defer to Sprint Documentation Sync):
* The business workflow, decision points, or exceptions change

After updating, regenerate activity diagram:
`Edit the ```plantuml block in the file, then run build_pdf.py`

### business-rules.md
**Applies to: Web App, Data Pipeline, ML Pipeline, Microservices, CLI Tool (optional)**
Not applicable to Library / SDK.
For Data Pipeline and ML Pipeline: this covers data quality rules and validation constraints enforced in code, not user-facing business policies.

Purpose:
Describe data quality rules and validation constraints enforced in code.
Each rule must declare its Enforcement Layer.

Update when (if listed in current-state.md → Doc Checklist, update at task level; otherwise defer to Sprint Documentation Sync):
* Data quality rules or validation constraints change
