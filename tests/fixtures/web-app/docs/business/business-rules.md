# Business Rules

## BR-001 — User Must Be Authenticated

| | |
|---|---|
| **Description** | All API endpoints except /login require a valid JWT token |
| **Enforcement Layer** | FastAPI dependency injection middleware |

## BR-002 — Order Total Must Be Positive

| | |
|---|---|
| **Description** | An order cannot be placed with zero or negative total value |
| **Enforcement Layer** | Service layer validation before database write |
