---
name: code-quality-check
description: Use when reviewing code quality/architecture — during Step 1c of a retrofit, whenever the user explicitly asks for a code quality or architecture review of this project, or when Learning Checkpoint A escalates because the user confirms unfamiliar/inherited/unreviewed code needs a full review. Checks layering, Package First, complexity, naming, schema, security, error handling, observability, permission consistency, state machine consistency, interface overlap, synthetic test data, cross-component interfaces, and performance — scored High/Medium/Low/Nit against this project's declared type.
---

# Code Quality Check

Used during the "Retrofitting an Existing Project" workflow (see AGENTS.md).

Run this immediately after Step 1 (Read Codebase) and before Step 2 (Documentation).

Do not begin writing documentation until all High severity issues have been resolved.

**Also run this in full — not the lightweight Checkpoint A questions — whenever the user
confirms this code needs a full quality review** (asked because there is no project
record of who built it or whether it was reviewed — not because of a guess about whose
code it is; see `guidance/learning-checkpoints/common.md` → Checkpoint A for the exact
ask-first trigger). In this case each finding must also include the two extra fields
defined under **Report Format** below (Why It's Wrong / Correct Pattern) — the point is
for the person reviewing it to learn from the findings, not just get a fix list.

---

# Required Context

Read the documents for your declared project type before inspecting code. **Hybrid
projects (e.g. `Data Pipeline + Web App`):** there is no combined row below — read and
apply every row for each declared type, union the "What to inspect" and Layering rules
across them, same as the guidance-file rule in `AGENTS.md`.

| Project type | Read before inspecting |
|---|---|
| **Web App** | `current-state.md`, `docs/architecture/*`, `docs/business/*`, `docs/specs/data-model.md`, `docs/specs/permissions.md`, `docs/project-plan.md` |
| **Microservices** | `current-state.md`, `docs/architecture/*`, `docs/business/*`, `docs/specs/data-model.md`, `docs/specs/permissions.md`, `docs/specs/service-catalog.md`, `docs/project-plan.md` |
| **CLI Tool** | `current-state.md`, `docs/architecture/architecture.md`, `docs/specs/cli-contract.md`, `docs/project-plan.md` |
| **Library / SDK** | `current-state.md`, `docs/architecture/architecture.md`, `docs/specs/public-api.md`, `docs/project-plan.md` |
| **Data Pipeline** | `current-state.md`, `docs/architecture/architecture.md`, `docs/specs/pipeline-contract.md`, `docs/specs/data-model.md`, `docs/project-plan.md` |
| **ML Pipeline** | `current-state.md`, `docs/architecture/architecture.md`, `docs/specs/pipeline-contract.md`, `docs/specs/model-contract.md`, `docs/project-plan.md` |
| **AI / LLM App** | `current-state.md`, `docs/architecture/architecture.md`, `docs/specs/llm-contract.md`, `docs/specs/eval-spec.md`, `docs/project-plan.md` |
| **IaC / DevOps** | `current-state.md`, `docs/architecture/topology.md`, `docs/specs/runbook.md`, `docs/specs/drift-policy.md`, `docs/project-plan.md` |
| **Mobile App** | `current-state.md`, `docs/architecture/architecture.md`, `docs/architecture/frontend.md`, `docs/specs/mobile-contract.md`, `docs/project-plan.md` |

Then inspect ONLY:

| Project type | What to inspect |
|---|---|
| **Web App / Microservices** | Application entry point; data layer; one complete vertical slice |
| **CLI Tool** | Command parser; handler function; one complete command path |
| **Library / SDK** | Public API function; one internal implementation path |
| **Data Pipeline / ML Pipeline** | Pipeline entry; one stage; one output writer |
| **AI / LLM App** | Prompt assembly; LLM call; response parser |
| **IaC / DevOps** | Module input validation; one complete resource group definition |
| **Mobile App** | App entry / screen component; ViewModel/Presenter; one complete navigation flow |

Do NOT scan unrelated modules.

Do NOT read the entire repository unless explicitly required by current-state.md.

---

# Objectives

Evaluate whether the implementation is:

- Consistent with the documented architecture
- Consistent with documented business rules
- Following AGENTS.md principles
- Safe to continue documentation

Focus on correctness rather than style.

---

# Report Format

**Code Quality Check — [Project Name]**

| Area | Finding | Evidence | Severity | Recommendation |
|------|----------|----------|----------|----------------|
| Layering | ... | src/... | High | ... |

Only include areas that contain findings.

**Good Things (optional but encouraged)** — note patterns worth keeping, not just problems.
This applies regardless of project type — a well-isolated Data Pipeline stage boundary, a
clean CLI flag/handler split, a Terraform module with real destroy protection, etc. are all
equally valid entries. Use the same evidence discipline as findings — real file/function
names, not generic praise:

| Area | What's good | Why it's worth keeping |
|------|-------------|------------------------|
| Layering | ... | ... |

Skip this table if nothing stands out — it's for genuinely worth-noting patterns, not a
participation entry for every review. The point is the same as the Learning Checkpoint's
teach-back: understanding what's correct and why matters as much as catching what's wrong.

**When taking over someone else's code** (see the note at the top of this file), add two
more columns to every row:

| Area | Finding | Evidence | Severity | Recommendation | Why It's Wrong | Correct Pattern |
|------|----------|----------|----------|----------------|-----------------|------------------|

- **Why It's Wrong** — the general principle being violated, not a guess about this
  specific author's intent (not "the author probably didn't know better"). Ground it in
  the Layering / Type-Specific rule this project's declared type actually uses — see the
  Layering table and Type-Specific Checks sections below for the rule per type. For
  example: a Web App controller writing to the DB directly can't be unit-tested without
  a database; a CLI Tool's flag parser running a network call during parsing means the
  command can't be tested without side effects; a Data Pipeline stage skipping input
  contract validation risks silently corrupting every downstream stage; a Terraform
  module with a hardcoded secret is a security finding regardless of which cloud it targets.
- **Correct Pattern** — what the idiomatic fix looks like for this project's actual
  language/framework/type, named concretely using real file, function, or resource names
  from this codebase — not a generic textbook description disconnected from it, and not
  assumed to be a web-app fix by default.

Both fields describe the rule and the fix shape, not this specific finding's root cause —
the Evidence Rules below still apply: never guess why the original author did something,
only what the code does and what the correct alternative looks like.

Possible areas:

- Layering
- Package First
- Complexity
- Missing Pattern
- Naming
- Schema
- Security
- Error Handling
- Observability
- Permission Consistency
- State Machine Consistency
- API Endpoint Overlap
- Synthetic Test Data
- Cross-Component Interface
- Performance
- Other

---

# Evidence Rules

Every finding MUST include:

- File
- Function / Class / Endpoint
- Why it is a problem

Example:

Evidence:
src/orders/controller.ts
updateOrder()

Business logic performs database writes directly instead of calling the service layer.

If evidence cannot be found:

Output

Unable to verify

Never guess.

Never infer missing behavior.

---

# Severity Guide

**Why only High blocks:** the goal of this review is to make the codebase healthier over
time, not to reach a perfect state before continuing. A change that clearly improves code
health should not be held up chasing every Medium/Low/Nit item — that's why only High
blocks Step 2; Medium/Low get queued for the current sprint instead of blocking now, and
Nit isn't queued at all. If you (the user) disagree with a finding's severity or validity,
that's a discussion, not something to accept silently — downgrade or drop it together, with
the reason recorded, rather than the review being the final word by default.

## High

Only use High when one of the following is true:

- Incorrect business behavior
- Security vulnerability
- Data corruption risk
- Architecture contradiction
- Documented business process cannot be completed
- Canonical documentation conflicts with implementation

High findings MUST be fixed before Step 2.

---

## Medium

Use when:

- Maintainability issue
- Duplicate logic
- Missing validation
- Missing index
- Confusing API
- Technical debt that should be addressed before the next feature

Do not fix now.

Append to the current sprint in project-plan.md.

---

## Low

Minor issues:

- Naming
- Small cleanup
- Documentation mismatch
- Minor consistency improvements

Append to the current sprint.

---

## Nit (optional — not a formal severity, not queued)

Use when the observation is a personal style preference, not backed by this project's
style guide, an existing convention in the codebase, or an objective correctness rule. The
test: if the codebase has no established rule either way and this is just how you'd
personally write it, it's a Nit — not a Low.

Prefix the finding with `Nit:` in the Finding column instead of giving it a severity.

Do NOT append Nits to project-plan.md — they carry no obligation to act. They're visibility
only, and the user can ignore them freely without needing to justify skipping one (unlike a
Low finding, which at least got queued for a reason grounded in a real rule).

---

# Area-Specific Rules

## Layering

Check that each layer contains only what belongs to it.
The layer names and rules depend on the project type — use the row that matches:

| Project type | Entry layer rule | Middle layer rule | Data / output layer rule |
|---|---|---|---|
| **Web App** | Controller: HTTP binding only (parse request, return response) | Service: business logic only | Repository: DB queries only — no business logic |
| **Microservices** | Varies by service transport — HTTP: Controller (binding only); gRPC: RPC Handler (request unmarshalling only); Event-driven: Consumer / Listener (message parsing only) | Service: business logic only | Repository: DB queries only — no business logic |
| **CLI Tool** | Command parser: flag/arg parsing only | Handler / UseCase: command logic | Store / Writer: file I/O or config persistence only |
| **Library / SDK** | Public API function: input validation + delegation only | Internal implementation | No persistence layer — outputs are return values |
| **Data Pipeline** | Stage entry: input contract validation only | Transform / Enrich: data logic | Writer / Sink: output contract only — no data logic |
| **ML Pipeline** | Stage entry: schema + quality checks | Model / Transform: inference or feature logic | Artifact writer: serialisation only |
| **AI / LLM App** | Request handler: prompt assembly only | LLM caller: API call + retry logic | Response parser: output extraction only |
| **Mobile App** | View / Screen: UI rendering and user event handling only — no API calls or business logic | ViewModel / Presenter / BLoC: state management and business logic | Repository / Service: API calls and local storage only — no UI logic |
| **IaC / DevOps** | Not applicable — IaC is declarative; check that module input validation is isolated and resource definitions contain no embedded scripting that belongs in a separate module | — | — |

Business logic in the entry layer is always a finding, regardless of project type.

---

## Package First

Before recommending custom code:

Check whether an existing dependency already solves the problem.

If duplicate custom implementation exists:

Report it.

Do not recommend rewriting unless necessary.

---

## Complexity

Check whether the code solves the actual, current, documented requirement — or an imagined
future one that isn't written down anywhere (project-plan.md, research.md, or an actual
ticket). Over-engineering is a maintainability cost with no offsetting benefit when the
extensibility it was built for never gets used.

