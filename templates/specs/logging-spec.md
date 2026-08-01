# logging-spec.md

## Rules

- This file acts as the logging index and rule definition.
- Do not put module logging details in this file.
- Each module must have its own logging file named `log-<module-name>.md`.
- Each module logging file must follow the rules and format defined in this document.
- Direct print / console statements are NOT allowed. Always use the project's shared logger utility.

### Implementation Rules

- The log file must list every log point in the module in the order they are called.
- After implementation, if function names or file paths change, update the matching log file immediately.
- File paths must be relative to the project root.

When to generate the log file and which step triggers it is defined in AGENTS.md → Module Completion Check.

---

## Logger Instantiation

At the top of each file, create a logger instance scoped to that module's name.

The exact API depends on the logging library used in this project. Use whatever the project's
shared logger utility provides. Common patterns across languages and frameworks:

| Language / Framework | Typical pattern |
|---|---|
| Node.js (custom util) | `const logger = createLogger("MODULE")` |
| Node.js (winston) | `const logger = winston.child({ module: "MODULE" })` |
| NestJS | `private readonly logger = new Logger(ClassName.name)` |
| Python | `logger = logging.getLogger("MODULE")` |
| Go (slog) | `logger := slog.With("module", "MODULE")` |
| Go (zap) | `logger := zap.L().With(zap.String("module", "MODULE"))` |
| Laravel | `Log::channel("MODULE")` or tagged via context |
| Spring Boot | `private static final Logger log = LoggerFactory.getLogger(ClassName.class)` |

If this project uses a shared logger utility, document its instantiation pattern here
and remove the examples above.

The module name passed to the logger must match the Module Naming Convention table below.

---

## Log Output Destination

Logs must be written to both console and file simultaneously.

Each module writes to its own log file, named with the module name and the timestamp of when the session started:

```
logs/<module-name>_<YYYY-MM-DD_HH-mm-ss>.log
```

Examples:
```
logs/order_2026-06-12_10-23-01.log
logs/inventory_2026-06-12_10-23-01.log
logs/payment_2026-06-12_10-23-01.log
```

The timestamp is captured once at application startup and shared across all modules for that session,
so all log files from the same run share the same timestamp.

The `logs/` directory must be created automatically at application startup if it does not exist.
Log files must be appended to within a session, never overwritten.
The shared logger utility is responsible for handling file writes — individual modules do not write
to files directly.

---

## Log Output Format

```
[<ISO 8601 timestamp>] [<LEVEL>] [<MODULE>] <message>
  → <data as key=value or JSON if provided>
```

Example:

```
[2026-06-12T10:23:01.123Z] [INFO]  [ORDER]     create order — start
  → {"userId": "u_001", "itemCount": 3}

[2026-06-12T10:23:01.400Z] [INFO]  [INVENTORY] deduct stock — start
  → {"productId": "p_099", "requested": 2}

[2026-06-12T10:23:01.456Z] [WARN]  [INVENTORY] deduct stock — failed: insufficient stock
  → {"productId": "p_099", "current": 0, "requested": 2}

[2026-06-12T10:23:01.789Z] [ERROR] [PAYMENT]   payment API call — failed: Connection timeout
  → {"message": "Connection timeout", "stack": "..."}

[2026-06-12T10:23:01.800Z] [INFO]  [ORDER]     create order — end: success
  → {"orderId": "o_001", "userId": "u_001"}
```

---

## Message Format Rules

Every log message must follow this pattern:

```
<operation> — <state>
```

- `<operation>` is the action being performed (e.g. create order, deduct stock, payment API call)
- `<state>` describes where in the operation this log fires

| State | When to use |
|---|---|
| `start` | entering the function or operation |
| `end: success` | operation completed successfully |
| `end: <reason>` | operation completed with a non-error outcome (e.g. end: not found, end: skipped) |
| `failed: <reason>` | error or exception occurred |
| `warning: <reason>` | unexpected but non-fatal state |

This means every log line is self-describing. Reading the log alone tells you which module,
which operation, and what happened at that point — without needing to read the source code.

---

## Module Naming Convention

Use a single short name in uppercase that matches the feature or layer.

```
ORDER          order management
INVENTORY      stock and inventory
PAYMENT        payment processing
AUTH           authentication and authorisation
USER           user management
DB             database transactions
HTTP           incoming requests and responses
QUEUE          message queue
CACHE          cache operations
CRON           scheduled jobs
STARTUP        application initialisation
```

Add new module names to this list as they are created.

---

## Log Levels

| Level | When to use |
|---|---|
| `info` | Normal flow — start, successful steps, end |
| `warn` | Unexpected but non-fatal — retry, fallback, rejected business rule |
| `error` | Failures that need attention — exceptions, rollbacks, external call errors |
| `debug` | Development only — gated by env flag, never on by default in production |

The exact level names used in code depend on the logging library:

