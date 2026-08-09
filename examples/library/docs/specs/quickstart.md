# Quickstart

## Prerequisites

- Python 3.10 or higher
- `pip` 22+

## Setup

1. Install the package: `pip install jsonpatch-lite`
2. In a Python shell, import the two top-level functions:
   ```python
   from jsonpatch_lite import diff, apply_patch
   ```
3. Compute a patch between two documents:
   ```python
   patch = diff({"name": "Ada"}, {"name": "Ada", "active": True})
   ```
4. Apply the patch back to the original document:
   ```python
   result = apply_patch({"name": "Ada"}, patch)
   assert result == {"name": "Ada", "active": True}
   ```

## Verification

Run `python -m pytest --pyargs jsonpatch_lite.tests` to confirm the installed package
passes its own self-check suite, or run the `assert` in step 4 above to verify a basic
diff/apply round-trip works in your environment.