| Project type | What to look for |
|---|---|
| **Web App / Microservices** | Abstraction layers (interfaces, factories, strategy patterns, dependency-injection containers) with only one real implementation and no documented plan for a second |
| **CLI Tool** | A generic plugin/config system built for a small fixed set of commands with no stated need for third-party extensibility |
| **Library / SDK** | Configuration options, hooks, or extension points with zero callers using them, added speculatively "in case someone needs it" |
| **Data Pipeline / ML Pipeline** | A generic multi-stage orchestration framework built for a pipeline that only ever runs one fixed sequence |
| **AI / LLM App** | Multi-step agent/tool-chaining orchestration for a task a single prompt call could resolve just as reliably |
| **IaC / DevOps** | Wrapper modules or parameterized variables for values that never actually vary across this project's environments |
| **Mobile App** | Generic state-management or navigation abstraction for a screen flow that never branches |

Check:
- Can you point to a real, current caller/requirement that needs this flexibility today?
- Would removing the abstraction and inlining the single real case make the code easier to
  follow, with no loss of behavior?

Severity: **Medium** — usually a maintainability cost, not a correctness bug. Only use
**High** if the added complexity itself is the source of an actual bug (e.g. a generic
dispatch layer that silently drops an unhandled case).

Recommendation: simplify to match the actual requirement, or — if genuine near-term
extensibility is planned — point to where that's documented; if it isn't documented
anywhere, that's itself part of the finding.

