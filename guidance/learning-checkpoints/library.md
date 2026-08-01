# Learning Checkpoints — Library / SDK

Substitute these nouns into `learning-checkpoints-common.md`'s Checkpoint A / B steps.

**Checkpoint A (existing code) — ask about:**
- Which public function/class owns this behavior, and its stability tier
- What breaks for callers if this signature changes (compatibility impact)

**Checkpoint B (new requirement) — ask about:**
- New public function/class shape: params, return type, deprecation plan for anything replaced
- Whether this belongs in the public API surface or stays internal

**Common unfamiliar-tech hotspots for this type** (candidates for Checkpoint 0):
- Packaging/publish tooling for the target registry (PyPI, npm, etc.)
- Type-stub or generic/typing patterns if new to you
