# API Contract

Public REST API for `ticket-service`. Used by the attendee-facing purchase flow and by
gate-staff validation devices.

## Error Response Format

All errors return the unified envelope:
```json
{ "error": { "code": "SNAKE_CASE_CODE", "message": "human-readable description", "details": {} } }
```

## Endpoints

| Method | Path | Description |
|---|---|---|
| POST | /api/tickets/purchase | Purchase one or more tickets for an event |
| GET | /api/tickets/:id | Fetch a single ticket's status |
| POST | /api/tickets/:id/validate | Mark a ticket as used at the venue gate |

### POST /api/tickets/purchase

Purchase one or more tickets for an event.

#### Request Body
| Field | Type | Required | Description |
|---|---|---|---|
| event_id | string | yes | Event identifier |
| ticket_type_id | string | yes | Ticket type identifier (e.g. General Admission) |
| quantity | integer | yes | Number of tickets, minimum 1 |
| attendee_email | string | yes | Where to send the confirmation |
| payment_token | string | yes | Token from the payment provider's client SDK |

#### Response Body (201)
| Field | Type | Description |
|---|---|---|
| ticket_id | string | Ticket UUID |
| status | string | Always `valid` on successful purchase |
| purchased_at | string | ISO 8601 timestamp |

#### Response Body (409)
`{ "error": { "code": "SOLD_OUT", "message": "No capacity remaining for this ticket type", "details": {} } }`

### GET /api/tickets/:id

Fetch a single ticket's status.

#### Response Body (200)
| Field | Type | Description |
|---|---|---|
| ticket_id | string | Ticket UUID |
| status | string | `valid` \| `used` \| `refunded` |
| event_id | string | Event identifier |
| ticket_type_id | string | Ticket type identifier |

### POST /api/tickets/:id/validate

Mark a ticket as used at the venue gate.

#### Response Body (200)
`{ "ticket_id": "tk_881", "status": "used", "validated_at": "ISO8601" }`

#### Response Body (422)
`{ "error": { "code": "ALREADY_USED", "message": "Ticket was already scanned", "details": {} } }`
