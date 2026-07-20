# Current State

Project: Order Management Platform
Project Type: Microservices + Web App
Status: Complete (example)

## Active Task

Task: Hybrid example — microservices + web app
Task Type: feature
Status: Complete

## What was built

A minimal reference project showing how to structure documentation for a
Microservices + Web App hybrid project. Two services are documented:
- `order-service` — REST API for order creation and lifecycle
- `admin-ui` — React dashboard for operations team

## How this hybrid differs from a single-type project

**Extra documents from Microservices type:**
- `docs/specs/service-catalog.md` — lists both services
- `docs/specs/service-contract.md` — defines the REST contract between services

**Extra documents from Web App type:**
- `docs/business/` — business objects and processes (not required for pure Microservices)
- `docs/specs/permissions.md` — role-based access control for the admin UI
