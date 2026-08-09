# Quickstart

## Prerequisites

- Docker Desktop 24+
- Node.js 20+, Go 1.22+, Python 3.11+ (one per service, for local development)

## Setup

1. Clone the repository: `git clone https://github.com/example/eventflow.git`
2. Start all three services plus RabbitMQ and Postgres: `docker compose up -d`
3. Apply database migrations for each service:
   `docker compose exec ticket-service npm run migrate`,
   `docker compose exec inventory-service go run ./cmd/migrate`
4. Seed a sample event: `docker compose exec ticket-service npm run seed`
5. Purchase a test ticket: `curl -X POST localhost:8081/api/tickets/purchase -d @seed/sample-purchase.json`

## Verification

Run `docker compose exec ticket-service npm test` and `docker compose exec inventory-service go test ./...`
to confirm both services' test suites pass, then confirm the sample purchase in step 5
returns `201` with a `ticket_id`.
