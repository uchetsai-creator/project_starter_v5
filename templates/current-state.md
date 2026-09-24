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
<!-- Y: this task started from a new user requirement and scope/edge-case/acceptance-criteria
     questions were asked before implementing (AGENTS.md -> New requirement from the user /
     Learning Checkpoint B). N/A: task was already scoped in project-plan.md, or Checkpoint A
     (existing code) applied instead. Fill this in when Task above stops being a placeholder —
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

**Status:** In Progress
<!-- When done: "Complete — Pending Sprint Doc Sync" -->

---

## Approach

<!--
  Two steps, in this order, both with the user. Propose, don't decide: the user may pick another
  option, reorder, split differently, or cut scope. Wait for a reply each time; silence is not
  confirmation.
  1. Explain the approach in plain language (what will change, why this way, alternatives,
     risks) — no unexplained jargon; the user must be able to follow it to agree or disagree.
  2. Only after that is agreed, propose the breakdown — it depends on the chosen approach.
  Who to discuss what with: the approach and breakdown decide what ships first and what gets
  cut, so agree them with whoever owns the requirement; deeper technical detail is discussed with
  the people who will build and maintain it. Set Approach Confirmed to Y after both steps.
-->

- **Approach:** [How this will be implemented and why this way — in terms the user can follow]
- **Alternatives considered:** [At least one, with the trade-off, wherever there is a real choice]
- **Risks / unknowns:** [What could go wrong; what to try first (spike) before committing to the plan]
- **Breakdown:** [Tasks in order, each following the size rules in templates/project-plan.md; mark [P] where no dependency]
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

- [ ] `docs/[relevant spec]` — [what to check / update]
- [ ] `docs/[relevant spec]` — [what to check / update]
<!-- Add or remove lines. At task completion, run only what is listed here. -->

---

## Closeout (when all Steps and Verify are done)

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
  ENFORCED: `.githooks/pre-commit` blocks every commit once the Pending count reaches 3, until sync marks entries `Documentation synchronized`.
- **task-log.md**: write one row — all columns must be ✅ before writing

> Need the full verification table or step detail? Load `templates/task-completion.md`.

---

## Notes

* [Implementation decisions, rationale, or issues encountered]
