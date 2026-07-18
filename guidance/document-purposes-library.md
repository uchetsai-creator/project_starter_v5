# Document Purposes — Library / SDK

<!--
  Reference only. Load together with document-purposes-common.md.
  This file covers documents specific to Library / SDK projects.
  See document-purposes.md for the type-to-file lookup table.
-->

Load together with `document-purposes-common.md`.

---

## Specs (docs/specs/)

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

---

## Architecture (docs/architecture/)

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

**Not applicable to Library / SDK.**
Libraries have no user-facing business workflows or domain entities.
Business logic belongs in the application that consumes the library, not in the library itself.

---

## Flows (docs/modules/)

**Not applicable to Library / SDK** for business-process or background-job flows.
Libraries use the Shared Utility flow format in `module-data-flow.md` for internal modules —
see `document-purposes-common.md § Flows`.
