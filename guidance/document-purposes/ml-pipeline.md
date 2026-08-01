# Document Purposes — ML Pipeline

<!--
  Reference only. Load together with document-purposes-common.md.
  This file covers documents specific to ML Pipeline projects.
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
and how each stage handles errors.
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

### logging-spec.md
→ See `document-purposes-common.md § Specs — logging-spec.md`

---

## Architecture (docs/architecture/)

### backend.md
**Applies to: Web App, CLI Tool, Data Pipeline, ML Pipeline, Microservices (per-service)**
Not applicable to Library / SDK (libraries have no runtime backend).

Purpose:
Describe pipeline stack and stage layering pattern.
Use the actual layer names from the codebase.
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
Describe runtime structure — services, environment variables, training/serving infrastructure,
and deployment topology.

Update when (if listed in current-state.md → Doc Checklist, update at task level; otherwise defer to Sprint Documentation Sync):
* Services, env vars, or training/serving infrastructure changes
* Deployment topology changes

After updating the Deployment Diagram block, regenerate the diagram:
`Edit the \`\`\`plantuml block in the file, then run build_pdf.py`

---

## Business (docs/business/)

### business-rules.md
**Applies to: Web App, Data Pipeline, ML Pipeline, Microservices, CLI Tool (optional)**
Not applicable to Library / SDK.
For ML Pipeline: this covers data quality rules and validation constraints enforced in code.

Purpose:
Describe data quality rules and validation constraints enforced in code.
Each rule must declare its Enforcement Layer.

Update when (if listed in current-state.md → Doc Checklist, update at task level; otherwise defer to Sprint Documentation Sync):
* Data quality rules or validation constraints change
