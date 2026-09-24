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
- **Impact lines** — for each task, everything it changes besides code, so the user sees the full cost of
  the split before agreeing to it. Five lines in `current-state.md → Approach`, all filled with the user:
  1. **Docs to update** — which spec documents change and why.
     - Candidates: `python3 build-context.py --task-type sprint-end`. That is every document that applies
       to this project type, **not** filtered by the current task's type. The default `.ai/AI_CONTEXT.md`
       is filtered by the *current* task's type, but a requirement spans several tasks of different
       types (a schema task, an API task, a UI task) — filtering by one of them hides docs the others need.
     - Compare the approach with each candidate's `update_trigger` in `document-registry.yaml` (e.g.
       architecture: "system components or data-flow changes") and say whether it is hit. Also name the
       candidates you consider NOT affected and why — the user decides; you never silently drop one.
     - A document that does not exist yet but should (e.g. `permissions.md` when roles are added) is
       listed as "create", not skipped because the candidate list only shows what exists.
     - `project-requirements.md` is always on the list (the Clarifications answers are written back —
       see `clarifying-checklist.md`). Note which task updates which doc.
  2. **Tests to add/update** — which tests each task adds or changes and which `AC-`/`FR-` id each
     covers (or `N/A — user: <reason>`, e.g. a docs-only change; the agent may not write that itself).
     `verify_acceptance.py` only checks that the test plan *lists* an id, so this is where the real tests
     are named. Test code is not a registered document, so it would otherwise never come up.
  3. **Dependencies** — packages added, removed or upgraded, the manifest / lockfile touched, and
     `docs/specs/dependencies.md`; or `none`.
  4. **Config / CI / deploy** — env vars, config files, migrations, CI workflow, Docker/deploy files
     touched; or `none`. These are code-adjacent files no document registry lists.
  5. **Per-module docs** — modules that need a new or changed flow file and log file, index tables
     (`business-objects`, `business-process`, `prompt-library`) to update, README file trees when files
     are added or removed; or `none`. `verify_module_docs.py` and `verify_index_coverage.py` catch these
     only at Sprint Documentation Sync; naming them up front avoids finding out later.
- **Out of scope** — what this task deliberately does not do

Wait for the user's reply again. Update the section to match what was agreed — including the impact
lines; the agreed `Docs to update` is what you write into `Doc Checklist` when the task is set up, and
the tests / dependencies / config / per-module items become steps of the relevant task.

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

## Requirement status and the push gate

A requirement is one Clarifications → Approach → Breakdown cycle. `current-state.md → Requirement Status`
stays `In Progress` while any task in the Breakdown is open; set `Complete` (and fill `Requirement IDs`)
when the last one is done. Commits are not blocked either way. `.githooks/pre-push` blocks a push to
`main`/`master` (configurable: `push_gate_branches`) unless the requirement is `Complete` and
`verify_acceptance.py --only <Requirement IDs>` passes, or the user marked it `Descoped — user: <reason>`.
Other branches only get a warning.

## What is enforced

`adapters/claude/pretooluse_scope_guard.py` and `.githooks/pre-commit` block source changes while a
real Current Task's `Approach Confirmed` is unfilled or not `Y`. The checks apply when
`current-state.md` has the field; the template always includes it, so new projects are checked from
the first task. The same hooks also block while an impact line that exists is empty or still the placeholder,
while `Docs to update` does not name `project-requirements.md`, and while `Tests to add/update` names no
`AC-`/`FR-` id and is not `N/A — user: <reason>`. Only lines that exist are checked (older files are not
covered). This checks the lines were written, not that the user agreed to them. A `current-state.md` that predates the field must add it to be covered. Like
`Clarifying Questions Asked`, the check confirms the field was filled — it cannot tell whether the
conversation really happened.
