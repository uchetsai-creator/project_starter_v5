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

Check that:

- Controller contains HTTP logic only
- Service contains business logic
- Repository/Data layer contains persistence logic

Business logic inside controllers is a finding.

---

## Package First

Before recommending custom code:

Check whether an existing dependency already solves the problem.

If duplicate custom implementation exists:

Report it.

Do not recommend rewriting unless necessary.

---

## Naming

Check:

- Module names
- Repository methods
- Service methods
- Endpoint naming

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

## API Endpoint Overlap

Find endpoints operating on the same resource/state.

Example:

PATCH /orders/:id/approve

PATCH /orders/:id/approval

If both change identical state without a documented reason:

Medium severity.

Recommend:

- Merge endpoints

or

- Add a Design Note explaining why both exist.

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
| Web app | Frontend form field ↔ backend validation rule ↔ DB column |
| Data pipeline | File sensor glob ↔ GE data asset name ↔ dbt source ↔ DB schema |
| API service | Request schema ↔ handler validation ↔ DB write |
| CLI tool | Flag name ↔ config key ↔ env var name |

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
