# Project Initialization — Microservices

<!--
  Read this file ONCE when starting a new Microservices project.
  After initialization is complete, this file is no longer needed for day-to-day tasks.
  Workflow rules, task completion, and sprint sync live in AGENTS.md.
-->

## Per-Service Setup

For each individual service, load `templates/init/web-app.md` and follow its initialization sequence in that service's own `docs/` folder, with these adaptations:

- `api-contract.md` — include only if the service exposes an HTTP/REST or GraphQL API externally. For internal gRPC-only services, replace with a gRPC section inside `service-contract.md`. For event-driven services with no synchronous API, omit entirely.
- `frontend.md` — omit for backend-only services.
- `permissions.md` — include only if the service enforces its own auth. Services that delegate auth to an API gateway may omit this.

## System-Level Setup

At the system (repo root) level, additionally create:

1. Create docs/specs/service-catalog.md from templates/specs/service-catalog.md.
2. Create docs/specs/service-contract.md from templates/specs/service-contract.md.
3. Create docs/architecture/architecture.md from templates/architecture/architecture.md (system-level — shows all services and their connections).
4. Create docs/architecture/deployment.md from templates/architecture/deployment.md (system-level — shows deployment topology across all services).
