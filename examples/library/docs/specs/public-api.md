# Public API

## Functions

### `diff(source: JSONValue, target: JSONValue) -> list[Operation]`

Compute a minimal RFC 6902 patch that transforms `source` into `target`.

**Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `source` | `JSONValue` | Yes | Original document (dict, list, or scalar) |
| `target` | `JSONValue` | Yes | Desired end state of the document |

**Returns:** `list[Operation]` — an ordered list of patch operations. Empty list if
`source == target`.

**Example:**
```python
patch = diff({"name": "Ada"}, {"name": "Ada", "active": True})
# [{"op": "add", "path": "/active", "value": True}]
```

---

### `apply_patch(document: JSONValue, patch: list[Operation]) -> JSONValue`

Apply a patch to `document` and return the resulting document. `document` is never
mutated in place.

**Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `document` | `JSONValue` | Yes | Document to patch |
| `patch` | `list[Operation]` | Yes | Patch operations, as produced by `diff()` or hand-written |

**Returns:** `JSONValue` — the patched document (a new object).

**Raises:**

| Exception | When |
|---|---|
| `PatchValidationError` | The patch itself is malformed (bad `op`, missing required field) |
| `PatchApplyError` | A `path`/`from` reference does not exist in `document` |
| `PatchTestFailed` | A `test` operation's expected value does not match |

**Example:**
```python
result = apply_patch({"name": "Ada"}, [{"op": "add", "path": "/active", "value": True}])
# {"name": "Ada", "active": True}
```

---

## Classes

### `class Patch`

Wraps a list of raw operation dicts and validates them against RFC 6902 syntax.

**Constructor:**
```python
patch = Patch(operations: list[dict])
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `operations` | `list[dict]` | Yes | Raw operation dicts, e.g. from `json.loads(patch_json)` |

**Public methods:**

| Method | Returns | Description |
|---|---|---|
| `validate()` | `None` | Raises `PatchValidationError` if any operation is malformed |
| `apply(document)` | `JSONValue` | Equivalent to `apply_patch(document, self.operations)` |

**Example:**
```python
patch = Patch([{"op": "remove", "path": "/active"}])
patch.validate()
result = patch.apply({"name": "Ada", "active": True})
```

---

## Types and Enums

```python
class OpType(str, Enum):
    ADD = "add"
    REMOVE = "remove"
    REPLACE = "replace"
    MOVE = "move"
    COPY = "copy"
    TEST = "test"
```

`Operation = dict[str, object]` — a single patch operation, e.g.
`{"op": "replace", "path": "/name", "value": "Grace"}`.

`JSONValue = dict | list | str | int | float | bool | None` — any JSON-compatible value.

---

## Exceptions

| Name | Base class | Raised when |
|---|---|---|
| `PatchValidationError` | `ValueError` | Patch document violates RFC 6902 syntax |
| `PatchApplyError` | `LookupError` | A `path`/`from` JSON Pointer does not resolve in the document |
| `PatchTestFailed` | `AssertionError` | A `test` operation's value does not match |

---

## What is NOT public

- `jsonpatch_lite._pointer` (internal JSON Pointer resolution)
- `jsonpatch_lite._diff_impl` (internal diff algorithm)
- Any symbol beginning with `_`

---

## Deprecation Log

No public symbols have been deprecated yet.

---

## Non-Functional Requirements

| Metric | Requirement |
|---|---|
| Import time | < 50ms — no I/O or heavy computation at import |
| `diff()` latency | < 200ms for two 10,000-key dicts |
| Thread safety | All public functions are thread-safe (no shared mutable state) |
| Supported Python versions | 3.10, 3.11, 3.12, 3.13 |

---

## Edge Cases

| Scenario | Expected behaviour |
|---|---|
| `diff(a, a)` on identical objects | Returns `[]` |
| `apply_patch(doc, [])` | Returns a deep copy of `doc`, unchanged |
| `move` operation with a `from` path that does not exist | Raises `PatchApplyError` |
| Operation dict missing the `op` key | Raises `PatchValidationError` at `Patch.validate()` time |
| `test` operation whose value does not match | Raises `PatchTestFailed`; document left unmodified |
