# Explaining the Approach and Proposing the Breakdown

Referenced from `AGENTS.md → New requirement from the user` and `learning-checkpoints/common.md`
(Checkpoint A item 2, Checkpoint B item 2). **This discussion with the user is mandatory — there
is no N/A.** It applies to every task with a real Current Task: new, small, or already scoped.

## Why this is a separate step

Clarifying questions settle **what** is being built (scope, edge cases, acceptance criteria).
This step is a second conversation about **how it is built and split**. Skipping it means the
agent decides the approach and the breakdown alone — the user only finds out when the code
already exists, and two stakeholders who wanted different behaviour only find out after one
interpretation has been built.

## Two steps, in this order

Both go into `docs/current-state.md → Approach`, and the user replies to each. Propose, don't
decide: the user may choose another option, reorder, split differently, or cut scope. Silence is
not confirmation.

### 1. Explain the approach in plain language

Say how you plan to implement it and why, in terms the user can follow — what will change from
their point of view, why this way, what the alternatives are, and what could go wrong. Avoid
unexplained jargon; if the user cannot follow it, they cannot agree or disagree with it.

- **Approach** — how it will be implemented and why; name the design pattern if one fits
- **Alternatives considered** — at least one, with the trade-off, wherever there is a real choice
- **Risks / unknowns** — what to try first (a spike) before committing to the plan

Wait for the user's reply and adjust before moving on.

### 2. Then propose the breakdown

The breakdown depends on the chosen approach, so it comes second.

- **Breakdown** — the tasks in order, each within the size rules in `templates/project-plan.md`
  (one-sentence intent, ≤5 steps, ≤3-4 files, independently verifiable), with `[P]` where a task
  has no pending dependency
- **Out of scope** — what this task deliberately does not do

Wait for the user's reply again. Update the section to match what was agreed.

## Who to discuss what with

- The approach and the breakdown decide what ships first and what gets cut — agree them with
  whoever owns the requirement.
- Deeper technical detail is discussed with the people who will build and maintain it.
- **Two stakeholders who want different behaviour** — settle it here, before implementation.

## Recording it

When both steps are confirmed, set `Approach Confirmed` to `Y`, optionally followed by what was
agreed. Accepted forms:

- `Y`
- `Y — approach A chosen over B; split into DB / BE / FE`
- `Y — confirmed when project-plan.md was written` (task already discussed at planning time)

`N/A` is **not** accepted. For a small change, the conversation can be one sentence to the user —
but it still happens first.

## What is enforced

`adapters/claude/pretooluse_scope_guard.py` and `.githooks/pre-commit` block source changes while a
real Current Task's `Approach Confirmed` is unfilled or not `Y`. The checks apply when
`current-state.md` has the field; the template always includes it, so new projects are checked from
the first task. A `current-state.md` that predates the field must add it to be covered. Like
`Clarifying Questions Asked`, the check confirms the field was filled — it cannot tell whether the
conversation really happened.
