# Service Catalog

## Services

| Service | Owner | Port | Base URL | Dependencies |
|---|---|---|---|---|
| ticket-service | Ticketing Team | 8081 | /api/tickets | inventory-service, RabbitMQ, postgres |
| inventory-service | Ticketing Team | 8082 | /internal/holds | postgres |
| notification-service | Platform Team | 8083 | /internal/notifications | RabbitMQ, postgres, email/SMS provider |

## ticket-service

**Description:** Owns the attendee-facing ticket purchase flow, gate validation, and the
outbox that publishes `ticket.purchased` events.

**Tech stack:** Node.js / Express, PostgreSQL

**Exposed API:** Public REST at `/api/tickets` — see `api-contract.md`. Calls
`inventory-service` internally — see `service-contract.md`.

## inventory-service

**Description:** Tracks per-event ticket-type capacity, places time-limited holds during
checkout, and releases expired holds via a background sweeper.

**Tech stack:** Go, PostgreSQL

**Upstream dependencies:** Called by `ticket-service` only; has no outbound calls to
other services.

## notification-service

**Description:** Consumes `ticket.purchased` events from RabbitMQ and sends purchase
confirmations and pre-event reminders via email/SMS, with retry on delivery failure.

**Tech stack:** Python (Celery worker) + small REST API for delivery-status queries,
PostgreSQL

**Upstream dependencies:** Consumes events published by `ticket-service` via RabbitMQ;
no synchronous calls to other services.
