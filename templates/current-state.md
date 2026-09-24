# Current State

<!--
  EXECUTION RULES — read before starting any task:
  1. Every blocking command must be wrapped with timeout:
     timeout 120 bash -c '...' && echo "✅ done" || echo "❌ timed out"
  2. If any operation has been running for more than 5 minutes without a clear
     success signal — stop, report what you were doing and the last known output,
     and wait for instruction. Do not keep waiting or trying new things silently.
-->

## Current Task

**Task:** [Task name, e.g., BE Order API]

**Goal:** [What this task needs to achieve]

**Task Type:** [task-type]
<!-- Valid values: feature | pipeline-stage | bug-fix | sprint-end | eval-run | iac-change
     Used by build-context.py to filter .ai/AI_CONTEXT.md to relevant documents.
     Leave as [task-type] placeholder if unknown — script falls back to all Required docs. -->

**Clarifying Questions Asked:** [Y / N/A — reason]
<!-- Y: the user answered every category in "Clarifications" below before implementing
     (AGENTS.md -> New requirement from the user / Learning Checkpoint B). N/A: task was already
     scoped in project-plan.md, or Checkpoint A (existing code) applied instead. Fill this in when Task above stops being a placeholder —
     pre-commit blocks the commit if it's still unfilled at that point. -->

**Approach Confirmed:** [Y — what was agreed]
<!-- Y: BEFORE writing code you (1) explained to the user, in plain language, how you plan to
     implement this and why, and (2) once that was agreed, proposed how to split it into tasks —
     and the user confirmed or adjusted both. Mandatory: there is no N/A, whether the task is
     new, small, or already scoped. A task discussed while project-plan.md was written: write
     "Y — confirmed when project-plan.md was written". A small change: "Y — <what you told the
     user and what they said>". Clarifying questions settle WHAT is being built; this settles
     HOW it is built and split — a separate conversation. Fill this in when Task above stops
     being a placeholder — the PreToolUse scope guard and pre-commit both block source changes
     while it is unfilled. Like Clarifying Questions Asked, this only checks the field was
     filled, not that a real conversation happened. -->

**Requirement IDs:** [FR-/AC- ids this requirement adds to project-requirements.md, e.g. FR-012, AC-012]

**Requirement Status:** [In Progress / Complete / Descoped — user: reason]
<!-- One requirement = one Clarifications -> Approach -> Breakdown cycle (several tasks).
     In Progress: tasks in the Breakdown are still open — commit freely, nothing is verified yet.
     Complete: set when the LAST task in Approach -> Breakdown is done. `git push` to a gated branch
     (main/master by default) then runs verify_acceptance.py --only <Requirement IDs> and blocks
     on failure. Descoped — user: <reason>: the user dropped it (only the user may — the agent may
     not). Not checked at commit time; enforced by .githooks/pre-push. Older files without this
     field are not covered. -->

**Status:** In Progress
<!-- When done: "Complete — Pending Sprint Doc Sync" -->

---

## Clarifications

<!--
  The USER answers every line below — you do not decide which categories matter for this task.
  Walk the user through each category (questions to start from: guidance/clarifying-checklist.md),
  one category at a time, with as many questions as it takes, and record `Q → A` in the user's own
  words. If a category looks less relevant, SAY SO and give your reason, but still ask — only the
  user may skip it, recorded as `N/A — user: <their reason>`. Replace `[ask the user]` only with
  what the user actually answered. Set Clarifying Questions Asked to Y only when every line is
  answered. This checks the lines are filled, not that a real conversation happened.
-->

- **Goal & scope:** [ask the user]
- **Users & permissions:** [ask the user]
- **Data:** [ask the user]
- **Flow & interaction:** [ask the user]
- **Edge cases & failure handling:** [ask the user]
- **Non-functional (performance, security, reliability, compliance):** [ask the user]
- **Integrations & external dependencies:** [ask the user]
- **Constraints & trade-offs:** [ask the user]
- **Terminology & conventions:** [ask the user]
- **Acceptance criteria (done means):** [ask the user]

---

## Approach

<!--
  Two steps, in this order, both with the user. Propose, don't decide: the user may pick another
  option, reorder, split differently, or cut scope. Wait for a reply each time; silence is not
  confirmation.
  1. Explain the approach in plain language (what will change, why this way, alternatives,
     risks) — no unexplained jargon; the user must be able to follow it to agree or disagree.
  2. Only after that is agreed, propose the breakdown — it depends on the chosen approach — together
     with everything each task changes besides code: spec docs (document-registry.yaml `update_trigger`),
     tests, dependencies, config/CI/deploy, per-module docs. Fill all five lines below; the user confirms.
  Who to discuss what with: the approach and breakdown decide what ships first and what gets
  cut, so agree them with whoever owns the requirement; deeper technical detail is discussed with
  the people who will build and maintain it. Set Approach Confirmed to Y after both steps.
-->

