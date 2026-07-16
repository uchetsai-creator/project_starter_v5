# Project Initialization — Mobile App

<!--
  Load this file when setting up a new Mobile App project with project_starter_v4.
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

**Step 1 — Fill in `docs/project-requirements.md`**
Document platform targets (iOS / Android / both), framework (React Native / Flutter / SwiftUI / Kotlin),
minimum OS versions, and App Store / Google Play account details.

**Step 2 — Fill in `docs/architecture/architecture.md`**
Show the high-level components: mobile client, any BFF or backend APIs, push notification service,
analytics/crash reporting, and third-party SDKs.

**Step 3 — Fill in `docs/architecture/frontend.md`**
Document screen-based structure, navigation pattern (Stack / Tab / Drawer), component strategy,
and state management library (Redux, Riverpod, Zustand, etc.).

**Step 4 — Fill in `docs/specs/mobile-contract.md`**
Inventory all screens, the navigation graph, deep-link scheme, OS permission declarations,
and push notification payload schemas. This is the primary contract document for Mobile App projects.

**Step 5 — Fill in `docs/architecture/distribution.md` (Mobile App section)**
Document the build pipeline (Fastlane / Xcode Cloud / Bitrise / GitHub Actions),
signing configuration, and App Store / Google Play submission checklist.

**Step 6 — Fill in `docs/specs/quickstart.md`**
Cover: clone → install dependencies → configure environment (API keys, Firebase, etc.) →
run on simulator/emulator → run on physical device → run tests.

**Step 7 — Fill in `docs/specs/logging-spec.md`**
Document crash reporting (Sentry / Firebase Crashlytics / etc.), analytics events,
and module naming convention for log tags.

**Step 8 — Conditional documents (create only if applicable)**

- `docs/architecture/backend.md` — if the mobile app includes a BFF (Backend for Frontend) layer in this repo
- `docs/architecture/database.md` + `docs/specs/data-model.md` — if using local persistent storage (SQLite, Realm, Core Data, Room)
- `docs/specs/api-contract.md` — if integrating with third-party or internal REST/GraphQL APIs; document endpoint schemas
- `docs/specs/permissions.md` — if the app has multi-user auth with role-based access control
- `docs/specs/compatibility-matrix.md` — if officially supporting multiple OS versions; document which versions are tested and supported
- `docs/business/business-process.md` + `[process-name]-process.md` — if complex multi-step user workflows need documentation
- `docs/business/business-rules.md` — if domain-specific validation or policy rules are embedded in the app logic
- `docs/specs/research.md` — if technology choices (framework, state management, navigation library) were non-obvious; document the decision rationale

**Step 9 — Run the module inventory scan**

```bash
python3 docs/script/scan_codebase.py src --project-type mobile-app
```

For React Native / Flutter feature-based layouts, scan at depth 2:

```bash
python3 docs/script/scan_codebase.py src/features --project-type mobile-app --depth 2
```

Creates `docs/codebase-map.md` entries for each screen module.

**Step 10 — Verify documentation completeness**

```bash
python3 docs/script/verify_docs.py --project-type mobile-app
```

Fix any ❌ Missing Required items before beginning sprint work.
