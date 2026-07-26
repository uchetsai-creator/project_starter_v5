# Project Initialization — Mobile App

<!--
  Load this file when setting up a new Mobile App project with project_starter_v5.
  Mobile App = native or cross-platform mobile (React Native, Flutter, iOS/Swift, Android/Kotlin).
  For hybrid types (e.g., Mobile App + AI/LLM App), load this file AND the other type's init file;
  union the step lists and skip duplicates.
-->

## Documents that do NOT apply to Mobile App (skip entirely)

Do not create these — they are N/A for this project type:

- `deployment.md` — replaced by `distribution.md` for app-store builds
- `release-guide.md` — replaced by the App Store / Google Play checklist in `distribution.md`
- `cli-contract.md`, `public-api.md` — no CLI or importable SDK
- `pipeline-contract.md`, `pipeline-debug.md` — no data/ML pipeline
- `llm-contract.md`, `prompt-library.md`, `eval-spec.md`, `llm-debug.md` — no LLM layer
- `rag-contract.md`, `mcp-contract.md` — no RAG or MCP
- `service-catalog.md`, `service-contract.md`, `event-catalog.md` — no microservice mesh
- `model-contract.md`, `experiment-log.md` — no ML model training
- `topology.md`, `runbook.md`, `drift-policy.md` — no IaC layer
- `business-objects.md`, `[object-name]-object.md` — mobile apps rarely have standalone domain object lifecycles

---

## Initialization Steps

**Step 1 — Create `.project-starter.yml` at the project root** (used by the hook and all verify scripts):

```yaml
project_type: mobile-app
docs_path: docs/
# Optional: spec_code_adapter / spec_code_spec / spec_code_src — enables the spec↔code
# drift gate in pre-commit + orchestrator. See README.md → Spec ↔ Code Validator →
# Wiring it into pre-commit.
```

**Step 2 — Copy `document-registry.yaml` from the framework root to your project root:**

```bash
cp /path/to/project_starter_v5/document-registry.yaml .
```
This file is required by all verify scripts and `build_pdf.py`. Without it, scripts will fail with "document-registry.yaml not found".

**Step 3 — Install the verification hook** (see `README.md → Verification` for details):

```bash
cp .githooks/pre-commit .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit
```

**Step 4 — Fill in `docs/project-requirements.md`**
Document platform targets (iOS / Android / both), framework (React Native / Flutter / SwiftUI / Kotlin),
minimum OS versions, and App Store / Google Play account details.

**Step 5 — Fill in `docs/architecture/architecture.md`**
Show the high-level components: mobile client, any BFF or backend APIs, push notification service,
analytics/crash reporting, and third-party SDKs.

**Step 6 — Fill in `docs/architecture/frontend.md`**
Document screen-based structure, navigation pattern (Stack / Tab / Drawer), component strategy,
and state management library (Redux, Riverpod, Zustand, etc.).

**Step 7 — Fill in `docs/specs/mobile-contract.md`**
Inventory all screens, the navigation graph, deep-link scheme, OS permission declarations,
and push notification payload schemas. This is the primary contract document for Mobile App projects.

**Step 8 — Fill in `docs/architecture/distribution.md` (Mobile App section)**
Document the build pipeline (Fastlane / Xcode Cloud / Bitrise / GitHub Actions),
signing configuration, and App Store / Google Play submission checklist.

**Step 9 — Fill in `docs/specs/quickstart.md`**
Cover: clone → install dependencies → configure environment (API keys, Firebase, etc.) →
run on simulator/emulator → run on physical device → run tests.

**Step 10 — Fill in `docs/specs/logging-spec.md`**
Document crash reporting (Sentry / Firebase Crashlytics / etc.), analytics events,
and module naming convention for log tags.

**Step 11 — Conditional documents (create only if applicable)**

- `docs/architecture/backend.md` — if the mobile app includes a BFF (Backend for Frontend) layer in this repo
- `docs/architecture/database.md` + `docs/specs/data-model.md` — if using local persistent storage (SQLite, Realm, Core Data, Room)
- `docs/specs/api-contract.md` — if integrating with third-party or internal REST/GraphQL APIs; document endpoint schemas
- `docs/specs/permissions.md` — if the app has multi-user auth with role-based access control
- `docs/specs/compatibility-matrix.md` — if officially supporting multiple OS versions; document which versions are tested and supported
- `docs/business/business-process.md` + `[process-name]-process.md` — if complex multi-step user workflows need documentation
- `docs/business/business-rules.md` — if domain-specific validation or policy rules are embedded in the app logic
- `docs/specs/research.md` — if technology choices (framework, state management, navigation library) were non-obvious; document the decision rationale

**Step 12 — Create test-plan.md and test-report.md**

Create `docs/specs/test-plan.md` from `templates/specs/test-plan.md`.
For Mobile App: document unit tests (business logic utils), component tests (single screen with navigation mocked), integration tests (screen + real backend staging), and E2E tests (Detox / Maestro / XCUITest for critical user flows).

Create `docs/specs/test-report.md` from `templates/specs/test-report.md` (fill in after first test run).

**Step 13 — Create `docs/current-state.md` from `templates/current-state.md`**
Run `python3 build-context.py` now (steps 1-2 already put `.project-starter.yml` +
`document-registry.yaml` in place) to fill in its Doc Checklist section.

**Step 14 — Run the module inventory scan**

```bash
python3 docs/script/scanners/scan_codebase.py src --project-type mobile-app
```

For React Native / Flutter feature-based layouts, scan at depth 2:

```bash
python3 docs/script/scanners/scan_codebase.py src/features --project-type mobile-app --depth 2
```

Creates `docs/codebase-map.md` entries for each screen module.

**Step 15 — Verify documentation completeness**

```bash
python3 docs/script/validators/verify_docs.py --project-type mobile-app
```

Fix any Missing Required items before beginning sprint work.

**Optional utility documents (create on demand, any time):**
- `docs/specs/glossary.md` — if the app introduces domain-specific screen names, navigation patterns, or business terms that the team (including designers and QA) needs to align on. Create from `templates/specs/glossary.md`.
- `docs/specs/dependencies.md` — to track SDK versions (React Native, Flutter, Expo, etc.), native module versions, and upgrade policy. Create from `templates/specs/dependencies.md`.
