# Architecture

## Overview

EventFlow is a three-service ticketing platform. `ticket-service` owns purchases and
validation, `inventory-service` owns per-event seat/ticket-type capacity, and
`notification-service` sends purchase confirmations and reminders. Services communicate
synchronously via REST for the purchase path and asynchronously via a message broker for
post-purchase notifications.

## System Components

| Component | Type | Responsibility |
|---|---|---|
| ticket-service | REST API (Node.js/Express) | Ticket purchase, validation, gate scanning |
| inventory-service | REST API (Go) | Seat/ticket-type capacity, holds, releases |
| notification-service | Worker + REST API (Python) | Consumes purchase events, sends email/SMS |
| Message Broker | RabbitMQ | Delivers `ticket.purchased` events to notification-service |
| PostgreSQL (per service) | Database | Each service owns its own schema — no shared DB |

## Data Flow

```plantuml
@startuml
title EventFlow — System Architecture
actor "Attendee" as attendee
actor "Gate Staff" as gate
component "ticket-service" as ticket
component "inventory-service" as inventory
component "notification-service" as notif
queue "RabbitMQ" as broker
database "ticket-db" as tdb
database "inventory-db" as idb

attendee --> ticket : POST /api/tickets/purchase
gate --> ticket : POST /api/tickets/:id/validate
ticket --> inventory : POST /internal/holds
ticket --> tdb : persist ticket
ticket --> broker : publish ticket.purchased
broker --> notif : consume ticket.purchased
inventory --> idb : persist holds / capacity
@enduml
```
