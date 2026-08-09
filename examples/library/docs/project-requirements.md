# Project Requirements

## Goals

* Give Python developers a small, dependency-free library for computing and applying
  JSON Patch (RFC 6902) documents.
* Make diffing two JSON-compatible objects and applying the resulting patch a two-function
  workflow with predictable, deterministic output.

---

## Scope

### In Scope
* Computing a patch (list of operations) between two JSON-compatible Python objects
* Applying a patch to a document and returning the patched result
* Validating a patch document against RFC 6902 syntax before applying it
* The six standard operations: `add`, `remove`, `replace`, `move`, `copy`, `test`

### Out of Scope
* JSON Merge Patch (RFC 7396) — a different, simpler patch format
* Network transport or HTTP endpoints for exchanging patches
* Schema validation of the underlying documents (JSON Schema)

---

## Roles

| Role | Description |
|---|---|
| Library consumer | Python developer importing `jsonpatch_lite` into their application |
| Maintainer | Reviews PRs, cuts releases, triages compatibility issues |

---

## Functional Requirements

* **FR-001**: The library must compute a minimal RFC 6902 patch between two JSON-compatible
  Python objects (dict, list, str, int, float, bool, None).
* **FR-002**: The library must apply a patch to a document and return a new patched object
  without mutating the original.
* **FR-003**: The library must validate that every operation in a patch has the required
  fields for its `op` type (e.g. `move` requires `from` and `path`).
* **FR-004**: The library must support the `test` operation, aborting the whole patch
  application if any `test` operation's value does not match.
* **FR-005**: The library must raise a distinct exception type for a malformed patch
  document versus a patch that fails to apply to a given target document.

---

## Non-Functional Requirements

* **Performance**: Diffing two 10,000-key dicts completes in under 200ms on a typical
  developer laptop.
* **Compatibility**: Pure Python, zero required runtime dependencies.
* **Portability**: Works identically on CPython 3.10–3.13 on Linux, macOS, and Windows.
* **API stability**: Public functions and classes follow the deprecation policy in
  `release-guide.md` before removal.

---

## Edge Cases

### Empty and missing input
* Diffing two identical documents returns an empty patch (`[]`).
* Applying an empty patch (`[]`) to a document returns the document unchanged.

### Permission boundaries
* Not applicable — this is a pure in-process library with no auth boundary.

### Concurrency and race conditions
* `apply_patch()` never mutates its input document, so concurrent callers applying
  different patches to the same source object cannot interfere with each other.

### External dependency failures
* Not applicable — the library performs no I/O.

### State machine violations
* Applying a `move` operation whose `from` path does not exist raises `PatchApplyError`
  before any part of the document is modified.

### Data contract violations
* A patch document containing an operation with an unknown `op` value (not one of the six
  standard operations) raises `PatchValidationError` at validation time, before apply.

---

## Acceptance Criteria

* **AC-001**: Given two JSON-compatible objects `a` and `b`, when `diff(a, b)` is called,
  then applying the returned patch to `a` via `apply_patch(a, patch)` produces a result
  deeply equal to `b`.
* **AC-002**: Given a patch containing a `test` operation whose expected value does not
  match the document, when `apply_patch()` is called, then it raises `PatchTestFailed`
  and the document is not modified.
* **AC-003**: Given a syntactically invalid patch (missing a required field for its `op`),
  when `Patch.validate()` is called, then it raises `PatchValidationError` naming the
  offending operation index.

---

## Assumptions

* Callers pass in already-decoded Python objects (the result of `json.loads`), not raw
  JSON strings — encoding/decoding is the caller's responsibility.
* Dict key order is not treated as semantically significant when diffing.