---

## Missing Pattern

The mirror image of Complexity above: instead of an abstraction with no real second case,
this is the same type-dispatch logic (an `if`/`elif` chain or `isinstance`/type-check chain
over the same fixed set of types) hand-duplicated across two or more functions or files. Each
copy has to be kept in sync by hand whenever a type is added, which is exactly the kind of
drift risk a Registry, Strategy, or plain polymorphism (a method on each type instead of a
chain checking every type from outside) is for.

| Project type | What to look for |
|---|---|
| **Web App / Microservices** | The same business-type switch (order status, payment method, notification channel...) reimplemented in more than one function/file instead of one lookup table or polymorphic method |
| **CLI Tool** | Subcommand-name → handler mapping duplicated between the parser and the dispatcher instead of one command registry |
| **Library / SDK** | The same input-type branching (`isinstance`/type check) repeated across multiple public functions instead of dispatching once at the boundary |
| **Data Pipeline / ML Pipeline** | Per-source-format or per-source-system branching (CSV vs. JSON vs. API vs. DB) duplicated across multiple stages instead of one pluggable reader/writer interface |
| **AI / LLM App** | Per-provider branching (OpenAI vs. Anthropic vs. local model, or per-tool-name dispatch) duplicated across call sites instead of one adapter interface |
| **IaC / DevOps** | Per-cloud-provider or per-environment conditional blocks duplicated across multiple modules instead of parameterized/adapter modules |
| **Mobile App** | Per-platform (iOS/Android) branching duplicated inside shared business logic instead of one platform-abstraction layer |

Check:
- Is the exact same set of types/cases branched on in two or more places?
- When a new type/case was added, did more than one of those places have to be edited to keep
  it working? (Check `changelog.md` / `git log` for the type that was added most recently — did
  every duplicate site actually get updated, or did one get missed?)
- Would collapsing the duplicates into one registry/dispatch table, or moving the per-type
  logic onto the type itself (polymorphism), remove the duplication with no loss of behavior?

