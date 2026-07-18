# Debug Instrumentation Rules

Framework-agnostic. Map each layer below to whatever your stack actually calls it
(e.g. "Controller" might be a Django view, an Express route handler, a Go HTTP handler,
or a Spring `@RestController` method — the placement and intent are the same).

## Before Starting: Ask About the Stack

Before instrumenting a flow, ask the user (unless already established earlier in this
conversation or documented in docs/architecture/backend.md / frontend.md):

1. **Language/framework** for this flow (e.g. "Express + Prisma", "Django", "Go net/http",
   "vanilla CLI in Python")
2. **Logging mechanism** to use — project's existing logger, or plain print/console statements
   if none exists
3. **Which layers from the list below apply** to this specific flow — skip asking about layers
   that obviously don't apply (e.g. don't ask about "Client-Side Request Preparation" for a
   backend-only cron job), but confirm the ones that are ambiguous

Once the stack is known, instrument using that language's actual syntax and the project's real
function/file names — not placeholder pseudocode. The examples in each layer below are
illustrative only; replace them with what the target codebase actually looks like.

If the same stack is used repeatedly in a session, do not re-ask each time — confirm once and
reuse for subsequent flows unless the user switches stacks.

## Requirements

* Do not modify business logic.
* Do not add instrumentation to files that are not listed in the selected module-data-flow.
* Clearly mark all debug code with a `DEBUG:` comment/marker in the language's native comment syntax.
* Print the key data being passed between layers — not everything, just enough to trace the flow.
* Use the project's actual logging/print mechanism (`console.log`, `print`, `fmt.Println`,
  `logger.debug`, etc.) — whatever the language and project already use.
* Only add instrumentation for layers that exist in the code being instrumented. Skip any layer
  below that has no equivalent in this stack or this particular flow.

## Debug Format

```
DEBUG: <Flow Name> - <Step Name>
<group/indent start, if the language supports it>
print("<Label>", value)
<group/indent end>
```

Use the language's native grouping mechanism if one exists (e.g. `console.group` in JS,
indentation + a clear prefix in Python, structured log fields in Go). If none exists, a single
prefixed line per piece of data is fine. Add a breakpoint/debugger statement only when explicitly
requested.

---

## Layers

Each layer lists: where to place the instrumentation, and what data to print. Map the layer name
to whatever your framework calls that concept.

The table below shows which layers typically apply to each project type.
"–" means the layer is rarely needed or has no equivalent; individual flows may vary.

| Layer | Web App | Microservices | CLI Tool | Library | Data Pipeline | ML Pipeline | AI/LLM App | IaC/DevOps | Mobile App |
|---|---|---|---|---|---|---|---|---|---|
| 1. Entry Point | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 2. Client-Side Request Prep | ✅ | – | – | – | – | – | ✅ | – | ✅ |
| 3. Outbound Call | ✅ | ✅ | ✅ | – | ✅ | – | ✅ | – | ✅ |
| 4. Request Handling Entry | ✅ | ✅ | – | – | – | – | – | – | – |
| 5. Validation | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | – | ✅ |
| 6. Business Logic Entry | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | – | ✅ |
| 7. Business Rule Decisions | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | – | ✅ |
| 8. Data Access — Read | ✅ | ✅ | ✅ | – | ✅ | ✅ | ✅ | – | ✅ |
| 9. Data Access — Write | ✅ | ✅ | ✅ | – | ✅ | ✅ | – | – | ✅ |
| 10. Transactional Boundaries | ✅ | ✅ | – | – | ✅ | – | – | – | ✅ |
| 11. Response Construction | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| 12. Client-Side Result Handling | ✅ | – | – | – | – | – | ✅ | – | ✅ |
| 13. State/Cache Invalidation | ✅ | ✅ | – | – | – | – | – | – | ✅ |
| 14. UI/Output Refresh | ✅ | – | ✅ | – | – | – | – | – | ✅ |

### 1. Entry Point (UI event, CLI command, request handler, queue message, pipeline trigger, or LLM call)

Where the first external trigger enters the code. Map to whichever applies to this project type:

| Project type | Entry point |
|---|---|
| **Web App / Microservices** | HTTP route handler / GraphQL resolver / WebSocket message handler |
| **CLI Tool** | Command parser — first line after args are parsed |
| **Library / SDK** | Public function — first line of the exported function body |
| **Data Pipeline** | Stage entry — first line after the input dataset or file is received |
| **ML Pipeline** | Stage entry — after input schema is validated, before processing begins |
| **AI / LLM App** | Prompt assembly function — immediately before the LLM API call; also at each MCP tool call entry (tool name + input args) and tool response receipt |
| **Background Job** | Consumer handler — first line after the queue message is received |
| **IaC / DevOps** | CI/CD pipeline trigger — first step in the `terraform plan` or `apply` job; first task in an `ansible-playbook` run |
| **Mobile App** | App launch handler (`onCreate` / `viewDidLoad`) for startup flows; deep-link handler entry for navigation flows; ViewModel / BLoC method entry for feature flows |

