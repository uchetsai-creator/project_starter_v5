# Service Contract

Inter-service REST contracts. For the public-facing API contract (used by external clients and
the admin-ui), see `api-contract.md`.

## admin-ui → order-service

### GET /internal/orders

**Purpose:** Fetch paginated order list for the admin dashboard.

**Request headers:**
| Header | Value |
|---|---|
| X-Service-Token | shared secret from env |

**Response:**
```json
{
  "orders": [{ "id": "uuid", "status": "pending|paid|shipped|cancelled", "created_at": "ISO8601" }],
  "total": 120,
  "page": 1
}
```

### POST /internal/orders/:id/override-status

**Purpose:** Allow ops team to manually override an order status (e.g. mark as refunded after
out-of-band payment confirmation).

**Request body:**
```json
{ "status": "refunded", "reason": "manual override by ops" }
```

**Response:** `200 OK` with updated order object, or `422` with `{ "error": "invalid_transition" }`.
