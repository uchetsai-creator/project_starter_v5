# API Contract

## Error Response Format

All errors return the unified envelope:

```json
{ "error": { "code": "ERROR_CODE", "message": "human-readable description", "details": {} } }
```

## Endpoints

| Method | Path | Description |
|---|---|---|
| GET | /users | List all users |
| POST | /users | Create a new user |
| GET | /orders | List orders |
| POST | /orders | Create an order |
