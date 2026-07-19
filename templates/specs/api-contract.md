# API Contract

<!--
  Describes the full specification for every API endpoint.
  Each endpoint corresponds to a functional requirement in project-requirements.md.

  Which contract file to use — pick the one that matches your project type:

  | Project type                    | Contract file                                      |
  |---------------------------------|----------------------------------------------------|
  | Web App / Microservices (HTTP)  | api-contract.md (this file)                        |
  | CLI Tool                        | cli-contract.md                                    |
  | Library / SDK                   | public-api.md                                      |
  | Data Pipeline / ML Pipeline     | pipeline-contract.md                               |
  | AI / LLM App                    | llm-contract.md  +  rag-contract.md (if RAG)  +  mcp-contract.md (if MCP) |

  Mixed-protocol projects (e.g. REST + WebSocket, REST + gRPC) should have one section
  per protocol inside this file. Do not omit a protocol because it was not in the
  original template — if the codebase emits or receives real-time events, document them.

  The sections below (Overview table, per-endpoint blocks, Error Response Format,
  Error Code Catalogue) are REST / HTTP specific.
  Add or replace sections for GraphQL, gRPC, WebSocket as needed (templates at bottom).
-->

> **Applies to:** Web App, Microservices. For other project types see the routing table above.

**Base URL:** `[e.g., /api/v1]`
**Authentication:** `[e.g., Bearer Token (JWT) / API Key / mTLS / None]`
**Content-Type:** `application/json`

---

## Overview

<!--
  Sub-action endpoint rule:
  For state-transition endpoints (e.g., /:id/acknowledge, /:id/cancel, /:id/publish):
  - Document whether the endpoint handles only one direction (e.g., acknowledge only)
    or both directions (e.g., acknowledge + un-acknowledge via request body).
  - If two endpoints overlap in purpose (e.g., /acknowledge and /acknowledgement both
    affect the same state), add a **Design Note:** under each endpoint explaining why
    they are separate. If no justification exists, consolidate into one endpoint.
  - Deprecated endpoints must be marked with ~~strikethrough~~ in the Overview table
    and include a `**Deprecated:** Use [replacement endpoint] instead.` note.
-->

| Method | Path | Description | Auth |
|---|---|---|---|
| `POST` | `/[resource]` | [description] | ✅ |
| `GET` | `/[resource]` | [description] | ✅ |
| `GET` | `/[resource]/:id` | [description] | ✅ |
| `PATCH` | `/[resource]/:id` | [description] | ✅ |
| `DELETE` | `/[resource]/:id` | [description] | ✅ |

---

## `POST /[resource]`

**Description:** [description]

**Request Body:**

```json
{
  "[field]": "string",   // required
  "[field]": 0,          // required
  "[field]": "string"    // optional
}
```

**Validation Rules:**

| Field | Required | Rule | Error code |
|---|---|---|---|
| `[field]` | ✅ | Length 1–255 | `VALIDATION_FIELD_REQUIRED` |
| `[field]` | ✅ | Range 1–1000 | `VALIDATION_FIELD_OUT_OF_RANGE` |
| `[field]` | ❌ | Format: email | `VALIDATION_FIELD_FORMAT` |

**Success `201 Created`:**

```json
{
  "id": "uuid",
  "[field]": "string",
  "created_at": "2025-01-01T00:00:00Z"
}
```

**Errors:**

| HTTP | Error code | Scenario |
|---|---|---|
| `400` | `VALIDATION_FIELD_REQUIRED` | Required field missing |
| `401` | `AUTH_TOKEN_EXPIRED` | Token expired |
| `409` | `[ENTITY]_ALREADY_EXISTS` | Duplicate resource |

---

## `GET /[resource]`

**Description:** [description]

**Query Parameters:**

| Parameter | Required | Default | Description |
|---|---|---|---|
| `page` | ❌ | `1` | Page number |
| `per_page` | ❌ | `20` | Items per page, max 100 |
| `status` | ❌ | — | Filter by status |

**Success `200 OK`:**

```json
{
  "data": [
    {
      "id": "uuid",
      "[field]": "string",
      "created_at": "2025-01-01T00:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 100,
    "total_pages": 5
  }
}
```

**Errors:**

| HTTP | Error code | Scenario |
|---|---|---|
| `400` | `VALIDATION_ENUM_INVALID` | Invalid status value |
| `401` | `AUTH_TOKEN_EXPIRED` | Token expired |

---

## `GET /[resource]/:id`

**Description:** [description]

**Success `200 OK`:** Returns the full resource

