# Project Types — Reference

Reference lookup only — load when detecting/declaring project type or resolving a hybrid
combination. Not needed during normal task work (AGENTS.md's short version is enough there).

## Supported Types

`web-app` is the actively-maintained type — the only one with a fully worked-out
task-breakdown convention (see AGENTS.md → Project Type). The other 8 below are
**Experimental**: usable (document matrix, validators, and skills all cover them), but
conventions that assume web-app's DB/BE/FE layering have not been built out for them yet.

| Type | Description |
|---|---|
| **Web App** | Backend + optional frontend, HTTP/GraphQL API, user auth, persistent DB |
| **CLI Tool** (Experimental) | Command-line interface, subcommands, flags, stdin/stdout; no persistent server |
| **Library / SDK** (Experimental) | Reusable package published to a registry; callers import it; no deployment |
| **Data Pipeline** (Experimental) | ETL/ELT batch or streaming; data in → data out; no user-facing API |
| **ML Pipeline** (Experimental) | Training → evaluation → serving; model artifact is the primary output |
| **Microservices** (Experimental) | Multiple independently deployed services communicating via API or events |
| **AI / LLM Application** (Experimental) | Chatbot, copilot, or agent built on a foundation model; prompt-driven, no model training |
| **IaC / DevOps** (Experimental) | Infrastructure-as-Code or DevOps tooling; Terraform, Pulumi, Ansible, Helm; resource topology, runbooks, drift policy |
| **Mobile App** (Experimental) | Native or cross-platform mobile app (React Native, Flutter, iOS/Swift, Android/Kotlin); screen-based, app-store distributed |

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
