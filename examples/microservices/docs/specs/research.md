# Research

## Technology Decisions

Decision: Split into three services (ticket, inventory, notification) instead of a
single monolith with modules.
Rationale: Inventory holds during an on-sale burst need independent horizontal scaling
from notification delivery, which is I/O-bound on a third-party email/SMS provider;
coupling their deploys would mean scaling one for the other's bottleneck.

Decision: Use synchronous REST between ticket-service and inventory-service for the
hold/commit/release calls, but asynchronous messaging (RabbitMQ) for notifications.
Rationale: A hold must be confirmed before the purchase can proceed, so that call is on
the critical path and needs an immediate response; a notification is not on the critical
path — the purchase should succeed even if the broker or notification-service is briefly
unavailable.

Decision: Give each service its own PostgreSQL database rather than a shared schema.
Rationale: Independent deploys require independent schema migrations; a shared database
would force all three services' migrations to be coordinated, defeating the point of
splitting them.

## Resolved Clarifications

Q: Should a hold have a hard expiry, or persist until explicitly released?
A: Hard expiry (10 minutes, `HOLD_EXPIRY_SECONDS`). An abandoned checkout must not hold
inventory indefinitely; a background sweeper in `inventory-service` releases expired
holds even if `ticket-service` never sends an explicit release.
