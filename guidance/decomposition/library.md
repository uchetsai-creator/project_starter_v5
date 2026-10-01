# Decomposition — Library / SDK

Nouns for `guidance/decomposition/common.md`.

- **Observer:** a developer calling the library's public API
- **Entry point:** a public function, class, or method exported from the package
- **Independent Test:** import the package as a consumer would and call the public API —
  never reach into private modules

## Artifact kinds

| Kind | Prefix | In a library | First failing check |
|---|---|---|---|
| Contract | `CONTRACT` | Public signature, types, documented exceptions in `public-api.md` | Type check / test that the symbol exists with the signature |
| State | `STATE` | Usually none — only for libraries that persist (caches, on-disk formats) | Round-trip test of the persisted format |
| Logic | `LOGIC` | Internal implementation | Unit test through the public function |
| Entry | `ENTRY` | Export from the package root, version bump, deprecation shim | Import test: `from pkg import thing` works |
| Guard | `GUARD` | Input validation, documented exceptions, compatibility across supported versions | Test: bad input raises the documented exception type |

A change to a public signature is a Contract task on its own, so the compatibility impact
(`compatibility-matrix.md`, release notes) is reviewed separately from the implementation.

## Typical Guard cases

- Invalid argument → the documented exception type, not a generic error
- Unsupported runtime / dependency version → clear error at import or call time
- Deprecated API still works and emits a deprecation warning

## Example slice

```
SL-1 (P1)  parse() raises ParseError on malformed input
  Independent Test: from pkg import parse, ParseError; parse("bad") raises ParseError
  Task CONTRACT [SL-1] ParseError in the public API               Covers: FR-004
  Task LOGIC    [SL-1] parser detects malformed input             Covers: FR-004, AC-006
  Task ENTRY    [SL-1] export ParseError from package root        Covers: AC-006
```
