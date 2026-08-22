---
name: research-decision-log
description: Use whenever the conversation reaches a technology decision — explicit ("let's go with X", "we should use X instead of Y", "record this") or implicit (comparing frameworks/libraries and landing on one, a database schema choice with stated rationale, choosing between architectural patterns, an auth/deployment strategy pick, a NEEDS CLARIFICATION item from project-plan.md getting resolved). Drafts a docs/specs/research.md entry and asks the user before writing it — never write without explicit approval. Do NOT use for the very first task of a brand-new project with no code yet — session-start-hook.sh's own nudge covers that moment; this Skill is for every decision after that.
---

# Research Decision Log

The goal is to catch a technology decision at the moment it's made in conversation — not
at sprint end, when nobody remembers the alternatives that got ruled out. This does not
replace `sprint-doc-sync`'s own research.md checklist item (a periodic safety net for
whatever this Skill missed); it catches most decisions earlier, while the reasoning is
still fresh.

There is no reliable mechanical trigger for "was this conversation a decision" — unlike
`workflow-registry.yaml`'s schema or `spec_code_bindings`' YAML shape, this is a judgment
call, not a structural check a script could make instead. Use the signals below as a
prompt for your own judgment, not a checklist to pattern-match literally.

## Trigger signals

**Explicit** — the user says so directly:
- "Let's go with X"
- "We should use X instead of Y"
- "The trade-off is worth it because..."
- "Record this as a decision" / "log this"

**Implicit** — a decision happened without being announced as one:
- Comparing two or more frameworks/libraries and landing on one
- A database schema or storage choice with a stated reason
- Choosing between architectural patterns (e.g. event-driven vs. request/response)
- Picking an auth/authorization strategy
- Evaluating deployment infrastructure alternatives
- Resolving a `NEEDS CLARIFICATION` item from `docs/project-plan.md`

## What to do when triggered

1. Check whether `docs/specs/research.md` already has a non-placeholder `## [Decision
   Name]` entry for this same decision — if so, this is a revision, not a new entry;
   update the existing one instead of adding a duplicate.
2. Draft the entry using the template's own shape (`templates/specs/research.md`):
   Decision, Rationale (as bullets), Alternatives Considered (table: Option / Pros / Cons
   / Reason rejected), References.
3. Present the draft to the user and ask before writing anything —
   **never write to `docs/specs/research.md` without explicit approval.** If the user
   declines or wants changes, revise or discard; do not write a version they haven't seen.
4. Only after approval: append the entry to `docs/specs/research.md`.

## What this Skill does not do

- Does not run on its own schedule or poll for decisions — it only fires when a decision
  surfaces in the current conversation.
- Does not replace the sprint-end checklist item in `sprint-doc-sync` — that is the
  fallback for whatever this Skill didn't catch, not a duplicate check to skip because
  this Skill exists.
- Does not fire for the brand-new-project moment — `session-start-hook.sh` already nudges
  toward an initial research.md discussion when `docs/current-state.md`'s Task is still a
  placeholder and `docs/specs/research.md` has no real content yet. That is a deterministic,
  file-state-based check; this Skill's own trigger is not — the two are deliberately
  different mechanisms for two different moments, not one mechanism doing both jobs.
