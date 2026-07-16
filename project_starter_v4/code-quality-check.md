# Code Quality Check

Used during the "Retrofitting an Existing Project" workflow (see AGENTS.md).

Run this immediately after Step 1 (Read Codebase) and before Step 2 (Documentation).

Do not begin writing documentation until all High severity issues have been resolved.

---

# Required Context

Read ONLY the following documentation before inspecting code:

- current-state.md
- docs/architecture/*
- docs/business/*
- docs/data-model.md
- docs/permissions.md
- docs/project-plan.md

Then inspect ONLY:

1. Application entry point
2. Data layer
3. One complete vertical slice

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

Possible areas:

- Layering
- Package First
- Naming
- Schema
- Security
- Error Handling
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

# Area-Specific Rules

## Layering

Check that each layer contains only what belongs to it.
The layer names and rules depend on the project type — use the row that matches:

| Project type | Entry layer rule | Middle layer rule | Data / output layer rule |
|---|---|---|---|
| **Web App / Microservices** | Controller: HTTP binding only (parse request, return response) | Service: business logic only | Repository: DB queries only — no business logic |
| **CLI Tool** | Command parser: flag/arg parsing only | Handler / UseCase: command logic | Store / Writer: file I/O or config persistence only |
| **Library / SDK** | Public API function: input validation + delegation only | Internal implementation | No persistence layer — outputs are return values |
| **Data Pipeline** | Stage entry: input contract validation only | Transform / Enrich: data logic | Writer / Sink: output contract only — no data logic |
| **ML Pipeline** | Stage entry: schema + quality checks | Model / Transform: inference or feature logic | Artifact writer: serialisation only |
| **Microservices** | Per-service: same as Web App | — | — |
| **AI / LLM App** | Request handler: prompt assembly only | LLM caller: API call + retry logic | Response parser: output extraction only |

Business logic in the entry layer is always a finding, regardless of project type.

---

## Package First

Before recommending custom code:

Check whether an existing dependency already solves the problem.

If duplicate custom implementation exists:

Report it.

Do not recommend rewriting unless necessary.

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

## Permission Consistency

Read every:

business/*-process.md

Collect every:

(Role, Action)

Cross-reference:

permissions.md

API Endpoint Access table.

Evaluate Source:

Hardcoded
→ High

Seeded default
→ Medium

Missing Source column
→ High

Recommendation:

Grant access

or

Document why another workflow is used.

---

## State Machine Consistency

Canonical source:

business/*-object.md

Compare with:

data-model.md

If transitions differ:

High severity.

business object documentation is always the source of truth.

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
| **AI / LLM App** | Prompt variable name ↔ value injected at runtime ↔ expected output format in eval rubric |

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

# Sprint Completion

When the current sprint is completed:

1. Review remaining incomplete tasks.
2. Check whether completed work affects future tasks.
3. Update affected task descriptions if necessary.
4. Do not silently delete tasks.
5. Preserve sprint history.

---

# Success Criteria

The review is complete only when:

- No High severity findings remain.
- Every finding includes evidence.
- No speculative findings exist.
- Medium/Low findings are appended to the current sprint.
- Documentation has not started before High findings are resolved.
- Only files related to confirmed findings have been modified.
