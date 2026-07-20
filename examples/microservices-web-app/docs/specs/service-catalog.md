# Service Catalog

## Services

| Service | Owner | Port | Base URL | Dependencies |
|---|---|---|---|---|
| order-service | Platform Team | 8080 | /api/orders | postgres, redis |
| admin-ui | Frontend Team | 3000 | / | order-service |

## order-service

**Description:** Manages order lifecycle — creation, payment, fulfilment, cancellation.

**Tech stack:** Node.js / Express, PostgreSQL, Redis (job queue)

**Exposed API:** REST at `/api/orders` — see `service-contract.md` for inter-service contracts
and `api-contract.md` for the public-facing contract.

## admin-ui

**Description:** React single-page app for the operations team. Displays orders, allows manual
status overrides, and exports CSV reports.

**Tech stack:** React, Vite, TanStack Query

**Upstream dependencies:** Calls `order-service` REST API. No direct DB access.
