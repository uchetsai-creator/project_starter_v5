# Service Contract

<!--
  For: Microservices projects
  Purpose: Documents the contracts between services — what Service A sends to Service B,
           what B guarantees back, and how failures are handled on both sides.
  Update when: An inter-service endpoint, event schema, or resilience policy changes.
  One file covers all inter-service contracts for this system.
  See service-catalog.md for the full list of services and their dependencies.
-->

<!--
  Use whichever section(s) match how your services actually communicate.
  Services that communicate via HTTP/REST → use REST / HTTP Contracts below.
  Services that communicate via a message broker → use Event / Message Contracts below.
  Many Microservices architectures use both — keep both sections.
  Delete the section that does not apply.
-->

## REST / HTTP Contracts

<!--
  Use this section when one service calls another synchronously over HTTP.
  Delete if all inter-service communication is event/queue-based.
-->

Repeat this block for each service-to-service REST call.

---

### [caller-service] → [callee-service]

**Endpoint:** `[METHOD] /path/{param}`

**Purpose:** [Why caller-service needs this — what it does with the response]

**Authentication:** [mTLS / shared secret header `X-Internal-Token` / JWT / None]

**Request:**
```json
{
  "field": "value"
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `field` | string | Yes | [Description] |

**Success response (2xx):**
```json
{
  "id": "abc123",
  "status": "ok"
}
```

**Error responses:**

| Status | Code | When |
|---|---|---|
| 400 | `INVALID_INPUT` | [Condition] |
| 404 | `NOT_FOUND` | [Condition] |
| 503 | `SERVICE_UNAVAILABLE` | Callee is down or overloaded |

**Resilience policy (caller-service side):**

| Property | Value |
|---|---|
| Timeout | [e.g., 5s] |
| Retries | [e.g., 3 × with exponential backoff starting at 100ms] |
| Circuit breaker | [Open after N failures in M seconds / Not implemented] |
| Fallback | [Return cached value / Return empty / Fail fast] |

---

## Event / Message Contracts

Repeat this block for each event that crosses service boundaries.

---

### [EventName] — [producer-service] → [consumer-service]

**Transport:** [Kafka / RabbitMQ / AWS SNS+SQS / Redis Pub/Sub]
**Topic / Queue:** `[topic-or-queue-name]`
**Serialisation:** [JSON / Avro / Protobuf]

**Schema:**
```json
{
  "eventType": "EventName",
  "version": "1.0",
  "occurredAt": "2024-01-01T00:00:00Z",
  "payload": {
    "id": "abc123",
    "field": "value"
  }
}
```

| Field | Type | Required | Description |
|---|---|---|---|
| `eventType` | string | Yes | Always `"EventName"` |
| `version` | string | Yes | Schema version for evolution |
| `occurredAt` | ISO 8601 | Yes | When the event occurred (not when published) |
| `payload.id` | string | Yes | [Description] |

**Ordering guarantee:** [Keyed by `id` — same key ordered within partition / No ordering guarantee]

**At-least-once / exactly-once:** [At-least-once — consumer must be idempotent on `id`]

**Consumer idempotency:** [Deduplicate on `payload.id` — already-processed IDs are ignored]

**Failure handling (consumer side):**

| Scenario | Behaviour |
|---|---|
| Processing error (transient) | Retry up to [N] times with [backoff] |
| Permanent failure | Move to dead-letter queue `[dlq-name]` — alert [channel] |
| Schema mismatch | Log and move to DLQ — do not crash consumer |

---

## Schema Evolution Rules

1. **Additive changes** (new optional field): consumers must ignore unknown fields — safe to deploy without coordination.
2. **Breaking changes** (rename, remove, type change): bump `version`, keep old consumer alive until all consumers are migrated, then remove old version.
3. **Never** remove a field without a deprecation period of at least one release cycle.

---

## Non-Functional Requirements

| Metric | Requirement |
|---|---|
| Inter-service call p95 latency | [service] → [service]: < [e.g., 100ms] |
| Circuit breaker threshold | Open after [N] failures in [M] seconds |
| Event processing lag (consumer) | < [e.g., 30s] behind producer at steady state |
| DLQ alert SLA | Oncall paged within [e.g., 5 minutes] of first message in DLQ |
| Schema compatibility window | Old and new schema version supported simultaneously for [e.g., 2 weeks] during migration |

---

## Edge Cases

### REST / HTTP

| Scenario | Expected behaviour |
|---|---|
| Callee is down or unreachable | Caller applies circuit breaker; uses fallback (see resilience policy per contract) |
| Request times out | Caller retries with idempotency key if operation is idempotent; otherwise fails fast |
| Callee returns unexpected `5xx` | Log, increment error counter, apply backoff — do not surface raw error to end user |
| Service-token header missing | Callee returns `401 MISSING_SERVICE_TOKEN` |
| Schema version unsupported by callee | Callee returns `400 SCHEMA_VERSION_UNSUPPORTED`; caller must upgrade before retrying |
| Caller sends duplicate request (idempotent op) | Callee returns same `200` with original result; no side effects repeated |
| Request payload exceeds callee size limit | Callee returns `413`; caller must chunk request |

### Event / Message

| Scenario | Expected behaviour |
|---|---|
| Consumer receives duplicate event | Idempotency check on `payload.id` — deduplicate silently, do not reprocess |
| Event schema version unknown to consumer | Move to DLQ; alert oncall — do not crash consumer process |
| DLQ is full | Page oncall immediately; halt producer if at-least-once guarantee would be violated |
| Consumer lag exceeds retention window | Alert oncall; trigger replay from snapshot if available |
| Producer crashes mid-batch | Broker retains unacknowledged messages; consumer retries on restart |
| Consumer processes event out of order | [Accept and handle out-of-order / reject if sequence number is lower than last seen]