Severity: **Medium** — usually a maintainability/drift-risk cost, not a correctness bug yet.
Use **High** only if a duplicate site was evidenced to have actually drifted (missing a case
the other site(s) already handle — an outdated `elif` chain that silently falls through).

Recommendation: name the specific pattern that fits (Strategy, Factory, Registry, Template
Method, or plain polymorphism) and point to where this codebase already does it well, if it
does — reuse that shape rather than inventing a new one.

---

## Naming

Check for inconsistencies that reduce readability. Apply only the categories that exist in this project:

- Module / package / stage names
- Public function or method names (Library, CLI, Service)
- Endpoint or command names (Web App, CLI Tool)
- Repository / store / DAO method names (Web App, Microservices)
- Pipeline stage and dataset names (Data Pipeline, ML Pipeline)
- Prompt IDs and variable names (AI / LLM Application)

Only report inconsistencies that reduce readability.

---

## Schema

Check for:

- Missing indexes
- Missing constraints
- Poor foreign keys
- Frequently queried columns without indexes

Only report when evidence exists.

---

## Security

Check for:

- Missing authorization
- Missing authentication
- SQL injection
- Unsafe file handling
- Unsafe deserialization
- Sensitive information leakage

Do not speculate.

---

## Error Handling

Check for:

- Missing exception handling
- Ignored errors
- Missing rollback
- Missing retries where required

---

## Observability

Run this check for all project types except Library / SDK.

Apply only the rows that match the project type(s) declared in this project.

### trace_id propagation

| Project type | What to check |
|---|---|
| **Web App / Microservices** | Does the HTTP request handler generate a `trace_id` before calling any module? Is `trace_id` passed through to all downstream log calls? |
| **Data Pipeline** | Does each pipeline run / DAG trigger generate a `trace_id` or equivalent run-scoped identifier? Is it included in every stage log entry? |
| **ML Pipeline** | Does each training or inference run generate a run ID? Is it included in every stage and artifact log? |
| **AI / LLM App** | Does each LLM call generate a `trace_id`? Is it included in the LLM call log entry and all related tool call logs? |
| **CLI Tool** | Does each command invocation generate or accept a `trace_id` / session ID when the command spans multiple steps? |
| **Background Job** | Does each job execution generate a `trace_id` at start? Is it included in all log entries for that execution? |
| **Mobile App** | Does each API call from the app include a correlation / session ID in the request (e.g., `X-Session-Id` header)? Is it included in local log entries for that request? |
| **IaC / DevOps** | Not applicable — `terraform apply` / `plan` output is captured by the CI/CD runner natively; no application-level `trace_id` is needed. |

If `trace_id` is generated but not propagated into log data fields: **Medium.**
If no `trace_id` is generated at all at the entry point: **Medium.**

Not applicable to: Library / SDK, IaC / DevOps.

---

### LLM call structured log (AI / LLM Application only)

Every code path that calls an LLM must emit one structured log entry per call with at minimum:

- `trace_id`
- `prompt_version`
- `model`
- `input_tokens`
- `output_tokens`
- `latency_ms`
- `cost_usd`

Optional fields (include when applicable):
- `retrieved_chunks` — number of RAG chunks injected
- `tool_calls` — list of tool names triggered
- `judge_score` — included only when an eval run is performed

If any required field is missing from the LLM call log: **Medium.**
If no structured LLM call log exists at all: **Medium.**

---

### Pipeline stage row count logging (Data Pipeline / ML Pipeline only)

Each stage that reads and transforms data must log:
- Row count received (input)
- Row count produced (output)
- Row count rejected or skipped (if any filtering occurs)

These three numbers make it possible to diagnose data loss without re-running the pipeline.

If a stage applies filtering or aggregation but logs only "success" without row counts: **Low.**
If no row count logging exists anywhere in the pipeline: **Medium.**

---

## Permission Consistency

Read every `business/*-process.md` and collect every (Role, Action) pair.
Cross-reference against `docs/specs/permissions.md` — API Endpoint Access table.

**Source evaluation:**

| Source type | Severity |
|---|---|
| Hardcoded in code | High |
| Seeded default | Medium |
| Missing Source column in `permissions.md` | High |

**Recommendation:** Grant access, or document in `permissions.md` why a different workflow is used.

---

## State Machine Consistency

Canonical source: `business/*-object.md`

Compare against: `docs/specs/data-model.md`

| Finding | Severity |
|---|---|
| State transitions in code differ from `business/*-object.md` | High |

Business object documentation is always the source of truth.

---

## Interface Overlap

Find interfaces (endpoints, commands, functions, pipeline stages) that operate on the same resource or state without a documented reason to be separate.

