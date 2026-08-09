# Test Plan

## Testing Strategy

We use a layered testing approach with unit tests and property-based tests, run entirely
in-process since the library performs no I/O.
Unit tests validate `diff()`, `apply_patch()`, and `Patch.validate()` against a fixed set
of RFC 6902 example documents drawn from the spec's own appendix.
Property-based tests (via Hypothesis) generate random JSON-compatible documents and assert
the round-trip invariant: `apply_patch(a, diff(a, b)) == b` for arbitrary `a` and `b`.

## Test Scope

- Unit: each of the six operation types (`add`, `remove`, `replace`, `move`, `copy`, `test`),
  applied individually and in combination
- Unit: exception paths — malformed patch, missing path, failed `test` operation
- Property: round-trip diff/apply invariant across randomly generated nested structures
