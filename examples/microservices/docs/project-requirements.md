# Project Requirements

## Goals

* Let event organizers sell tickets online without overselling a venue's seat inventory.
* Give attendees an immediate purchase confirmation by email or SMS.
* Keep ticket sales, seat inventory, and notifications as independently deployable
  services so a notification-provider outage never blocks a purchase.

---

## Scope

### In Scope
* Ticket purchase and validation (`ticket-service`)
* Per-event seat/ticket-type inventory holds and release (`inventory-service`)
* Purchase-confirmation and event-reminder delivery (`notification-service`)
* Async communication between services via a message broker for inventory events

### Out of Scope
* Venue seating-chart design tools
* Payment processing itself (delegated to a third-party payment provider)
* Organizer-facing analytics dashboards

---

## Roles

| Role | Description |
|---|---|
| Attendee | Purchases tickets via the public API; receives confirmations |
| Event Organizer | Configures an event's ticket types and inventory limits |
| Gate Staff | Validates a ticket at the venue entrance |

---

## Functional Requirements

* **FR-001**: `ticket-service` must reserve a seat/ticket-type hold in `inventory-service`
  before completing a purchase, and release the hold if payment fails.
* **FR-002**: `inventory-service` must never allow reserved + sold counts for a ticket
  type to exceed its configured capacity.
* **FR-003**: On a successful purchase, `ticket-service` must publish a
  `ticket.purchased` event that `notification-service` consumes to send a confirmation.
* **FR-004**: `notification-service` must retry a failed email/SMS delivery up to 3 times
  before marking it failed and alerting the organizer.
* **FR-005**: Gate staff must be able to validate a ticket (mark it "used") via the
  public API, and a ticket already marked "used" must be rejected on a second scan.

---

## Non-Functional Requirements

* **Availability**: `ticket-service` and `inventory-service` are each independently
  deployable with 99.9% uptime targets; `notification-service` degrading does not block
  ticket sales.
* **Consistency**: Inventory holds use a short-lived reservation (10 minutes) with an
  expiry job, so an abandoned checkout releases the seat automatically.
* **Latency**: Purchase confirmation (hold + charge) completes in under 2 seconds p95.
* **Scalability**: `inventory-service` must handle bursts of 5,000 concurrent hold
  requests during a popular event's on-sale moment without overselling.

---

## Edge Cases

### Empty and missing input
* A purchase request with zero ticket quantity is rejected with `400 invalid_quantity`.

### Permission boundaries
* Gate staff attempting to validate a ticket for an event they are not assigned to
  receive `403 forbidden`.

### Concurrency and race conditions
* Two simultaneous purchase requests for the last available seat in a ticket type: only
  one hold succeeds; the second receives `409 sold_out` from `inventory-service`.

### External dependency failures
* The message broker is unreachable when `ticket-service` tries to publish
  `ticket.purchased` → the purchase still completes (ticket is valid), and the event is
  retried from an outbox table until the broker is reachable again.

### State machine violations
* A ticket already marked `used` cannot transition back to `valid` through the public
  API; only an organizer support action (audited separately) can do that.

### Data contract violations
* An inventory hold request referencing a `ticket_type_id` that doesn't exist in
  `inventory-service` returns `404 ticket_type_not_found` rather than silently creating
  a new type.

---

## Acceptance Criteria

* **AC-001**: Given an event with 1 seat left in a ticket type, when two purchase
  requests arrive concurrently, then exactly one succeeds and the other receives
  `409 sold_out`.
* **AC-002**: Given a completed purchase, when `notification-service` consumes the
  `ticket.purchased` event, then a confirmation email or SMS is sent within 30 seconds.
* **AC-003**: Given a ticket already scanned as `used`, when gate staff scan it again,
  then the API returns `422 already_used` and does not admit the attendee twice.

---

## Assumptions

* Payment authorization is handled by a third-party provider called synchronously by
  `ticket-service`; this system does not store card data.
* All three services share a single event/ticket-type ID space seeded by the organizer
  configuration step (out of scope for this document).
