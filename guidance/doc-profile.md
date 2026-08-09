# Document Profile — lite vs. full

`doc_profile` in `.project-starter.yml` is `full` by default. `lite` is for a solo
developer or a small project with no real stakeholders yet, where the full Required-doc
set is friction without a payoff — not a permanently smaller framework, a starting point.

## What actually changes

`lite` downgrades exactly these documents from Required to Optional, for whichever
project type(s) declared. Nothing else changes — same registry, same templates, same
validators, same pre-commit gate:

- `specs/permissions.md`
- `business/business-process.md`, `business/business-objects.md`, `business/business-rules.md`
- `architecture/backend.md`, `architecture/database.md`, `architecture/deployment.md`
- `specs/research.md`
- `specs/test-plan.md`, `specs/test-report.md`

Everything else — `project-requirements.md`, `quickstart.md`, `data-model.md`,
`api-contract.md`, `architecture/architecture.md`, `logging-spec.md` — stays Required in
both profiles. These are the documents the spec↔code drift gate and the context builder
actually depend on; downgrading them would cut the framework's real value, not just its
paperwork.

See `document-registry.yaml`'s `lite_downgrade` field for the authoritative list — this
file explains the *why*, that one is the source of truth for *what*.

## Why lite is not a different document set

A downgraded document is Optional, not deleted from the type's matrix and not replaced by
something else. Switching `doc_profile` back to `full` re-requires exactly the same
documents `lite` deferred — there is no migration, no rewrite, no second template set to
maintain. Growing from lite to full is "go fill in what you skipped," structurally
guaranteed by both profiles reading the same registry.

## When to switch to full

Not a fixed schedule — switch when one of these becomes true, whichever comes first:

- **A second contributor joins.** `business-process.md` and `business-rules.md` exist so
  someone who didn't write the code can understand what it's supposed to do.
- **The project gets a real permission/role model** (more than "the one person running
  this"). Write `permissions.md` before you write the code that checks roles, not after.
- **A real approval, audit, or compliance requirement appears.** `business-rules.md` is
  where that gets recorded, with an explicit enforcement layer per rule.
- **You're about to deploy somewhere reachable by more than localhost.**
  `architecture/deployment.md` should exist before that, not be reconstructed after an
  incident.
- **You need to explain a technology decision to someone else**, or to your future self
  more than a few weeks out — that's what `research.md` is for.

When any of these happens: set `doc_profile: full`, then treat the newly-Required
documents the same as any other missing-Required document — write them before the next
commit that touches related code, same as `.githooks/pre-commit` would demand for a
`full`-profile project from day one.

## What lite does not relax

- The mechanical guards (`pretooluse_scope_guard.py`, the Unscoped source-change guard,
  Clarifying Questions Asked) are unaffected — "ask before implementing" applies at every
  scale, lite or full.
- Learning Checkpoints (see `guidance/learning-checkpoints/common.md`) still run every
  task, regardless of `doc_profile`.
- Core contract documents (see the list above) are never downgraded — lite reduces
  paperwork, not the parts of the framework that actually catch spec↔code drift.
