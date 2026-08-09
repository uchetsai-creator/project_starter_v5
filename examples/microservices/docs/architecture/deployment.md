# Deployment

## Services

| Service | Port | Replicas |
|---|---|---|
| ticket-service | 8081 | 3 |
| inventory-service | 8082 | 3 |
| notification-service | 8083 | 2 |
| RabbitMQ | 5672 | 1 (clustered in production) |

Each service is a separate container image, deployed independently to Kubernetes with
its own rollout — a `notification-service` deploy never requires restarting
`ticket-service` or `inventory-service`.

## Build / Deploy Flow

Each service has its own CI pipeline: build image -> run unit + contract tests -> push
to the registry -> `kubectl rollout` to staging -> manual promote to production.
`service-contract.md` is validated in CI before any deploy — a breaking inter-service
change fails the pipeline instead of shipping.

## Environment Variables

| Variable | Description |
|---|---|
| DATABASE_URL | Per-service PostgreSQL connection string |
| RABBITMQ_URL | Message broker connection string |
| INVENTORY_SERVICE_URL | Base URL `ticket-service` uses to call `inventory-service` |
| HOLD_EXPIRY_SECONDS | Inventory hold time-to-live before automatic release (default 600) |
