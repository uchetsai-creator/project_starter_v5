# Project Plan

<!--
  Decomposition: Requirement → Slice → Task → Step. The method is the same for every project
  type; load guidance/decomposition/common.md and guidance/decomposition/[project-type].md
  before writing tasks — the type file gives the observer, entry point, task prefixes and
  first-failing-check for that type.

  Ordering principles:
  1. Shared foundation first (Milestone 1, INF tasks — groundwork no single slice owns).
  2. One milestone per slice, in priority order (P1 first). Slices are declared in
     project-requirements.md → ## Slices. The milestone ends when the slice's Independent
     Test passes.
  3. Inside a slice, one task per artifact kind, in data-flow order:
       Contract → State → Logic → Guard → Entry
     (skip kinds the slice does not need). Guard — failure / bad-input handling — is always
     its own task, separate from the happy path.
  4. Size each task using the objective rules below, not a time guess — "half a day
     to a day" is what a correctly-sized task tends to land on, but it is a side
     effect of the rules, not the rule itself. If a task fits the rules but clearly
     isn't half-day-sized, that means a step or file was undercounted — recheck it,
     don't override the rules with a gut-feel estimate.

  Task size rules (apply these to decide where to split, in this order):
  - One-sentence intent: you should be able to state the task's goal in one sentence
    without joining two unrelated things with "and". A task can pass every rule below
    and still be two tasks in disguise if it fails this check — split it first.
  - One artifact kind per task (Contract / State / Logic / Entry / Guard).
  - A task should have no more than 5 steps (excluding Verify).
  - If a task has more than 5 steps, split it into two tasks.
  - A task should touch no more than 3-4 files. If more, split it.
  - A task should be completable and verifiable on its own — if it cannot be verified
    without finishing another task first, merge them or reorder.
  - A task covers at least one FR or AC of its slice, named on its **Covers:** line.
    A task that covers nothing belongs to another slice or should be merged.
    verify_acceptance.py fails when a declared FR / AC is covered by no task (checked once
    this file has at least one filled **Covers:** line).
  - A Guard task handles at most three failure cases; more → split by failure family.

  Step size rules (apply within a task — steps are sequential, no [P] marker needed):
  - Step 1 writes the check that will prove the task, and it fails first (a test, a CLI
    assertion, a data assertion, an eval case, an expected plan diff — the type file names
    the usual one). Expected result: fails for the right reason.
  - A step is one action with exactly one expected result. If the Expected result needs
    "and" to describe two separate checks, split into two steps.
  - A step should map to roughly one file, or one function/endpoint/component within a
    file. If a step's action needs 2+ files to reach its expected result, either split
    it into one step per file, or the task itself is over the file-count rule above.
  - A step's Expected result must be checkable immediately (read the diff, run one
    command, glance at output) — not "only provable once a later step is also done."

  Task naming convention: [Prefix] [SL-n] [What it produces], or [Prefix] [P] [SL-n] [...]
  when marked parallel-safe (see below). Foundation tasks have no slice id.
  Prefixes:
  - web-app: DB / BE / FE (Milestone Documentation Sync and run-verify.sh read these;
    Contract, Logic and server-side Guard are BE, State is DB, Entry is FE). DB / BE / FE are
    always separate tasks.
  - every other type: CONTRACT / STATE / LOGIC / ENTRY / GUARD.
  - shared foundation: INF.  Existing MOD prefix (module-level work) is still accepted.

  Parallel marker [P]: mark a task [P] when it has no dependency on any other
  not-yet-completed task in the plan (e.g. two unrelated INF tasks, or tasks of two
  independent slices). This framework executes one Current Task at a time, so [P] does not
  mean "run simultaneously" — it means "not blocked, safe to pull forward out of order if
  priorities shift." Do not mark a task [P] if it depends on an earlier task in the same
  slice (e.g. Logic depending on its slice's State task).

  Filled example (cli-tool):
    ## Milestone 2: SL-1 — `tool export --format csv` writes CSV (P1)
    Independent Test: run on the fixture → exit 0, first stdout line is the header row
    ### Task 2: CONTRACT [SL-1] --format flag and accepted values     Covers: FR-001
    ### Task 3: LOGIC [SL-1] CSV serialiser                           Covers: FR-001, AC-001
      Step 1 test serialise(fixture) == expected CSV  → fails (function missing)
      Step 2 implement serialise in src/export/csv.py → test passes
    ### Task 4: GUARD [SL-1] unsupported format exits 2               Covers: AC-002
    ### Task 5: ENTRY [SL-1] export command calls the serialiser      Covers: AC-001
      Verify: run SL-1's Independent Test
  More examples, one per project type: guidance/decomposition/[project-type].md.

  Code quality tasks (added by code-quality-check.md) use the prefix [CODE QUALITY]
  and are inserted at the end of the current milestone when found.
  After completing [CODE QUALITY] tasks, review all remaining tasks and update any
  that reference changed function names, module interfaces, or file paths.
-->

---

## Milestone 1: Shared Foundation

Tasks in this milestone:
- Task 1: INF [Foundation Name]

### Task 1: INF [Foundation Name]

**Goal:** [What this task achieves]

**Covers:** [FR / AC ids — or "none — foundation" for groundwork no slice owns]

**Context:** `[file path]` — [why it needs to be read before starting]

**Files:**
- Create: `[file path]`
- Modify: `[file path]`

**Doc Checklist:**
<!--
  List only the documents that could need updating when this specific task completes.
  This is copied into current-state.md when the task starts — it becomes the only
  checklist the Agent runs at task completion (no need to open AGENTS.md).

  Pick by artifact kind (the type file names the concrete docs):
  - Contract task:      api-contract.md, cli-contract.md, public-api.md, pipeline-contract.md,
                        service-contract.md, mobile-contract.md, model-contract.md, llm-contract.md,
                        mcp-contract.md, permissions.md
  - State task:         data-model.md, database.md, business-objects.md, deployment.md
  - Logic task:         business-rules.md, business-process.md, module-data-flow.md, module-flow.md,
                        prompt-library.md, prompts/[id]-prompt.md, rag-contract.md, experiment-log.md
  - Entry task:         frontend.md, codebase-map.md (page structure), module-data-flow.md,
                        logging-spec.md, quickstart.md
  - Guard task:         business-rules.md, api-contract.md (error codes), logging-spec.md,
                        eval-spec.md, drift-policy.md, runbook.md
  - Config/infra (INF): deployment.md, quickstart.md
  - Eval run:           eval-log.md (append one row), eval-spec.md (if criteria changed)
-->
- [ ] `docs/[relevant spec]` — [what to check]

- [ ] **Step 1: [Step name]**
  [What to do. Expected result: [description]]

- [ ] **Step 2: [Step name]**
  [What to do. Expected result: [description]]

- [ ] **Verify**
  Run: `[exact command]`
  Expected: `[exact output or behaviour]`
  Do not mark this task complete until the expected output is confirmed.

---

## Milestone 2: SL-1 — [Slice behavior] (P1)

**Independent Test:** [Copied from project-requirements.md → ## Slices — run by the last task of this milestone]

Tasks in this milestone:
- Task 2: [Prefix] [SL-1] Contract — [What it defines]
- Task 3: [Prefix] [SL-1] State — [What it stores]
- Task 4: [Prefix] [SL-1] Logic — [What it computes]
- Task 5: [Prefix] [SL-1] Guard — [Which failures it handles]
- Task 6: [Prefix] [SL-1] Entry — [Where the observer reaches it]

### Task 2: [Prefix] [SL-1] Contract — [What it defines]

**Goal:** [Description]

**Covers:** [FR ids]

**Context:** `[file path]` — [why]

**Files:**
- Create: `[file path]`

**Doc Checklist:**
- [ ] `docs/specs/[contract spec for this type]` — update the interface definition

- [ ] **Step 1: [Write the failing contract check]**
  [Description. Expected result: check fails because the interface does not exist yet]

- [ ] **Step 2: [Define the interface]**
  [Description. Expected result: check from Step 1 passes]

- [ ] **Verify**
  Run: `[exact command]`
  Expected: `[exact output]`
  Do not mark this task complete until the expected output is confirmed.

---

### Task 3: [Prefix] [SL-1] State — [What it stores]

**Goal:** [Description]

**Covers:** [FR ids]

**Context:** `[schema / state file]` — [why]

**Files:**
- Create: `[migration / state file path]`

**Doc Checklist:**
- [ ] `docs/specs/data-model.md` — update schema, indexes, state machine if changed
- [ ] `docs/architecture/database.md` — update if main entities or relationships changed

- [ ] **Step 1: [Write the failing state check]**
  [Description. Expected result: fails — the field / table / resource does not exist yet]

- [ ] **Step 2: [Add the storage change]**
  [Description. Expected result: check from Step 1 passes]

- [ ] **Verify**
  Run: `[exact command]`
  Expected: `[exact output]`
  Do not mark this task complete until the expected output is confirmed.

---

### Task 4: [Prefix] [SL-1] Logic — [What it computes]

**Goal:** [Description]

**Covers:** [FR and happy-path AC ids]

**Context:** `[file path]` — [why]

**Files:**
- Create: `[file path]`
- Modify: `[file path]`

**Doc Checklist:**
- [ ] `docs/business/business-rules.md` — update if business constraints changed
- [ ] `docs/modules/module-data-flow.md` — update if the data flow changed

- [ ] **Step 1: [Write the failing happy-path check]**
  [Description. Expected result: fails for the right reason]

- [ ] **Step 2: [Implement]**
  [Description. Expected result: check from Step 1 passes]

- [ ] **Verify**
  Run: `[exact command]`
  Expected: `[exact output]`
  Do not mark this task complete until the expected output is confirmed.

---

### Task 5: [Prefix] [SL-1] Guard — [Which failures it handles]

**Goal:** [Description — at most three failure cases]

**Covers:** [Failure-case AC ids]

**Context:** `[file path]` — [why]

**Files:**
- Modify: `[file path]`

**Doc Checklist:**
- [ ] `docs/business/business-rules.md` — update if a constraint or error rule changed
- [ ] `docs/specs/logging-spec.md` — add the new error events if any

- [ ] **Step 1: [Write the failing check for failure case 1]**
  [Description. Expected result: fails — the case is not handled yet]

- [ ] **Step 2: [Handle failure case 1]**
  [Description. Expected result: check from Step 1 passes]

- [ ] **Verify**
  Run: `[exact command]`
  Expected: `[every failure case returns the documented result]`
  Do not mark this task complete until the expected output is confirmed.

---

### Task 6: [Prefix] [SL-1] Entry — [Where the observer reaches it]

**Goal:** [Description]

**Covers:** [AC ids checked at the entry point]

**Context:** `[file path]` — [why]

**Files:**
- Create: `[file path]`

**Doc Checklist:**
- [ ] `docs/architecture/frontend.md` / `docs/specs/quickstart.md` — update for the new entry point
- [ ] `docs/codebase-map.md` — update if new pages, commands, DAG tasks or exports were added

- [ ] **Step 1: [Write the failing entry-point check]**
  [Description. Expected result: fails — the entry point is not wired yet]

- [ ] **Step 2: [Wire the entry point]**
  [Description. Expected result: check from Step 1 passes]

- [ ] **Verify**
  Run: `[the slice's Independent Test]`
  Expected: `[exact output or behaviour]`
  Do not mark this task complete until the expected output is confirmed.

<!--
  Insert [CODE QUALITY] tasks here if Medium/Low issues were found during code-quality-check.md.
  Complete these before starting Milestone 3.
  After completing, review Milestone 3+ tasks and update any affected function names or file paths.

  Format:
  ### Task N: [CODE QUALITY] [Area]: [Recommendation]
  **Goal:** [What to fix and why]
  **Files:**
  - Modify: `[file path]`
  - [ ] **Step 1: [Fix description]**
  - [ ] **Verify**
    Run: `[exact command]`
    Expected: `[no regressions, behaviour unchanged]`
    Do not mark this task complete until the expected output is confirmed.
-->

---

## Milestone 3: SL-2 — [Slice behavior] (P2)

**Independent Test:** [Copied from project-requirements.md → ## Slices]

Tasks in this milestone:
- Task 7: [Prefix] [SL-2] Logic — [What it computes]
- Task 8: [Prefix] [SL-2] Entry — [Where the observer reaches it]

### Task 7: [Prefix] [SL-2] Logic — [What it computes]

**Goal:** [Description]

**Covers:** [FR and AC ids]

**Context:** `[file path]` — [why]

**Files:**
- Create: `[file path]`

**Doc Checklist:**
- [ ] `docs/business/business-rules.md` — update if business constraints changed

- [ ] **Step 1: [Write the failing check]**
  [Description]

- [ ] **Verify**
  Run: `[exact command]`
  Expected: `[exact output]`
  Do not mark this task complete until the expected output is confirmed.

---

### Task 8: [Prefix] [SL-2] Entry — [Where the observer reaches it]

**Goal:** [Description]

**Covers:** [AC ids]

**Context:** `[file path]` — [why]

**Files:**
- Create: `[file path]`

**Doc Checklist:**
- [ ] `docs/codebase-map.md` — update if new entry points were added

- [ ] **Step 1: [Write the failing check]**
  [Description]

- [ ] **Verify**
  Run: `[the slice's Independent Test]`
  Expected: `[exact output or behaviour]`
  Do not mark this task complete until the expected output is confirmed.

---

## Completed

* [Task name] — [completion date]