| Project type | What to look for |
|---|---|
| **Web App / Microservices** | Two endpoints that mutate the same resource field: e.g., `PATCH /orders/:id/approve` and `PATCH /orders/:id/approval` |
| **CLI Tool** | Two subcommands that produce the same output or modify the same config key |
| **Library / SDK** | Two public functions with overlapping behaviour: e.g., `parse()` and `read()` that both deserialise the same format |
| **Data Pipeline** | Two stages that read the same source or write to the same destination without a clear handoff contract |
| **ML Pipeline** | Two preprocessing steps that apply the same transformation on the same feature |
| **AI / LLM App** | Two prompt templates that perform the same task (e.g., two "summarise" prompts targeting the same content type) |
| **IaC / DevOps** | Two Terraform resource blocks or modules that manage the same underlying cloud resource (e.g., two `aws_security_group_rule` blocks with identical port/protocol) |
| **Mobile App** | Two screens that display and allow editing of the same data without a documented reason (e.g., two "Edit Profile" paths reachable via different navigation flows) |

If overlap exists without a documented reason: **Medium severity.**

Recommend: merge the interfaces, or add a Design Note in the relevant spec file explaining why both exist.

---

## Synthetic Test Data

Any test data designed to trigger a failure (break-kit, chaos test, fault injection, boundary violation) must be actually executed at least once before the task is marked complete — not just designed on paper.

Why: design assumptions can be wrong. For example, a seed script might silently fill missing columns with NULL instead of failing, making a test that was supposed to fail appear to pass.

Checklist before marking a negative-case test complete:
- [ ] Run the test with the intentionally bad data
- [ ] Confirm the output is the expected failure (not a silent pass or a different error)
- [ ] Record the actual output in the task's Verify section

If the failure does not trigger as expected — treat it as a bug in the test design. Fix the test before proceeding.

Severity: **High** if a negative-case test has not been executed and verified.

---

## Cross-Component Interface Consistency

Run this check whenever a task touches any external interface definition.

An external interface is any contract between two components:

| Project type | Examples of external interfaces |
|---|---|
| **Web App** | Frontend form field ↔ backend validation rule ↔ DB column |
| **CLI Tool** | Flag name ↔ config key ↔ env var name ↔ help text |
| **Library / SDK** | Public function signature ↔ documented type ↔ serialised output format |
| **Data Pipeline** | File sensor glob ↔ data asset name ↔ dbt source name ↔ DB schema |
| **ML Pipeline** | Feature schema ↔ training input contract ↔ model artifact format ↔ serving schema |
| **Microservices** | Event schema published by service A ↔ event schema consumed by service B |
| **AI / LLM App** | Prompt variable name ↔ value injected at runtime ↔ expected output format in eval rubric; MCP tool input schema ↔ actual args the LLM sends ↔ tool output format the response parser expects |
| **IaC / DevOps** | Terraform variable name ↔ secrets manager key name ↔ env var referenced in application code; module output name ↔ consuming module input name |
| **Mobile App** | Screen route name ↔ deep link path segment ↔ `mobile-contract.md` navigation graph entry; API request field name ↔ backend contract ↔ UI display field |

For each interface touched in this task:

1. List every component that references this interface (field name, path, schema, endpoint, asset name)
2. Confirm they all point to the same underlying data / same schema / same contract
3. If any component references a different name, path, or type — flag it as a contradiction before proceeding

Severity: **High** if any mismatch is found. A gap here means a runtime error that only appears when the full stack runs together.

**External service / third-party image assumptions:**

Before writing any config or code that depends on a specific version of an external service or image:

1. State the assumption explicitly (e.g. "v0.13.3 has a standalone MAE consumer image")
2. Verify it with an actual command (e.g. check Docker Hub tags, read release notes, run the image)
3. Record the result in `docs/specs/research.md → Version Assumptions`

Do NOT commit config based on an unverified assumption. If the assumption turns out to be wrong after committing, treat it as a High finding and fix before proceeding.

**Third-party dependency upgrade:**

When a task upgrades an existing dependency (library, service image, API client):

1. List every place in the codebase that calls the dependency's API, SDK method, config key, or endpoint — not just the file being changed
2. Check the dependency's changelog or release notes for breaking changes between the old and new version
3. Verify each integration point still works after the upgrade

Severity: **High** if an upgrade is committed without enumerating and verifying all integration points.

---

**External system write consistency:**

If a task writes to an external system that has multiple representations, targets, or entities (e.g. two database tables, two API platforms, a primary record and a derived/twin record):

1. List every write target — not just the primary one
2. Verify each target independently after the write
3. If any target is missing the expected data, treat it as a High finding

Severity: **High** if only the primary write target was verified and secondary targets were not checked.

---

**Verification authority:**

For any integration verified via a UI (dashboard, admin panel, visualization tool):

1. Identify the authoritative verification method: API endpoint, database query, or CLI command that returns the same underlying data
2. Record this authoritative check in the task's Verify section — UI confirmation alone is not accepted
3. If the UI shows inconsistent or missing data but the authoritative check returns correct data, the finding is in the UI layer, not the integration. Document this explicitly and do not block task completion on a known UI rendering issue

