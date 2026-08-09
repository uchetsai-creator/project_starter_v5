# Logging Spec

## Log Output Format

JSON structured logging, one line per event, with a `trace_id` propagated across all
three services on every purchase request (via an `X-Trace-Id` header).

## Required Log Points

- Purchase request received / completed / failed (ticket-service)
- Hold placed / committed / released (inventory-service)
- Notification queued / delivered / failed (notification-service)
- Ticket validated at gate (ticket-service)
