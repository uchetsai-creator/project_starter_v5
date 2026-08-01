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
Includes a component block for the backend module structure diagram.

Update when (if listed in current-state.md → Doc Checklist, update at task level; otherwise defer to Sprint Documentation Sync):
* Backend layering, stack, or module pattern changes

After updating, regenerate component diagram:
`Edit the ```plantuml block in the file, then run build_pdf.py`

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
Only Hardcoded constraints belong here — Seeded defaults (config file defaults) belong elsewhere.

Update when (if listed in current-state.md → Doc Checklist, update at task level; otherwise defer to Sprint Documentation Sync):
* Business rules change
* A constraint moves from default to hardcoded (or vice versa)