**Errors:**

| HTTP | Error code | Scenario |
|---|---|---|
| `401` | `AUTH_TOKEN_EXPIRED` | Token expired |
| `403` | `AUTH_RESOURCE_NOT_OWNED` | Accessing another user's resource |
| `404` | `[ENTITY]_NOT_FOUND` | ID does not exist |

---

## `PATCH /[resource]/:id`

**Description:** Partial update — only send fields to change

**Request Body:** Same as POST, but all fields are optional

**Success `200 OK`:** Returns the updated full resource

**Errors:**

| HTTP | Error code | Scenario |
|---|---|---|
| `401` | `AUTH_TOKEN_EXPIRED` | Token expired |
| `403` | `AUTH_RESOURCE_NOT_OWNED` | Modifying another user's resource |
| `404` | `[ENTITY]_NOT_FOUND` | ID does not exist |
| `409` | `[ENTITY]_STATE_INVALID` | Current state does not allow this operation |
| `409` | `[ENTITY]_CONCURRENT_UPDATE` | Optimistic lock conflict |

---

## `DELETE /[resource]/:id`

**Description:** [Soft delete / Hard delete]

**Success `204 No Content`**

**Errors:**

| HTTP | Error code | Scenario |
|---|---|---|
| `401` | `AUTH_TOKEN_EXPIRED` | Token expired |
| `403` | `AUTH_RESOURCE_NOT_OWNED` | Deleting another user's resource |
| `404` | `[ENTITY]_NOT_FOUND` | ID does not exist |
| `409` | `[ENTITY]_STATE_INVALID` | Current state does not allow deletion |

---

## Error Response Format

All errors use a unified format:

```json
{
  "error": {
    "code": "VALIDATION_FIELD_REQUIRED",
    "message": "Field [field] is required",
    "user_message": "[Field name] is required"
  }
}
```

---

## Error Code Catalogue

| Code | HTTP | Description | Retryable |
|---|---|---|---|
| `AUTH_TOKEN_MISSING` | 401 | Authorization header missing | N |
| `AUTH_TOKEN_EXPIRED` | 401 | Token has expired | N |
| `AUTH_TOKEN_INVALID` | 401 | Token verification failed | N |
| `AUTH_PERMISSION_DENIED` | 403 | Role lacks required permission | N |
| `AUTH_RESOURCE_NOT_OWNED` | 403 | Resource does not belong to current user | N |
| `VALIDATION_FIELD_REQUIRED` | 400 | Required field missing | Y |
| `VALIDATION_FIELD_FORMAT` | 400 | Field format invalid | Y |
| `VALIDATION_FIELD_TOO_LONG` | 400 | Field exceeds maximum length | Y |
| `VALIDATION_FIELD_OUT_OF_RANGE` | 400 | Value out of allowed range | Y |
| `VALIDATION_ENUM_INVALID` | 400 | Invalid enum value | Y |
| `[ENTITY]_NOT_FOUND` | 404 | Resource does not exist | N |
| `[ENTITY]_DELETED` | 410 | Resource has been permanently deleted | N |
| `[ENTITY]_ALREADY_EXISTS` | 409 | Resource already exists | N |
| `[ENTITY]_STATE_INVALID` | 409 | Current state does not allow this operation | N |
| `[ENTITY]_CONCURRENT_UPDATE` | 409 | Optimistic lock conflict | Y |
| `RATE_LIMIT_EXCEEDED` | 429 | Too many requests | Y |
| `EXTERNAL_[SERVICE]_TIMEOUT` | 504 | Upstream service timed out | Y |
| `INTERNAL_UNEXPECTED` | 500 | Unexpected internal error | Y |

---

## WebSocket Events

