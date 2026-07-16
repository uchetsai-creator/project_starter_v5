# Document Purposes — Mobile App

<!--
  Reference only. Load together with document-purposes-common.md.
  This file covers documents specific to Mobile App projects.
  See document-purposes.md for the type-to-file lookup table.
-->

Load together with `document-purposes-common.md`.

Mobile App projects use a screen-centric document set. `deployment.md` is replaced by `distribution.md`
(app-store builds, not server deployments). All pipeline, microservice, LLM, and IaC documents are N/A.

---

## Specs (docs/specs/)

### mobile-contract.md
**Applies to: Mobile App**

Purpose:
Canonical description of the app's screen surface and OS integration contracts.
Covers: screen inventory (name, route, auth requirement), navigation graph (Stack / Tab / Modal),
deep-link scheme, OS permission declarations with rationale strings, push notification payload schemas,
and App Store / Google Play metadata.

Load when: adding a new screen, changing navigation structure, adding an OS permission, or
modifying push notification payloads.

Update when (if listed in current-state.md → Doc Checklist, update at task level; otherwise defer to Sprint Documentation Sync):
* A new screen is added or an existing screen is removed or renamed
* Navigation graph changes (new stack, tab, or modal added)
* A new deep-link route is defined or an existing one changes
* A new OS permission is required or an existing one is removed
* A push notification payload schema changes

### distribution.md
**Applies to: Mobile App** (also: Library / SDK, CLI Tool — see those sections for package/binary distribution)

Purpose for Mobile App:
Documents the app-store build and submission pipeline. Covers: build tooling (Fastlane /
Xcode Cloud / Bitrise / GitHub Actions), signing configuration (certificates, provisioning
profiles, keystore), versioning policy, and App Store / Google Play submission checklist.
Replaces `deployment.md` for Mobile App projects — do not create deployment.md.

Load when: setting up the build pipeline, troubleshooting a signing issue, or preparing
an App Store / Google Play release.

Update when:
* Build tooling or CI configuration changes
* Signing certificates or provisioning profiles are rotated
* Versioning policy or build number scheme changes
* App Store / Google Play metadata or submission steps change

### compatibility-matrix.md
**Applies to: Mobile App** (also: Library / SDK, CLI Tool)

Purpose for Mobile App:
Documents which OS versions are officially tested and supported, known issues per OS,
and the policy for dropping old OS versions.

Update when:
* A new OS version is added to the support matrix
* An OS version is officially dropped
* A known OS-specific incompatibility is discovered

---

## Architecture (docs/architecture/)

### frontend.md
**Applies to: Mobile App** (also: Web App, Microservices with UI — those sections use page-based structure)

Purpose for Mobile App:
Documents screen-based structure, navigation pattern, component / widget strategy, and
state management library. Distinct from the web variant: no pages or routes in the HTTP sense —
structure is navigation stacks, tabs, and modals.

Load when: adding a new screen module, changing the navigation structure, or onboarding
a developer to the mobile codebase.

Update when:
* Navigation pattern changes (e.g., new top-level tab added)
* State management library changes
* Component / widget naming convention changes
* New platform target added (e.g., adding iPad-specific layout)

### architecture.md
**Applies to: Mobile App** (shared with all types — see document-purposes-common.md)

Mobile-specific note: the architecture diagram should show the mobile client, any
BFF (Backend for Frontend) or external API layer, push notification service, analytics /
crash reporting integration, and offline storage (if used). Do not draw individual screens.

### logging-spec.md
**Applies to: Mobile App** (shared — see document-purposes-common.md)

Mobile-specific note: covers crash reporting integration (Sentry / Firebase Crashlytics),
analytics event naming, and log tag naming convention for mobile modules.
