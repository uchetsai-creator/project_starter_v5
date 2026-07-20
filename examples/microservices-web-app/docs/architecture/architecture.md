# Architecture

## Overview

Two-service system: `order-service` (backend API) and `admin-ui` (React SPA). The admin-ui
communicates with order-service via internal REST endpoints secured by a shared service token.
External clients use the public REST API on order-service.

## System Components

| Component | Type | Responsibility |
|---|---|---|
| order-service | REST API (Node.js/Express) | Order lifecycle management, persistence |
| admin-ui | SPA (React/Vite) | Operations dashboard |
| PostgreSQL | Database | Order and customer data |
| Redis | Cache / Job queue | Status event queue for async fulfilment |

## Data Flow

```plantuml
@startuml
title Order Management Platform — System Architecture
actor "External Client" as client
actor "Ops Team" as ops
component "admin-ui\n:3000" as ui
component "order-service\n:8080" as api
database "PostgreSQL" as db
queue "Redis" as redis

client --> api : POST /api/orders
ops --> ui : browser
ui --> api : GET/POST /internal/orders
api --> db : read/write orders
api --> redis : enqueue fulfilment job
@enduml
```
