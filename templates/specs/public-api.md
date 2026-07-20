# Public API

<!--
  For: Library / SDK projects
  Replaces: api-contract.md (libraries have no HTTP endpoints)
  Purpose: Documents the public-facing interface — functions, classes, types, constants.
           Internal implementation detail is NOT documented here.
  Update when: A public function, class, type, or constant is added, changed, or deprecated.
  Breaking change policy: any change that requires callers to update their code is breaking.
  Semver: breaking → major bump; new public symbol → minor bump; fix → patch bump.
-->

## Public API Summary

**Package name:** `[package-name]`
**Import:**
```python
# Python
from package_name import ClassName, function_name
```
```typescript
// TypeScript / JavaScript
import { ClassName, functionName } from 'package-name'
```

### Stability tiers

| Tier | Meaning |
|---|---|
| **Stable** | Will not change without a major version bump |
| **Beta** | May change in minor versions — caller must pin |
| **Internal** | Not part of public API — do not use directly |

---

## Functions

Repeat this block for each public function.

---

### `functionName(param1, param2)`

**Stability:** Stable / Beta

**Description:** [What it does — one to three sentences]

**Parameters:**

| Name | Type | Required | Description |
|---|---|---|---|
| `param1` | `string` | Yes | [Description] |
| `param2` | `int` | No | [Description. Default: `0`] |

**Returns:** `ReturnType` — [Description of what is returned]

**Raises / Throws:**

| Exception | When |
|---|---|
| `ValueError` | [Condition that triggers this error] |
| `ConnectionError` | [Condition that triggers this error] |

**Example:**
```python
result = function_name("input", param2=5)
```

---

## Classes

Repeat this block for each public class.

---

### `ClassName`

**Stability:** Stable / Beta

**Description:** [What this class represents or does]

**Constructor:**

```python
obj = ClassName(required_param, optional_param=default)
```

| Parameter | Type | Required | Description |
|---|---|---|---|
| `required_param` | `string` | Yes | [Description] |
| `optional_param` | `bool` | No | [Description. Default: `False`] |

**Public methods:**

| Method | Returns | Description |
|---|---|---|
| `method_name(arg)` | `ReturnType` | [What it does] |
| `other_method()` | `None` | [What it does] |

**Example:**
```python
obj = ClassName("value")
result = obj.method_name("arg")
```

---

## Types and Enums

```python
class StatusEnum(Enum):
    PENDING = "pending"
    ACTIVE  = "active"
    DONE    = "done"
```

---

## Constants

| Name | Value | Description |
|---|---|---|
| `DEFAULT_TIMEOUT` | `30` | Default request timeout in seconds |
| `MAX_RETRIES` | `3` | Default retry limit |

---

## What is NOT public

The following are internal implementation details and must not be imported or relied on directly. They may change in any version without notice.

- `_internal_module`
- `_PrivateClass`
- Any symbol beginning with `_`

---

## Deprecation Log

| Symbol | Deprecated in | Removed in | Migration |
|---|---|---|---|
| `old_function()` | v1.2.0 | v2.0.0 | Use `new_function()` instead |

---

## Non-Functional Requirements

| Metric | Requirement |
|---|---|
| Import time | < [e.g., 100ms] — no I/O or heavy computation at import |
| Function call latency | [function_name]: < [e.g., 50ms] for typical input |
| Thread safety | [All public symbols are thread-safe / list exceptions] |
| Memory per call | Peak < [e.g., 50MB] for [typical input size] |
| Supported Python / Node versions | [e.g., Python 3.10+; Node 18+] |

---

## Edge Cases

| Scenario | Expected behaviour |
|---|---|
| `None` / `null` passed for required parameter | Raise `TypeError` with message identifying the parameter |
| Empty string passed for non-nullable string | Raise `ValueError("[param] must not be empty")` |
| Numeric value outside documented range | Raise `ValueError` with allowed range in message |
| Input larger than documented max size | Raise `ValueError` with size limit in message |
| Function called concurrently on shared mutable state | [Thread-safe — internal lock used / Not thread-safe — caller must synchronize] |
| Network unavailable (for I/O functions) | Raise `ConnectionError` — never swallow silently |
| Requested resource not found | Raise `[NotFoundError]("[entity] not found: [id]")` |
| Deprecated function called | Emit `DeprecationWarning` with migration path; still execute |

> *Match your actual exception classes. Callers must be able to distinguish recoverable from unrecoverable errors.*
