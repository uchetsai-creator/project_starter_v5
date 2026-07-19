# Test Plan

## Testing Strategy

We use a layered testing approach with unit tests, integration tests, and e2e tests.
Unit tests validate pure functions and business logic in isolation using pytest.
Integration tests verify database interactions and API endpoint behavior.
End-to-end tests confirm complete user workflows through the full stack.

## Test Scope

- Unit: pure functions, validators, utilities
- Integration: API routes, database queries, service calls
- E2E: complete user journeys from HTTP request to database