- **Approach:** [How this will be implemented and why this way — in terms the user can follow]
- **Alternatives considered:** [At least one, with the trade-off, wherever there is a real choice]
- **Risks / unknowns:** [What could go wrong; what to try first (spike) before committing to the plan]
- **Breakdown:** [Tasks in order, each following the size rules in templates/project-plan.md; mark [P] where no dependency]
- **Docs to update:** [Per task: which spec docs change and why (candidates: `python3 build-context.py --task-type sprint-end` = every doc for this project type, unfiltered by task type; matched against `update_trigger` in document-registry.yaml; project-requirements.md always). Also name candidates ruled out and why. The user confirms; it becomes the Doc Checklist]
- **Tests to add/update:** [Per task: which tests, and which AC-/FR- id each covers — or `N/A — user: <reason>`]
- **Dependencies:** [Packages added / removed / upgraded and the manifest or lockfile touched, plus docs/specs/dependencies.md — or `none`]
- **Config / CI / deploy:** [Env vars, config files, migrations, CI, Docker/deploy files touched — or `none`]
- **Per-module docs:** [New or changed modules needing a flow file and log file; index tables (business-objects, business-process, prompt-library) to update; README file tree — or `none`]
- **Out of scope:** [What this task deliberately does not do]

---

## Required Context

<!--
  Only include documents actually needed for this task.
  Do not include project-requirements.md, project-plan.md, or changelog.md
  unless this task explicitly requires them.

  If this task involves debugging a failure or investigating unexpected output, add:
  - Pipeline stage failure / data quality issue  → docs/specs/pipeline-debug.md
  - LLM wrong answer / eval score drop / tool failure → docs/specs/llm-debug.md
-->

* `docs/[relevant file]`
* `[other required file paths]`

---

## Steps

- [ ] **Step 1: [Step name]**
  [Description]
  Expected: [expected result]

- [ ] **Step 2: [Step name]**
  [Description]
  Expected: [expected result]

- [ ] **Verify**
  Run: `[exact command]`
  Expected: `[exact output or behaviour]`
  Do not mark this task complete until the expected output is confirmed.

---

## Next Task

<!--
  Fill this in when the current task is created (copied from project-plan.md once).
  When the current task completes, this becomes the new Current Task — no need to re-read project-plan.md.
  If unknown, write: "See project-plan.md"
-->

**Task:** [Next task name]
**Goal:** [What the next task needs to achieve]
**Required Context:** [Files the next task will need]

---

## Doc Checklist (this task only)

<!--
  WHEN TO FILL: when this task is first set up — not at closeout.
  HOW TO FILL: Run `python3 build-context.py` to generate `.ai/AI_CONTEXT.md` before starting.
  The Doc Checklist section in the generated file lists which documents to update for this task type.

  WHEN TO RUN: at task completion (Task Completion step 1a).
  Apply each item listed here — do NOT re-open AGENTS.md at closeout.

  ENFORCED: .githooks/pre-commit blocks a commit that sets Status to Complete while this
  section still has an unchecked `- [ ]` item or the raw, never-customized placeholder
  (`[relevant spec]`) below. Check items off (`- [x]`) as you actually apply them, not all
  at once at the end from memory.
-->

- [ ] `docs/project-requirements.md` — write the confirmed Clarifications back into the spec (scope/users → Goals, Scope, Roles; data/flow/integrations → Functional Requirements; non-functional → Non-Functional Requirements; edge cases → Edge Cases; done means → Acceptance Criteria AC-XXX; terminology/constraints → Assumptions). Keep this line and check it off once written.
- [ ] `docs/[relevant spec]` — [what to check / update]
- [ ] `docs/[relevant spec]` — [what to check / update]
<!-- Add or remove lines. At task completion, run only what is listed here. -->

---

## Closeout (when all Steps and Verify are done)

- **Requirement Status**: when this was the LAST task in Approach → Breakdown, set `Requirement Status` → `Complete` (fill `Requirement IDs`); otherwise leave it `In Progress`. `git push` to main/master then verifies that requirement.
- **Doc Checklist + current-state.md** (1 edit): apply Doc Checklist items above; set Status → `Complete — Pending Sprint Doc Sync`; mark steps `[x]`; promote Next Task → Current Task; update Required Context + Doc Checklist for new task; set Status → `In Progress`
  If this task touched any file outside `docs/`, commit *before* promoting Next Task →
  Current Task, then promote in its own docs-only commit — see `templates/task-completion.md`
  step 1 for why (the pre-commit source-change guard reads this file's state at commit time).
- **Verify**: run the command in the Verify step and confirm expected output — "no errors" is not sufficient
*(Replace `TYPE` in each command below with the value from `.project-starter.yml → project_type`.)*
- **Doc verification**: run pre-commit hook (`git commit`) or manually: `python3 docs/script/validators/verify_docs.py --project-type TYPE --content` — Required: __ / __ present
- **Log verification**: `python3 docs/script/validators/verify_logs.py --project-type TYPE --strict` — Verdict: ___
- **Test report verification**: `python3 docs/script/validators/verify_tests.py --project-type TYPE --strict` — Verdict: ___
- **Content quality verification**: `python3 docs/script/validators/verify_content.py --project-type TYPE --strict` — Verdict: ___
- **sprint-change-log.md**: append one entry — implementation summary, impact flags (Architecture/DB/API/Deployment/Module flow), status `Pending documentation synchronization`
  Then count entries at that status. **At 3, run Sprint Documentation Sync (`templates/sprint-sync.md`) now, before starting the next task** — this is a count trigger, not a calendar one; do not wait for a "sprint end."
  ENFORCED: `.githooks/pre-push` blocks a push to main/master once the Pending count reaches 3, until sync marks entries `Documentation synchronized`. Commits are not blocked.
- **task-log.md**: write one row — all columns must be ✅ before writing

> Need the full verification table or step detail? Load `templates/task-completion.md`.

---

## Notes

* [Implementation decisions, rationale, or issues encountered]