| Canonical level | Node/Winston | Python | Go (slog/zap) | Laravel | Spring |
|---|---|---|---|---|---|
| `info` | `.info()` | `.info()` | `.Info()` | `Log::info()` | `.info()` |
| `warn` | `.warn()` | `.warning()` | `.Warn()` | `Log::warning()` | `.warn()` |
| `error` | `.error()` | `.error()` | `.Error()` | `Log::error()` | `.error()` |
| `debug` | `.debug()` | `.debug()` | `.Debug()` | `Log::debug()` | `.debug()` |

Use the method name that matches your library. The canonical level name is used in log output
and in this document — the code method name follows the library.

---

## Required Log Points

| Point | Level | Message pattern |
|---|---|---|
| Function entry | info | `<operation> — start` |
| Key decision (branch that changes outcome) | info / warn | `<operation> — warning: <reason>` |
| Before external call (DB, API, queue, cache) | info | `<operation> — start` |
| After external call (success) | info | `<operation> — end: success` |
| After external call (non-fatal failure) | warn | `<operation> — warning: <reason>` |
| Exception / error handler | error | `<operation> — failed: <reason>` |
| Function exit (success) | info | `<operation> — end: success` |
| Transaction start | info | `transaction — start` |
| Transaction commit | info | `transaction — end: success` |
| Transaction rollback | error | `transaction — failed: rollback` |
| Job start | info | `<job name> — start` |
| Job finish | info | `<job name> — end: success` |

---

## Data Field Rules

- Always include the IDs needed to trace this call across modules (e.g. userId, orderId, resourceId).
- NEVER log: passwords, tokens, API keys, credit card numbers, or any PII.
- `debug` level is for development only — never put critical information exclusively in debug logs.

---

## Request Tracing

Every external entry point must generate a `trace_id` and propagate it through all downstream log calls within that request, pipeline run, or LLM call.

**When to generate:**

| Project type | Entry point |
|---|---|
| Web App / API | Incoming HTTP request handler (generate once, before any module calls) |
| Data Pipeline | Pipeline trigger / DAG run start |
| AI / LLM App | Each LLM call or user turn |
| Background Job | Job start (one trace_id per job execution) |

**How to generate:** UUID v4 (e.g. `crypto.randomUUID()` in Node.js, `uuid.uuid4()` in Python).

**How to propagate:** Pass as a parameter through function calls, or store in a request-scoped context (e.g. AsyncLocalStorage in Node.js, `contextvars` in Python). Do not regenerate downstream.

**How to include in logs:** Add `trace_id` as the first field in the data payload on every log line within the traced operation.

```
[2026-06-12T10:23:01.123Z] [INFO]  [ORDER]     create order — start
  → {"trace_id": "a1b2c3d4-...", "userId": "u_001", "itemCount": 3}

[2026-06-12T10:23:01.400Z] [INFO]  [INVENTORY] deduct stock — start
  → {"trace_id": "a1b2c3d4-...", "productId": "p_099", "requested": 2}

[2026-06-12T10:23:01.456Z] [ERROR] [PAYMENT]   payment API call — failed: timeout
  → {"trace_id": "a1b2c3d4-...", "message": "Connection timeout"}
```

The same `trace_id` threads all three log lines together — you can filter by `trace_id` in any log aggregator to see the complete chain for one request.

**Not applicable to:** Library / SDK projects (libraries do not own entry points and should not generate trace IDs).

---

## Module Log File Format

Each `docs/modules/<module-name>/log-<module-name>.md` must contain a table in this exact
shape — it is parsed by `verify_spec_code.py --adapter <language>_logging` to confirm the
log points listed here actually exist in the source code, not just in the doc:

```
| Function | Operation | State | Level |
|---|---|---|---|
| create_order | create order | start | info |
| create_order | create order | end: success | info |
| create_order | create order | failed: insufficient stock | error |
```

- **Function** — the exact function/method name in source (must match a `def` in code).
- **Operation** — the human-readable label used in the message, before ` — ` (em dash).
- **State** — `start` / `end: <reason>` / `failed: <reason>` / `warning: <reason>`, per
  Message Format Rules above. The free-text reason does not need to match code exactly —
  only the leading word (`start`/`end`/`failed`/`warning`) is compared.
- **Level** — canonical level from the Log Levels table (`info` / `warn` / `error` / `debug`),
  not the code's method name (e.g. Python's `.warning()` is still `warn` here).

One row per log point, in call order, as already required above. This table is in addition
to — not a replacement for — the free-text call-order description if you want to keep one.

**Running the check** (once a language detector exists — see `docs/contributing-adapters.md`):

```bash
python3 docs/script/validators/verify_spec_code.py --project-type TYPE \
    --adapter logging --spec docs/modules/ --src src/ --strict
```

`--adapter logging` runs every registered language detector at once (Python + JS/TS/React
today); pass `--adapter python_logging` or `--adapter javascript_logging` instead to check
only one language. `--spec` accepts either one `log-<module-name>.md` file or a directory
(e.g. `docs/modules/`) to check every module's log points in one run.

---

## Module Log Files

| Module | Log File |
|---|---|
| _(add modules here as they are created)_ | |
