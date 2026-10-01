# Decomposition — Microservices

Nouns for `guidance/decomposition/common.md`.

- **Observer:** a calling service, or a consumer of an event the service publishes
- **Entry point:** a service endpoint (HTTP / gRPC) or an event topic
- **Independent Test:** send a request (or publish the triggering event) to the one service and
  check the response, the emitted event, and the service's own state — other services stubbed

## Artifact kinds

| Kind | Prefix | In microservices | First failing check |
|---|---|---|---|
| Contract | `CONTRACT` | Endpoint / event schema in `service-contract.md`, `event-catalog.md` | Consumer-driven contract test against the schema |
| State | `STATE` | The service's own database migration (never a shared DB) | Migration applies; repository test expects the field |
| Logic | `LOGIC` | Handler / domain logic inside the one service | Component test: request in → expected response out |
| Entry | `ENTRY` | Route or consumer registration, publisher wiring, gateway route | Integration test: the event is published / the route answers |
| Guard | `GUARD` | Idempotency, retries, timeouts, circuit breaker, dead-letter handling | Test: duplicate message processed once; downstream timeout → fallback |

One task touches one service. A slice that spans services gets one task per service per kind,
ordered so the producer's Contract lands before the consumer's Logic.

## Typical Guard cases

- Duplicate or out-of-order message → processed once / ignored
- Downstream service timeout → retry with backoff, then fallback or dead-letter
- Schema version mismatch → rejected with a clear error, not silently dropped

## Example slice

```
SL-1 (P1)  Paying an order publishes order.paid
  Independent Test: POST /orders/:id/pay → 200, order.paid appears on the topic once
  Task CONTRACT [SL-1] order.paid event schema                    Covers: FR-003
  Task LOGIC    [SL-1] mark order paid                            Covers: FR-003, AC-004
  Task GUARD    [SL-1] duplicate pay request is idempotent        Covers: AC-005
  Task ENTRY    [SL-1] publish order.paid after commit            Covers: AC-004
```