Placement: immediately after the triggering input is captured, before any processing begins.

Print:
* The raw input as received (request body, CLI args, queue payload, input row count, prompt variables)

### 2. Client-Side Request Preparation (if applicable)

Where a frontend or client assembles the payload before sending it onward — building a request
body, preparing a mutation payload, assembling a CLI subprocess call.

Placement: immediately before the outgoing call is made.

Print:
* The assembled payload/arguments

Skip this layer entirely for server-only or CLI-only flows with no client/server split.

### 3. Outbound Call (HTTP request, RPC, queue publish, subprocess call)

Where the client/caller actually sends the request to the next layer.

Placement: immediately before, and immediately after, the call.

Print:
* Before: destination (URL/endpoint/queue name), method/verb, payload
* After: raw response or result received

Skip if the flow is a single process with no network/IPC boundary.

### 4. Request Handling Entry (server-side entry point)

Where the receiving side first gets the request — a controller method, a route handler, a queue
consumer, a CLI command's main function.

Placement: first statement inside the handler.

Print:
* Path/route params, query params, request body (or equivalent: command args, message payload)

### 5. Validation

Where input is validated or parsed against a schema.

Placement: immediately after validation/parsing completes.

Print:
* The validated/normalized data (not the raw input again — show what survived validation)

Skip if there is no formal validation step.

### 6. Business Logic Entry

Where the core business logic begins — a service method, a use-case function, a domain handler.

Placement: first statement inside the function.

Print:
* The input the business logic receives
* Any identifiers needed to trace this call (user ID, resource ID, etc.)

### 7. Business Rule Decisions

Any point where a business rule, conditional check, or decision determines the outcome —
a duplicate check, an authorization decision, an availability check, an approval threshold.

Placement: immediately after the check/decision is made.

Print:
* The input to the decision
* The result of the check
* The outcome/branch taken

This is one of the most valuable instrumentation points — include it at every meaningful
decision branch, not just the first one.

### 8. Data Access — Read

Where data is fetched from a database, cache, file, or external store.

Placement: immediately before, and immediately after, the read.

Print:
* Before: the query/lookup parameters (filter, key, query string)
* After: what was returned (or "not found")

### 9. Data Access — Write

Where data is created, updated, or deleted in a database, cache, file, or external store.

Placement: immediately before the write.

Print:
* What is being written (the payload, the target identifier, the operation type)

### 10. Transactional Boundaries (if applicable)

Where multiple writes are grouped into a single atomic operation.

Placement: immediately before starting the transaction, and at commit/rollback.

Print:
* What operations are included
* Commit success, or the rollback reason on failure

Skip if the flow has no multi-step atomic operation.

### 11. Response Construction

Where the result is shaped into whatever gets returned — a response DTO, a CLI exit message, a
rendered template context.

Placement: immediately before the result is sent/returned.

Print:
* The shaped output
* Status/exit code, if applicable

### 12. Client-Side Result Handling (if applicable)

Where the caller receives and processes the result — parsing a response, handling a CLI exit
code, consuming a queue acknowledgment.

Placement: immediately after the result is received.

Print:
* The received result

### 13. State/Cache Invalidation (if applicable)

Where local state, a cache, or a derived view is invalidated or refreshed as a side effect of
the operation succeeding.

Placement: immediately before the invalidation/refresh call.

Print:
* What is being invalidated (cache key, state slice, UI region)
* The triggering result, if relevant

Skip if the flow has no caching or derived-state layer.

### 14. UI/Output Refresh (if applicable)

Where the user-facing output changes as a result of the completed flow — clearing a form,
re-rendering a list, printing a final CLI message.

Placement: immediately before the visible state change.

Print:
* The state before and after the change, if both are easily available

Skip for pure backend/API flows with no UI.

---

## Completion Report

After implementation, report:

* Flow instrumented
* Files modified
* Which layers from the list above were actually used (and which were skipped, and why)
* Data printed at each location
* Expected execution order

Example:

```text
Flow instrumented:
Create Location

Layers used (this flow has no client/cache layer, so 2, 10, and 13 were skipped):
1. Entry Point
4. Request Handling Entry
5. Validation
6. Business Logic Entry
7. Business Rule Decisions (duplicate check)
8. Data Access — Read
9. Data Access — Write
11. Response Construction

Files modified:
- location_create_form.<ext>
- location_controller.<ext>
- location_service.<ext>
- location_repository.<ext>

Expected execution order:
Entry Point
→ Request Handling Entry
→ Validation
→ Business Logic Entry
→ Data Access — Read (duplicate check)
→ Business Rule Decisions
→ Data Access — Write
→ Response Construction
```
