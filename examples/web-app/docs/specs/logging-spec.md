# Logging Spec

## Log Output Format

Production logs are one JSON object per line on stdout. Every log line carries these fields:

| Field | Example | Notes |
|---|---|---|
| `timestamp` | `2026-06-12T10:23:01.123Z` | ISO 8601, UTC |
| `level` | `info` / `warning` / `error` | see Log Levels |
| `event` | `order_create_failed` | constant snake_case name, no values |
| `request_id` | `a1b2c3d4-...` | bound once per HTTP request; see Request Tracing |
| `logger` | `app.orders.service` | module path of the logging file |

Event-specific data sits in its own fields (for example `reason`, `user_id`, `order_id`), never inside `event`.

```json
{"timestamp": "2026-06-12T10:23:01.123Z", "level": "warning", "event": "order_create_failed", "logger": "app.orders.service", "request_id": "a1b2c3d4", "reason": "insufficient_stock", "product_id": "p_099", "requested": 2}
```

## Required Log Points

- HTTP request received (`http_request_received`, method and path, no body)
- HTTP response sent (`http_response_sent`, status code and duration in ms)
- Every failed or rejected business rule (`warning`, with `reason`)
- Every unexpected exception (`error`, with exception type, message and stack trace)
- Every call to an external system: start, end (success) and failure with the reason

## Module Naming Convention

Short uppercase names, one per feature area. They appear in the `logger` field as the module path and in event-name prefixes.

```
AUTH        login, logout, token refresh
ORDER       order creation and lifecycle
INVENTORY   stock reservation and deduction
PAYMENT     payment provider calls
HTTP        request and response boundary
```

## Data Field Rules

- Log IDs needed to trace the call across modules (`user_id`, `order_id`), never the full user record.
- Never log passwords, tokens, API keys, card numbers or other PII.
- Log file uploads by name, size and type, never by content.

## Request Tracing

Each HTTP request gets a `request_id` (reused from the incoming `X-Request-ID` header if present, otherwise generated). The request middleware binds it to the logging context so every line written during that request includes it, and the response carries the same `X-Request-ID` header. Error responses include the `request_id` in `error.details`, so a user report can be matched to its log lines.
