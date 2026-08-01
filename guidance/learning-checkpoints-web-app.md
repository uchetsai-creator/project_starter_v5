# Learning Checkpoints — Web App

Substitute these nouns into `learning-checkpoints-common.md`'s Checkpoint A / B steps.

**Checkpoint A (existing code) — ask about:**
- Which route/page and which layer (controller → service → repository) owns this behavior
- The DB schema and migration path this touches
- The auth/permission check this endpoint relies on

**Checkpoint B (new requirement) — ask about:**
- New endpoint shape: method, path, request/response fields, error codes
- Which existing page/component this plugs into, or if it's a new one

**Common unfamiliar-tech hotspots for this type** (candidates for Checkpoint 0):
- A new frontend framework or state-management pattern
- An ORM you haven't used, or an auth protocol (OAuth, JWT, session-based)
- A new frontend build/bundler toolchain
