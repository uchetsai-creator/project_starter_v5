# Test Plan

## Testing Strategy

We use a layered testing approach with unit tests, contract tests, and end-to-end tests
across all three services.
Unit tests validate business logic (hold expiry, capacity checks, retry logic) in
isolation per service.
Contract tests run against `service-contract.md` and `api-contract.md` in CI — a service
that changes a response shape without updating the contract file fails the build.
End-to-end tests run all three services together via `docker compose` and drive a full
purchase-to-notification journey.

## Test Scope

- Unit: hold expiry logic, capacity checks, retry/backoff, outbox event publishing
- Contract: request/response shapes for every endpoint in api-contract.md and
  service-contract.md
- E2E: purchase -> hold commit -> event published -> notification delivered -> gate scan
