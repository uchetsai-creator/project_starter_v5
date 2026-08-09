# Business Rules

## Rules

### BR-001: Inventory Cannot Be Oversold

| Field | Value |
|---|---|
| **Rule ID** | BR-001 |
| **Description** | The sum of reserved holds and committed sales for a ticket type must never exceed its configured capacity |
| **Reason** | Overselling a venue's physical seats creates an unresolvable conflict at the door |
| **Owner** | inventory-service |
| **Enforcement Layer** | Database constraint (check constraint on committed + reserved <= capacity) plus service layer validation before every hold |
| **Impact** | A hold request that would exceed capacity is rejected with `409 sold_out` |

### BR-002: A Ticket Can Only Be Validated Once

| Field | Value |
|---|---|
| **Rule ID** | BR-002 |
| **Description** | A ticket already marked `used` cannot be validated again through the public API |
| **Reason** | Prevents duplicate venue entry on a single purchased ticket (screenshot/photo sharing of a QR code) |
| **Owner** | ticket-service |
| **Enforcement Layer** | Service layer state-machine guard on the `validate` endpoint |
| **Impact** | A second scan attempt returns `422 already_used` and does not admit the attendee |

### BR-003: Expired Holds Auto-Release

| Field | Value |
|---|---|
| **Rule ID** | BR-003 |
| **Description** | A hold not committed within `HOLD_EXPIRY_SECONDS` (default 600) is automatically released back to available inventory |
| **Reason** | Abandoned checkouts must not permanently lock inventory away from other attendees |
| **Owner** | inventory-service |
| **Enforcement Layer** | Background sweeper job plus database constraint on hold expiry timestamp |
| **Impact** | Released capacity becomes immediately available to new hold requests |

---

## Approval Rules

| Action | Required approver | Trigger | Rejection response |
|---|---|---|---|
| Manual ticket refund after use | Organizer support action | Internal admin tool, not public API | 403 if attempted via public API |
| Increasing a ticket type's capacity mid-sale | Organizer | POST /internal/ticket-types/:id/capacity | 403 if requested by a non-organizer role |

## Validation Rules

| Rule | Condition checked | Failure behavior |
|---|---|---|
| Purchase quantity | `quantity >= 1` | 400 `invalid_quantity` before any hold is attempted |
| Ticket type exists | `ticket_type_id` resolves in inventory-service | 404 `ticket_type_not_found` |

## Notification Rules

| When | Who receives | Method |
|---|---|---|
| `ticket.purchased` event consumed | Attendee (from ticket payload) | Email, with SMS fallback if email bounces |
| Event starts in 24 hours | All attendees with a valid ticket for that event | Email reminder |

## Audit Rules

| Action | What is retained |
|---|---|
| Ticket validated at gate | `validated_at`, `validated_by` (gate staff ID), `device_id` |
| Manual refund by organizer support | `refunded_by`, `refunded_at`, `reason` |
