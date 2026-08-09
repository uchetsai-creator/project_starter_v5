# Permissions

## Roles

| Role | Description |
|---|---|
| attendee | Can purchase tickets and view their own tickets |
| gate_staff | Can validate (scan) tickets for events they are assigned to |
| organizer | Can configure events and ticket types; can view sales for their own events |

## Permission Matrix

| Action | attendee | gate_staff | organizer |
|---|---|---|---|
| POST /api/tickets/purchase | ✅ | ❌ | ❌ |
| GET /api/tickets/:id (own ticket) | ✅ | ✅ | ✅ |
| POST /api/tickets/:id/validate | ❌ | ✅ (assigned events only) | ❌ |
| Configure ticket types | ❌ | ❌ | ✅ (own events only) |
| View sales report | ❌ | ❌ | ✅ (own events only) |

Gate staff who attempt to validate a ticket for an event they are not assigned to
receive `403 forbidden`, enforced by `ticket-service`'s authorization middleware, not
just hidden in the UI.
