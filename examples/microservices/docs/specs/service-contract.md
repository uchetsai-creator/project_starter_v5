# Service Contract

Inter-service contracts. For the public-facing API contract (used by attendees and gate
staff), see `api-contract.md`.

## ticket-service → inventory-service

### POST /internal/holds

**Purpose:** Reserve a seat/ticket-type unit for the duration of a checkout.

**Request body:**
```json
{ "event_id": "evt_1", "ticket_type_id": "tt_ga", "quantity": 2, "hold_id": "uuid" }
```

**Response:** `201 Created` with `{ "hold_id": "uuid", "expires_at": "ISO8601" }`, or
`409 Conflict` with `{ "error": "sold_out" }` if capacity is exhausted.

### DELETE /internal/holds/:hold_id

**Purpose:** Release a hold — called when payment fails or checkout is abandoned.

**Response:** `204 No Content` on success, `404` if the hold does not exist (already
expired or already released — idempotent).

### POST /internal/holds/:hold_id/commit

**Purpose:** Convert a hold into a permanent sold ticket after payment succeeds.

**Response:** `200 OK` with `{ "ticket_type_id": "tt_ga", "committed": 2 }`.

## Events

- Topic: `ticket.purchased` — published by `ticket-service` after a hold is committed
  and payment succeeds; consumed by `notification-service`.
- Topic: `ticket.purchase_failed` — published by `ticket-service` when a hold expires or
  payment fails after a hold was placed; consumed by `notification-service` to suppress
  a duplicate confirmation attempt.

**`ticket.purchased` payload:**
```json
{
  "ticket_id": "tk_881",
  "event_id": "evt_1",
  "attendee_email": "attendee@example.com",
  "ticket_type_id": "tt_ga",
  "quantity": 2,
  "purchased_at": "ISO8601"
}
```

## Resilience Policies

`ticket-service` calls `inventory-service` with a 500ms timeout and 2 retries
(exponential backoff); after retries are exhausted the purchase fails with
`503 inventory_unavailable` rather than completing a sale without a confirmed hold.
`notification-service` retries a failed email/SMS delivery up to 3 times before writing
a `failed` delivery-status row for the organizer to see.
