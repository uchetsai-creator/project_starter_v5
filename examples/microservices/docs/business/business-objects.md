# Business Objects Index

## Relationships

| Object | Relates to | Relationship |
|---|---|---|
| Ticket | InventoryHold | N:1 — each ticket is created from exactly one committed hold |
| InventoryHold | TicketType | N:1 — each hold reserves capacity for one ticket type |
| Ticket | NotificationRecord | 1:N — each ticket may have multiple notification attempts (confirmation, reminder) |

## Object Files

| Object | File | Status field | States |
|---|---|---|---|
| Ticket | `docs/business/ticket-object.md` | `status` | valid -> used / refunded |
| InventoryHold | `docs/business/inventory-hold-object.md` | `status` | reserved -> committed / released / expired |
| NotificationRecord | `docs/business/notification-record-object.md` | `status` | queued -> delivered / failed |
