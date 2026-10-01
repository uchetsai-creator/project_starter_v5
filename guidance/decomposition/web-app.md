# Decomposition — Web App

Nouns for `guidance/decomposition/common.md`.

- **Observer:** an end user in the browser (or an API client, for API-only behavior)
- **Entry point:** a page / UI action, or an HTTP endpoint
- **Independent Test:** perform the user action in the UI (or call the endpoint) and check the
  visible result and the persisted state

## Artifact kinds

| Kind | Prefix | In a web app | First failing check |
|---|---|---|---|
| Contract | `BE` | Request/response schema, route signature in `api-contract.md` | Contract test: endpoint returns the documented shape |
| State | `DB` | Migration, model, index | Migration applies; schema test expects the new column |
| Logic | `BE` | Service / domain function behind the endpoint | Integration test: endpoint returns the expected result |
| Entry | `FE` | Page, component, client call to the endpoint | Component / E2E test: the action shows the result |
| Guard | `BE` (server) or `FE` (client-side feedback) | Validation, permission check, conflict handling, error display | Test expects 400 / 403 / 409 and the right message |

`DB` / `BE` / `FE` stay separate tasks — `run-verify.sh` and the Milestone Documentation Sync
trigger read these prefixes for web-app. Contract and Logic both carry `BE`; keep them separate
tasks when the contract changes on its own (e.g. a new error code), otherwise one `BE` task may
cover both.

## Typical Guard cases

- Invalid or missing input → 400 with a field-level message
- Wrong role → 403; not signed in → 401
- Concurrent edit / already processed → 409
- Downstream service or DB unavailable → 503 and a retry-safe client message

## Example slice

```
SL-2 (P2)  A line lead acknowledges an alarm
  Independent Test: click Acknowledge on one alarm → it leaves the list; DB row has who/when
  Task DB [SL-2] alarm acknowledgement columns                    Covers: FR-008
  Task BE [SL-2] POST /api/alarms/:id/ack (happy path)            Covers: FR-008, AC-005
  Task BE [SL-2] ack conflicts (409) and role check (403)         Covers: AC-006, AC-007
  Task FE [SL-2] Acknowledge button and "already acknowledged"    Covers: AC-005, AC-006
```