Severity: **Medium** if only UI verification is planned with no authoritative fallback defined.

---

## Performance

Only report evidence-based issues such as:

- N+1 queries
- Full table scans
- Obvious repeated expensive operations

Do not guess.

---

## Type-Specific Checks

Run only the sub-section(s) that match the project type declared in `AGENTS.md`.
Skip sub-sections for types not declared.

---

### CLI Tool

**Flag parsing isolation**

The command parser layer must only parse flags and arguments, not execute business logic.

Check:
- Does the command parser call file systems, databases, or network services during flag parsing?
- Are flags validated beyond type-checking inside the parser?

Severity: **Medium** if I/O or external calls occur during flag parsing (belongs in the handler layer). **High** if flag parsing triggers a write or mutation.

---

**Command responsibility separation**

Each subcommand should do one thing. A subcommand that both mutates state and produces output is doing two jobs.

Check:
- Does any subcommand perform more than one distinct user-facing operation?
- Are side effects (file write, API call) mixed with read-only output in the same command path?

Severity: **Medium** if a subcommand has mixed responsibilities.

---

**Exit code consistency**

Exit codes must be consistent across all subcommands and match `cli-contract.md`.

Check:
- Do all subcommands return 0 on success and non-zero on any failure?
- Are there cases where a command exits 0 when the operation failed (silent failure)?
- Are any exit codes used that are not documented in `cli-contract.md`?

Severity: **High** if a command exits 0 on failure — callers cannot detect the error. **Medium** if exit codes are inconsistent but failures are not silent.

---

### Library / SDK

**No side effects at import**

Importing the library must not trigger I/O, network calls, global state mutation, or stdout/stderr output. Initialization must be explicit.

Check:
- Does module-level code (outside functions and classes) perform file reads, network calls, or global state changes?
- Does importing the library print to stdout or stderr?

Severity: **High** if import has side effects — breaks test isolation and integration workflows.

---

**Public API stability**

Any symbol documented in `public-api.md` must not change signature without a deprecation log entry.

Check:
- Has any public function signature changed without a corresponding deprecation log entry in `public-api.md`?
- Has any public symbol been removed that was not first listed in the deprecation log?

Severity: **High** if a public symbol was removed or had a breaking change without a deprecation log entry.

---

**Test coverage of public surface**

Every public function, class, and type must have at least one test that exercises the documented contract.

Check:
- Is there a test for each public function listed in `public-api.md`?
- Do tests verify the documented return type and error behaviour, not just "no exception thrown"?

Severity: **Medium** if a public function has no test. **High** if the only tests are on internal code and the entire public surface is untested.

---

### Data Pipeline

**Inter-stage contract verification**

Each stage must validate its input against the upstream output contract before processing. Silent truncation or skipping of invalid rows without logging is a data quality risk.

Check:
- Does each stage validate column names, types, and required fields against `pipeline-contract.md` at startup?
- Are schema mismatches logged and surfaced — not silently dropped?

Severity: **High** if a stage processes data without validating the input contract (silent data corruption risk).

---

**Idempotency**

Re-running a stage must produce the same output. A stage that appends to a file or table without first truncating or deduplicating is not idempotent.

Check:
- Can each stage be safely re-run if interrupted?
- Does a re-run produce duplicate rows in the output dataset?
- Is the output path or table overwritten (safe) or appended without deduplication (risky)?

Severity: **High** if re-running a stage produces duplicate output rows (data duplication in all downstream stages).

---

**Archive / replay guarantees**

Raw input data must be preserved before transformation so a full replay from the raw layer is possible.

Check:
- Is the raw (pre-transform) data preserved after the extract stage?
- Is there a documented replay procedure in `pipeline-contract.md`?
- Is the archive path stable (not overwritten by subsequent runs)?

Severity: **Medium** if raw data is overwritten or discarded after transformation (no replay path). **High** if the project has compliance or audit requirements and no replay path exists.

---

### ML Pipeline

**Data leakage checks**

Training data must not contain information unavailable at inference time (future-dated fields, target-derived features, test set rows in the training set).

Check:
- Are any features derived from the target variable?
- Does the training set include row keys that also appear in the held-out test set?
- For time-series data: is the split ordered correctly (train before test, no shuffle across time)?

Severity: **High** if any data leakage is found — model metrics will not generalise to production.

---

**Train / test split integrity**

Splits must be reproducible and documented.

Check:
- Is the random seed fixed and logged for every split?
- Is the split ratio documented in `model-contract.md`?
- Is split logic isolated in a single function so it cannot vary between runs?

Severity: **Medium** if seed is not fixed. **High** if the split is applied differently across two runs (non-reproducible evaluation hides real model degradation).

