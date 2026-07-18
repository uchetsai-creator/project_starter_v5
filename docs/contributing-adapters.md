# Contributing a Framework Adapter

`verify_spec_code.py` catches spec–code drift through **adapters** — one per framework. Each adapter translates both the spec document and the source code into the same `NormalizedForm` objects, which the core validator then compares. The core is zero-knowledge about any framework; all framework-specific logic lives in the adapter.

This guide shows you how to add an adapter for a framework that isn't covered yet.

---

## Step 1 — Choose your NormalizedForm type

Pick the `NormalizedForm` subclass that matches what your framework exposes:

| Project type | NormalizedForm | Used by |
|---|---|---|
| Web App / Microservices | `NormalizedEndpoint` | FastAPI, Flask, Express |
| Data Pipeline / ML Pipeline | `NormalizedStageContract` | Airflow, Dagster, Prefect |
| CLI Tool | `NormalizedCommand` | Click |
| Library / SDK | `NormalizedFunction` | Python library |
| AI / LLM App | `NormalizedTool` | Tool schema |
| IaC / DevOps | `NormalizedResource` | Terraform, Pulumi |
| Mobile App | `NormalizedScreen` | React Native, Flutter |

All types are defined in `_spec_code_adapters/_base.py`.

---

## Step 2 — Create the adapter file

Create `templates/script/validators/_spec_code_adapters/<framework>.py`.

```python
from __future__ import annotations
from _base import FrameworkAdapter, NormalizedFunction, NormalizedField

class MyFrameworkAdapter(FrameworkAdapter):

    def extract_spec(self, spec_path: str) -> list[NormalizedFunction]:
        # Parse your spec format, return NormalizedFunction list.
        # Return [] on any error — never raise.
        ...

    def extract_code(self, src_path: str) -> list[NormalizedFunction]:
        # Walk src_path, parse source files, return NormalizedFunction list.
        # Return [] on any error — never raise.
        ...
```

Rules:
- **No comparison logic** in the adapter. Comparison lives in `verify_spec_code.py`.
- **No framework imports at module level**. Import lazily inside methods to avoid hard dependencies.
- Both methods must **return `[]` (not raise)** on any error condition.
- See `_example_adapter.py` for a fully annotated reference implementation.

### Spec format convention

Define a Markdown section format for your adapter's spec document and document it in the adapter's class docstring. Follow the pattern used by existing adapters:

```markdown
### item_name
#### <ContractSection>
| Field | Type | Description |
|---|---|---|
| field1 | str | ... |
```

---

## Step 3 — Register the adapter

Open `templates/script/validators/verify_spec_code.py` and add one line to `ADAPTER_REGISTRY`:

```python
ADAPTER_REGISTRY: dict[str, tuple[str, str]] = {
    ...
    'my_framework': ('my_framework', 'MyFrameworkAdapter'),  # add this
}
```

The key is the value users pass to `--adapter`. The tuple is `(module_filename_without_.py, ClassName)`.

---

## Step 4 — Write a unit test

Add a self-contained test. The simplest approach is an `if __name__ == '__main__':` block in your adapter file that creates temporary files and asserts round-trip correctness — see `_example_adapter.py` for the pattern.

```bash
python3 templates/script/validators/_spec_code_adapters/my_framework.py
# Should print: ✅  my_framework.py self-test passed
```

---

## Step 5 — Add pre-commit trigger (optional)

If your adapter has a canonical spec filename (e.g. `my-contract.md`), add a trigger to `.githooks/pre-commit` so drift is caught automatically when that file is staged:

```bash
# In .githooks/pre-commit, extend SPEC_CONTRACT_STAGED:
SPEC_CONTRACT_STAGED=$(printf '%s\n' "$STAGED" \
    | grep -E '(pipeline-contract|cli-contract|api-contract|public-api|my-contract)\.md$' || true)
```

---

## Step 6 — Update workflow-registry.yaml (optional)

If your framework is commonly used in a specific task type, add `verify_spec_code.py` to that workflow's validator sequence in `workflow-registry.yaml`.

---

## Step 7 — Open a pull request

1. Include your adapter file and any pre-commit / registry changes.
2. Confirm `python3 templates/script/framework/verify_framework.py --strict` passes.
3. Show sample output: spec-in-sync case (exit 0) and mismatch case (exit 1).

---

## Adapter checklist

- [ ] Inherits from `FrameworkAdapter` in `_base.py`
- [ ] Both methods return `[]` (not raise) on errors
- [ ] No framework imports at module level
- [ ] Class docstring explains spec format with an example
- [ ] Registered in `ADAPTER_REGISTRY` in `verify_spec_code.py`
- [ ] Self-test passes (`python3 _spec_code_adapters/<framework>.py`)
- [ ] README adapter table updated