<!--
  Include this section if your project uses WebSocket or Socket.IO.
  Remove it if your project is REST-only.

  Document every event the server emits and every event the client sends.
  For Socket.IO: use the event name as the heading (e.g. ## `kpi:update`).
  For raw WebSocket: use the message type field as the heading.

  If your project uses a unified event envelope (e.g. { id, type, payload }),
  document the envelope format once at the top, then describe each event's payload.
-->

**Transport:** `[e.g., Socket.IO 4.x / native WebSocket]`
**Connection URL:** `[e.g., wss://api.example.com / /socket.io]`
**Authentication:** `[e.g., JWT passed as auth.token in handshake / cookie / query param]`

### Event Envelope

<!--
  If all events share a common wrapper format, document it here.
  If each event has its own top-level shape, remove this section.
-->

```json
{
  "id":        "uuid",
  "type":      "event:name",
  "createdAt": "2025-01-01T00:00:00Z",
  "payload":   {}
}
```

### Event Overview

| Event | Direction | Trigger | Payload type |
|---|---|---|---|
| `[event:name]` | server → client | [what triggers it] | [payload type or —] |
| `[event:name]` | client → server | [what the client sends] | [payload type or —] |

### Server → Client Events

#### `[event:name]`

**Trigger:** [what causes the server to emit this event]

**Payload:**

```json
{
  "[field]": "[type / example value]"
}
```

---

### Client → Server Events

#### `[event:name]`

**Description:** [what this event does]

**Payload:**

```json
{
  "[field]": "[type / example value]"
}
```

**Response / Acknowledgement:** [describe ack if any, or "none"]

---

### Connection Lifecycle

| Event | Direction | Description |
|---|---|---|
| `connect` | client → server | Client establishes connection |
| `disconnect` | server → client | Server closes connection |
| `[custom]` | [direction] | [description] |

### Error Handling

| Scenario | Behaviour |
|---|---|
| Authentication failure | [e.g., connection refused with 401] |
| Invalid payload | [e.g., server emits error event with code] |
| Connection drop | [e.g., client reconnects automatically] |

---

## GraphQL API

<!--
  Include this section if your project uses GraphQL.
  Remove it if your project does not use GraphQL.

  Document every Query, Mutation, and Subscription.
  If your project uses a schema-first approach, the .graphql schema is the source of truth —
  this section documents the business meaning, validation rules, and error codes.
-->

**Endpoint:** `[e.g., POST /graphql]`
**Authentication:** `[e.g., Authorization: Bearer <token> header]`

### Types

<!--
  List the main input/output types. Focus on types that are not self-evident from the schema.
  Omit this section if the schema file is the canonical reference.
-->

```graphql
type [TypeName] {
  [field]: [Type]
}

input [InputName] {
  [field]: [Type]  # required / optional
}
```

### Queries

| Query | Description | Auth |
|---|---|---|
| `[queryName]([args])` | [description] | ✅ / ❌ |

#### `[queryName]`

**Arguments:**

| Argument | Type | Required | Description |
|---|---|---|---|
| `[arg]` | `[Type]` | ✅ | [description] |

**Returns:** `[TypeName]`

**Errors:**

| Code | Scenario |
|---|---|
| `[ERROR_CODE]` | [scenario] |

---

### Mutations

| Mutation | Description | Auth |
|---|---|---|
| `[mutationName]([args])` | [description] | ✅ / ❌ |

#### `[mutationName]`

**Arguments:**

| Argument | Type | Required | Description |
|---|---|---|---|
| `[arg]` | `[Type]` | ✅ | [description] |

**Returns:** `[TypeName]`

**Errors:**

| Code | Scenario |
|---|---|
| `[ERROR_CODE]` | [scenario] |

---

### Subscriptions

| Subscription | Description | Trigger |
|---|---|---|
| `[subscriptionName]` | [description] | [what triggers it] |

---

## gRPC API

<!--
  Include this section if your project uses gRPC.
  Remove it if your project does not use gRPC.

  Document every RPC method defined in your .proto files.
  The .proto file is the source of truth for message shapes —
  this section documents the business meaning, validation rules, and error codes.
-->

**Proto package:** `[e.g., com.example.v1]`
**Server address:** `[e.g., grpc.example.com:443]`
**Authentication:** `[e.g., JWT in Authorization metadata / mTLS]`

### Service Overview

| RPC Method | Type | Description |
|---|---|---|
| `[ServiceName]/[MethodName]` | Unary / Server streaming / Client streaming / Bidirectional | [description] |

### `[ServiceName]`

#### `[MethodName]`

**Type:** `[Unary / Server streaming / Client streaming / Bidirectional]`

**Request:** `[MessageType]`

| Field | Type | Required | Description |
|---|---|---|---|
| `[field]` | `[proto type]` | ✅ | [description] |

**Response:** `[MessageType]`

| Field | Type | Description |
|---|---|---|
| `[field]` | `[proto type]` | [description] |

**Errors (gRPC status codes):**

| Status code | Scenario |
|---|---|
| `NOT_FOUND` | [scenario] |
| `INVALID_ARGUMENT` | [scenario] |
| `PERMISSION_DENIED` | [scenario] |

<!--
  CLI Tool projects: document CLI commands in docs/specs/cli-contract.md, not here.
  api-contract.md covers REST/GraphQL/WebSocket endpoints only.
-->