---

**Metric reproducibility**

Re-running training with the same data and config must produce the same metrics (within floating-point tolerance).

Check:
- Are all sources of non-determinism controlled (random seeds, dropout, data shuffle order)?
- Are metric results logged with the exact config hash or experiment ID in `experiment-log.md`?

Severity: **Medium** if results vary between runs with identical config.

---

### Microservices

**Service contract conformance**

Every cross-service API call must conform to the contract in `service-contract.md`. A caller that sends an undeclared field or omits a required field is a latent runtime failure.

Check:
- Do all inter-service request payloads match the schema in `service-contract.md`?
- Do all consumers validate the response schema before accessing fields?
- If the contract was updated, have all callers been updated to match?

Severity: **High** if a caller sends or expects fields not in the current contract — runtime failure when the receiving service validates input.

---

**Circuit breaker coverage**

Every synchronous call to another service or external dependency must have a circuit breaker or equivalent protection: timeout + retry with backoff + fallback.

Check:
- Are there synchronous inter-service calls without a timeout configured?
- Are there retry loops without a backoff strategy or max-retry cap?
- Is there a fallback (cached result, degraded response, or explicit error) when an upstream service is unavailable?

Severity: **High** if a synchronous call has no timeout — one slow upstream can cascade to a full system outage. **Medium** if a timeout exists but no backoff or fallback is defined.

---

**Distributed tracing**

The `trace_id` generated at the entry service must be forwarded in every outbound call so the full request graph can be reconstructed from logs.

Check:
- Is `trace_id` included in every outbound HTTP header (e.g., `X-Trace-Id` or `traceparent`)?
- Does each downstream service extract the incoming `trace_id` and include it in all log entries for that request?
- Is `trace_id` forwarded in inter-service event messages (Kafka, SQS, etc.)?

Severity: **Medium** if `trace_id` is not propagated to outbound calls (cross-service debugging requires manual correlation). **High** if no `trace_id` is generated at the entry service (zero traceability across the system).

---

### AI / LLM App

**Prompt injection guard**

User-controlled input embedded in a prompt must be structurally isolated (delimiters, JSON encoding, separate message role) from the system instructions. Unguarded input lets a user override the system prompt or inject instructions that alter the model's behavior.

Check:
- Does every prompt template clearly separate system instructions from user-supplied content (e.g., separate `system` / `user` message roles, explicit delimiters)?
- Is user input passed through sanitization or structural isolation before being embedded?
- Are there code paths where raw user input can reach the system prompt section?

Severity: **High** if user input can reach the system prompt section without structural isolation — prompt injection can bypass content policies and exfiltrate data.

---

**LLM output validation before downstream use**

Code that acts on LLM output (DB writes, API calls, file writes, tool invocations) must parse and validate the output structure before use. Blindly passing LLM output downstream is a reliability and security risk.

Check:
- Is there a parsing / validation step between the LLM response and any downstream action?
- If the expected output is structured (JSON, YAML), is parse failure handled explicitly — not just a bare `json.loads()` / `JSON.parse()` with no error handling?
- Can a malformed or unexpected LLM response cause an unhandled exception or silent data corruption?

Severity: **High** if LLM output reaches a DB write or code execution path without validation. **Medium** if structured output is parsed without error handling (silent failures on malformed responses).

---

**Eval coverage for prompt changes**

Every prompt added or modified in this sprint must have a corresponding test case in `eval-spec.md`. Prompt changes without eval coverage make regressions invisible until production.

Check:
- For each prompt added or modified this sprint: does `eval-spec.md` have at least one test case that exercises the new or changed behavior?
- Does `eval-log.md` contain an entry from a run after the change was made?

Severity: **Medium** if a modified prompt has no covering test case in `eval-spec.md`. **High** if a prompt was changed with no eval run performed after the change.

---

### IaC / DevOps

**No credentials in code or config**

No API keys, passwords, tokens, or account numbers may appear in `.tf` files, Helm values, YAML config, or CI pipeline definitions. All secrets must be resolved from a secrets manager at apply time.

Check:
- Do any `.tf`, `.yaml`, or values files contain string literals in `password`, `secret`, `token`, or `key` fields?
- Are sensitive variables passed via `var.xxx` referencing a secrets manager data source, rather than hardcoded in `terraform.tfvars` or CI env vars?
- Does `git log` for this sprint contain any diff that added a secret literal (even if since removed)?

Severity: **High** — hardcoded credentials are a critical security finding regardless of repository visibility or whether the value appears to be a placeholder.

---

**Destroy protection on critical resources**

Resources that cannot be recovered from backup (state buckets, primary databases, identity providers) must have `prevent_destroy = true` in their lifecycle block, or equivalent protection in the cloud provider.

