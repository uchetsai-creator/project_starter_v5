# API Contract

Public REST API for `order-service`. Used by external clients and the admin-ui.

## Error Response Format

All errors return:
```json
{ "error": "snake_case_code", "message": "human-readable description" }
```

## Endpoints

### POST /api/orders

Create a new order.

#### Request Body
| Field | Type | Required | Description |
|---|---|---|---|
| customer_id | string | yes | UUID of the customer |
| items | array | yes | List of `{ sku: string, qty: integer }` |

#### Response Body (201)
| Field | Type | Description |
|---|---|---|
| id | string | Order UUID |
| status | string | Always `pending` on creation |
| created_at | string | ISO 8601 timestamp |

### GET /api/orders/:id

Fetch a single order.

#### Response Body (200)
| Field | Type | Description |
|---|---|---|
| id | string | Order UUID |
| status | string | `pending` \| `paid` \| `shipped` \| `cancelled` \| `refunded` |
| items | array | `{ sku, qty, price_cents }` |
| customer_id | string | UUID |
| created_at | string | ISO 8601 |
