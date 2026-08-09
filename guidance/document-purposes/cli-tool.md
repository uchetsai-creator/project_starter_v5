# Document Purposes — CLI Tool

<!--
  Reference only. Load together with document-purposes-common.md.
  This file covers documents specific to CLI Tool projects.
  See document-purposes.md for the type-to-file lookup table.
-->

Load together with `document-purposes-common.md`.

---

## Specs (docs/specs/)

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

### release-guide.md
→ See `document-purposes-library.md § Specs — release-guide.md`.

### compatibility-matrix.md
→ See `document-purposes-library.md § Specs — compatibility-matrix.md`. CLI Tool: optional
(Library / SDK is required).

### logging-spec.md
→ See `document-purposes-common.md § Specs — logging-spec.md`

---

## Architecture (docs/architecture/)

### backend.md
→ See `document-purposes-web-app.md § Architecture — backend.md`.
CLI Tool note: describe the command dispatch structure and layer responsibilities
(e.g. CLI parsing → command handlers → core logic), not a request/response backend.

### distribution.md
→ See `document-purposes-library.md § Architecture — distribution.md`.

---

## Business (docs/business/)

### business-process.md
**Applies to: Web App, Microservices, Data Pipeline (optional), CLI Tool (optional)**

Purpose:
Index file listing all business process documents.
Each business process has its own dedicated file: `docs/business/[process-name]-process.md`.
Create only if the CLI Tool has identifiable user-facing workflows worth documenting —
e.g., a multi-step onboarding wizard triggered by `tool init`, a report generation and
delivery flow, or a review-and-approve process driven by successive CLI commands.
Single-command operations do not need a business process document; cli-contract.md is sufficient.

Update when (at task level, together with the new process file — confirm index is updated whenever a new *-process.md is created):
* A new business process file is created — add a row to the table

### [process-name]-process.md
**Applies to: Web App, Microservices, Data Pipeline (optional), CLI Tool (optional)**

Purpose:
Describe one business process — goal, steps, decision points, exceptions, and Activity Diagram.
Cross-module technical call sequences belong in docs/modules/[module]/[module]-flow.md.
Process Steps table includes a Prerequisites column — any access condition the Owner role
needs beyond the role itself (config files present, permissions granted, precondition state)
must be noted at the step level, not only in a separate note a reader could skip past.

Location: `docs/business/[process-name]-process.md`

Files matching `*-process.md` are automatically included in the PDF.

Update when (if listed in current-state.md → Doc Checklist, update at task level; otherwise defer to Sprint Documentation Sync):
* The business workflow, decision points, or exceptions change

After updating, regenerate activity diagram:
`Edit the ```plantuml block in the file, then run build_pdf.py`

### business-rules.md
**Applies to: Web App, Data Pipeline, ML Pipeline, Microservices, CLI Tool (optional)**
Not applicable to Library / SDK.

Purpose:
Describe business constraints and policies — validation rules, argument constraints, and output
formatting rules enforced by the CLI. Each rule must declare its Enforcement Layer.
Only Hardcoded constraints belong here — a Seeded default (a config file's own default value,
changeable by the user without a rebuild) belongs in `cli-contract.md`'s config file schema
section instead, not here. CLI Tool has no permissions.md to route it to.

Update when (if listed in current-state.md → Doc Checklist, update at task level; otherwise defer to Sprint Documentation Sync):
* Business rules change
* A constraint moves from default to hardcoded (or vice versa)