Check:
- Do storage resources holding Terraform state or backups have `prevent_destroy = true`?
- Do primary database resources have `prevent_destroy = true`?
- Is there a documented justification in `topology.md` for any critical resource that intentionally omits this protection?

Severity: **High** if a critical resource lacks destroy protection — a `terraform destroy` or mistaken plan run could permanently delete non-recoverable data.

---

**Drift detection coverage**

Every resource in the inventory (`topology.md`) must be covered by the drift detection mechanism documented in `drift-policy.md`. Resources outside detection scope can silently diverge from declared state.

Check:
- Is each resource type in `topology.md` included in the drift detection scope?
- Are exempt resources listed in `drift-policy.md → Exempt Resources` with a justification?
- Does the detection cadence in `drift-policy.md` match what the CI/CD job or scheduled run actually executes?

Severity: **Medium** if a resource is in the inventory but not in the detection scope. **High** if a new resource was added this sprint and drift detection coverage was not updated to include it.

---

### Mobile App

**Permission declaration completeness**

Every OS permission used in code must be declared in the manifest (`AndroidManifest.xml` / `Info.plist`) and documented in `mobile-contract.md`. An undeclared permission crashes the app at runtime; an undocumented one causes App Store rejection.

Check:
- For each API call that requires a permission (camera, location, notifications, contacts, etc.): is the permission declared in the manifest?
- Is each declared permission listed in `mobile-contract.md → OS Permission Declarations` with its purpose string?
- Are there manifest declarations with no matching code path (orphan declarations)?

Severity: **High** if a used permission is not declared in the manifest — runtime crash on the first use. **Medium** if a used permission is declared in code but not documented in `mobile-contract.md`.

---

**Navigation graph conformance**

Every screen reachable via app navigation must be listed in `mobile-contract.md`. Screens absent from the contract are either undocumented (documentation gap) or unreachable (dead code).

Check:
- Does the navigation stack or router include any screens not listed in `mobile-contract.md → Screen Inventory`?
- Are there screens in `mobile-contract.md` with no corresponding component or view in the codebase (stale entries)?
- Do all deep-link routes listed in `mobile-contract.md` have a matching route handler in code?

Severity: **Medium** if a reachable screen is absent from `mobile-contract.md`. **High** if a deep-link route in `mobile-contract.md` has no handler in code — navigation crash on activation.

---

**Deep link parameter validation**

Deep link parameters are user-controlled input (URL query strings, path segments). They must be validated before use in API calls, DB queries, or navigation decisions.

Check:
- Are deep link parameters validated (type-checked, range-checked, or allow-listed) before being passed to an API call or navigation action?
- Can a crafted deep link URL cause an unhandled exception, navigate to an unexpected screen, or reach a network call with unvalidated input?

Severity: **High** if deep link parameters reach an API call or data operation without validation. **Medium** if validation exists but is incomplete (e.g., no length limit on a string field used in a downstream query).

---

# Rules During Fixes

Follow AGENTS.md principles:

- Package First
- Incremental changes only
- No unrelated refactoring
- No large architectural rewrites

Only modify files directly related to the finding.

Do NOT:

- Rename unrelated modules
- Reorganize folders
- Reformat unrelated files
- Rewrite working code

---

# After the Report

## High Severity

Fix High findings one at a time.

After each fix output:

Fixed:
- <summary>

Files:
- file1
- file2

Reason:
- why this resolves the finding

Continue until no High findings remain.

Only then continue to Step 2.

**Independent review gate — full-review case only** (triggered per the note at the top of
this file: inherited/unreviewed code). The same session that wrote the fix cannot also be
the one that declares it resolved — that is the reviewer grading its own fix. Before
checking a High finding off in this case, do one of:
1. Show the user the diff for this specific finding and get their explicit confirmation, or
2. Have a separate session or `/code-review` pass look at just this fix and confirm it
   independently.
Do not mark "no High findings remain" on self-judgment alone when this gate applies. This
does not apply to the lightweight Checkpoint A path (items 1-4) — only to a full review of
code with no existing ownership/review record.

---

## Medium / Low

Append each finding to the END of the current sprint in:

docs/project-plan.md

Format:

- [ ] [CODE QUALITY] [Area]: Recommendation

Examples:

- [ ] [CODE QUALITY] Schema: Add index on orders.status for frequent filtering
- [ ] [CODE QUALITY] Naming: Standardize repository method names
- [ ] [CODE QUALITY] Security: Replace custom JWT verification with framework middleware

Do NOT:

- Reorder existing tasks
- Rewrite completed tasks
- Modify future sprints

Append only.

---

# Success Criteria

The review is complete only when:

- No High severity findings remain.
- Every finding includes evidence.
- No speculative findings exist.
- Medium/Low findings are appended to the current sprint. Nits are not — they're visibility only.
- Documentation has not started before High findings are resolved.
- Only files related to confirmed findings have been modified.
