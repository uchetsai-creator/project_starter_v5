# API Contract

## Error Response Format

All errors return `{ "error": "message", "code": "ERROR_CODE" }`.

## Endpoints

| Method | Path | Description |
|---|---|---|
| GET | /users | List all users |
| POST | /users | Create a new user |
| GET | /orders | List orders |
| POST | /orders | Create an order |
