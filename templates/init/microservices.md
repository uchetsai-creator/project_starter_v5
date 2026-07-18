# Project Initialization — Microservices

## Per-Service Setup

For each individual service, load `templates/init/web-app.md` and follow its initialization sequence in that service's own `docs/` folder, with these adaptations:

> **Note:** When following `web-app.md` per service, **skip** the hook install step and `.project-starter.yml` creation step — both are system-level and are done once in **System-Level Setup** below (steps 8–9). Do not repeat them per service.

- `api-contract.md` — include only if the service exposes an HTTP/REST or GraphQL API externally. For internal gRPC-only services, replace with a gRPC section inside `service-contract.md`. For event-driven services with no synchronous API, omit entirely.
- `frontend.md` — omit for backend-only services.
- `permissions.md` — include only if the service enforces its own auth. Services that delegate auth to an API gateway may omit this.

## System-Level Setup

At the system (repo root) level, additionally create:

1. Create docs/specs/service-catalog.md from templates/specs/service-catalog.md.
2. Create docs/specs/service-contract.md from templates/specs/service-contract.md.
3. Create docs/architecture/architecture.md from templates/architecture/architecture.md (system-level — shows all services and their connections).
4. Create docs/architecture/deployment.md from templates/architecture/deployment.md (system-level — shows deployment topology across all services).
5. If the system uses asynchronous messaging (Kafka, RabbitMQ, SQS, Pub/Sub, or similar broker):
   - Create docs/specs/event-catalog.md from templates/specs/event-catalog.md.
   - For each event type, fill in payload schema, publisher, subscriber(s), retention, and dead-letter policy.
   - Note in service-contract.md that async schemas are canonical in event-catalog.md.
6. Create docs/specs/test-plan.md from templates/specs/test-plan.md (system-level — cross-service integration and contract tests).
7. Create docs/specs/test-report.md from templates/specs/test-report.md (system-level — fill in after first test run).

8. Install the verification hook (see `README.md → Verification` for details):
    ```bash
    cp .githooks/pre-commit .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit
    ```
9. Create `.project-starter.yml` at the project root (used by the hook and all verify scripts):
    ```yaml
    project_type: microservices
    docs_path: docs/
    ```
