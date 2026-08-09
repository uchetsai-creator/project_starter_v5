# Research

## Technology Decisions

Decision: Implement diffing with a custom recursive tree-walk instead of adopting an
existing diff algorithm library.
Rationale: RFC 6902 output must use JSON Pointer paths and the six standard ops; a
generic diff library (e.g. tree-based Myers diff) would need a translation layer that
adds complexity without reducing code size, since the pointer-path walk is already the
simplest correct implementation for nested dict/list structures.

Decision: Ship as a pure-Python package with zero required runtime dependencies.
Rationale: The target audience embeds this library in services with strict dependency
pinning; a zero-dependency package avoids version-conflict resistance in downstream
`requirements.txt` files and keeps install size under 20KB.

Decision: Raise typed exceptions (`PatchValidationError`, `PatchApplyError`,
`PatchTestFailed`) instead of a single generic `PatchError`.
Rationale: Callers need to distinguish "the patch document itself is malformed" from
"the patch is well-formed but doesn't apply to this document" from "a conditional test
op failed" — these require different recovery strategies (reject vs. retry vs. skip).

## Resolved Clarifications

Q: Should `diff()` detect array element moves (e.g. reordering a list) as `move`
operations, or always emit `remove` + `add` pairs?
A: Always emit `remove` + `add` for v1. Detecting moves inside arrays requires an LCS-style
algorithm that adds real complexity for a rare case; revisit if profiling shows patches are
unacceptably large for real workloads.
