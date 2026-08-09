---
name: task-closeout
description: Use at the end of every task, once all Steps and Verify in docs/current-state.md pass, when the inline Closeout section in current-state.md isn't enough on its own — e.g. you need the full verification table, the exact per-artifact-type verification method, or the commit-sequencing note for step 1c (promoting Next Task -> Current Task). For the common case, current-state.md's own Closeout section already has enough detail and this Skill isn't needed. Do NOT use for module completion (all tasks in a module done — see module-completion-check) or sprint documentation sync (3 pending sprint-change-log.md entries — see sprint-doc-sync).
---

# Task Completion

**Workflow: Task completed → minimal writes only. Sprint completed → synchronize all documentation.**

Do NOT update changelog.md, project-plan.md, codebase-map.md, or any spec/architecture/business document after a single task — defer to Sprint Documentation Sync.

## Mandatory post-task steps (every task)

1. **Apply Doc Checklist, then update `docs/current-state.md`** (1 edit block, in this order):
   a. Apply each item in `docs/current-state.md → Doc Checklist` — update the listed doc files now.
      These are the only doc updates that happen at task level. Do not open the full Document Update Checklist in AGENTS.md.
   b. In `docs/current-state.md`, while Current Task is still the old task:
      - Set **Status** to `Complete — Pending Sprint Doc Sync`
      - Mark completed steps `[x]`
   c. Now promote Next Task → Current Task:
      - Copy **Next Task** → **Current Task** (name, goal)
      - Look up the task after upcoming in project-plan.md → write it into **Next Task**
        (upcoming → Current Task; the task after upcoming → Next Task)
      - Update **Required Context** for the new current task
      - Update **Doc Checklist** → already filtered when this task was set up; replace with filtered list for the new task
      - Set **Status** to `In Progress`

      > Note: `current-state.md → Closeout` omits Step 1c for brevity — the authoritative procedure is here.

   > **Commit before 1c if this task touched source files.** `.githooks/pre-commit`'s
   > Unscoped source-change guard reads `current-state.md`'s Current Task at commit time
   > against whatever is staged — once 1c promotes Current Task to the next (unscoped)
   > task, staging source files from the task that just finished will be blocked, even
   > though they belonged to a properly-scoped task. If the task touched any file outside
   > `docs/`, commit everything through 1b first (source + doc changes, with Current Task
   > still showing the just-finished task and `Status: Complete — Pending Sprint Doc
   > Sync`), *then* apply 1c as its own follow-up commit that only touches
   > `docs/current-state.md`. A docs-only task (no source files touched) can still do the
   > whole block — including 1c — in one commit.

2. **Run verification** for what was changed:

| Changed artifact | Required verification |
|---|---|
| New feature / endpoint | Call the endpoint, confirm expected response |
| Database migration / schema | Run migration, confirm schema matches expected state |
| Config / environment | Start affected service, confirm healthy |
| Network / infrastructure config | Verify connectivity between affected services (e.g. `docker exec serviceA ping serviceB`) |
| Script / utility | Run the script, confirm expected output |
| Documentation only | `python3 docs/script/generators/build_pdf.py docs --lang en -o /tmp/test.pdf` |
| Diagram (plantuml block) | Rebuild PDF, confirm diagram renders correctly |

Verification must confirm the feature works — not just that no errors occurred.
- ❌ "No errors in log" is not sufficient
- ✅ "Endpoint returns expected data", "UI shows correct state", "output matches expected value"

For validation / guard logic: verify that invalid input is correctly rejected.
- ❌ "All checks passed on clean data" alone is not sufficient
- ✅ "Fed invalid data → check correctly returned failure"

3. **Add one entry to `docs/sprint-change-log.md`** (1 edit):
   - Implementation summary, technical impact flags (Architecture/DB/API/Deployment/Module flow), potential documentation updates.
   - Status: **Pending documentation synchronization**
   - Insert chronologically — append after the last existing entry, not at the top.

4. **Write one row to `docs/task-log.md`** (1 edit):

`| [date] | [task] | [files changed] | [command run] | ✅/❌ [result] | current-state ✅ | sprint-log ✅ |`
