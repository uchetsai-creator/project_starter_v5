# Project Types — Reference

Reference lookup only — load when detecting/declaring project type or resolving a hybrid
combination. Not needed during normal task work (AGENTS.md's short version is enough there).

## Supported Types

| Type | Description |
|---|---|
| **Web App** | Backend + optional frontend, HTTP/GraphQL API, user auth, persistent DB |
| **CLI Tool** | Command-line interface, subcommands, flags, stdin/stdout; no persistent server |
| **Library / SDK** | Reusable package published to a registry; callers import it; no deployment |
| **Data Pipeline** | ETL/ELT batch or streaming; data in → data out; no user-facing API |
| **ML Pipeline** | Training → evaluation → serving; model artifact is the primary output |
| **Microservices** | Multiple independently deployed services communicating via API or events |
| **AI / LLM Application** | Chatbot, copilot, or agent built on a foundation model; prompt-driven, no model training |
| **IaC / DevOps** | Infrastructure-as-Code or DevOps tooling; Terraform, Pulumi, Ansible, Helm; resource topology, runbooks, drift policy |
| **Mobile App** | Native or cross-platform mobile app (React Native, Flutter, iOS/Swift, Android/Kotlin); screen-based, app-store distributed |

## Common Hybrid Combinations

| Combination | What the second type adds |
|---|---|
| Data Pipeline + Web App | `api-contract.md`, `permissions.md`, `frontend.md` (dashboard/admin UI) |
| CLI Tool + Library | `public-api.md`, `compatibility-matrix.md` (the tool also ships as an importable package) |
| ML Pipeline + Web App | `api-contract.md`, `permissions.md` (model served via REST endpoint) |
| AI / LLM App + Web App | `api-contract.md`, `frontend.md`, `deployment.md` (hosted chatbot with UI) |

This list is illustrative, not exhaustive — any combination follows the same rule (see
AGENTS.md → Mixed / Hybrid Project Types): create all documents Required or Optional for
ANY declared type, skip only what's N/A for ALL of them.
