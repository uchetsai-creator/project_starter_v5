# Proposing the Breakdown and Approach

Referenced from `AGENTS.md → New requirement from the user` and `learning-checkpoints/common.md`
(Checkpoint A item 2, Checkpoint B item 2). Load it when a task starts from a new requirement, or
when a change spans more than one file/layer or has more than one reasonable implementation.

## Why this is a separate step

Clarifying questions settle **what** is being built (scope, edge cases, acceptance criteria).
This step is a second conversation about **how it is split and implemented**. Skipping it means
the agent decides the breakdown and the approach alone — the user only finds out when the code
already exists, and two stakeholders who wanted different behaviour only find out after one
interpretation has been built.

## What to write in `docs/current-state.md → Approach`

Fill it in before writing any code, then show it to the user:

- **Breakdown** — the tasks in order, each within the size rules in `templates/project-plan.md`
  (one-sentence intent, ≤5 steps, ≤3-4 files, independently verifiable), with `[P]` where a task
  has no pending dependency
- **Approach** — how it will be implemented and why; name the design pattern if one fits
- **Alternatives considered** — at least one, with the trade-off, wherever there is a real choice
- **Risks / unknowns** — what to try first (a spike) before committing to the plan
- **Out of scope** — what this task deliberately does not do

## Who to discuss what with

- **Breakdown and order** decide what ships first and what gets cut — agree them with whoever
  owns the requirement.
- **Technical approach** is discussed with the people who will build and maintain it. The
  requester only needs the trade-offs that change time, risk, or cost.
- **Two stakeholders who want different behaviour** — settle it here, before implementation.

## Propose, don't decide

The user may split it differently, reorder it, choose another option, or cut scope. Wait for a
reply; silence is not confirmation. When the user confirms (with or without changes), update the
Approach section to match what was agreed, then set `Approach Confirmed` to `Y`.

## When `N/A` is allowed

Set `Approach Confirmed: N/A — <reason>` only for:

- a single obvious change (one file, no real design choice), or
- a task whose breakdown and approach were already confirmed while `docs/project-plan.md` was
  written.

When in doubt, propose — a false-positive costs one short message; a skipped one means building on
an unchecked assumption.

## What is enforced

`adapters/claude/pretooluse_scope_guard.py` and `.githooks/pre-commit` block source changes while a
real Current Task's `Approach Confirmed` is unfilled or not `Y` / `N/A`. This applies only when
`current-state.md` has the field, so files that predate it keep working; the template always has it.
Like `Clarifying Questions Asked`, the check confirms the field was filled — it cannot tell whether
the conversation really happened.
