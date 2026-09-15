# Project Plan

<!--
  Ordering principles:
  1. Shared foundation first
  2. Each feature as a vertical slice: DB → BE → FE
  3. Size each task using the objective rules below, not a time guess — "half a day
     to a day" is what a correctly-sized task tends to land on, but it is a side
     effect of the rules, not the rule itself. If a task fits the rules but clearly
     isn't half-day-sized, that means a step or file was undercounted — recheck it,
     don't override the rules with a gut-feel estimate.
  4. Group tasks into sprints — a sprint is a logical chunk of work, typically 3-5 tasks

  Task size rules (apply these to decide where to split, in this order):
  - One-sentence intent: you should be able to state the task's goal in one sentence
    without joining two unrelated things with "and". A task can pass every rule below
    and still be two tasks in disguise if it fails this check — split it first.
  - A task should have no more than 5 steps (excluding Verify).
  - If a task has more than 5 steps, split it into two tasks.
  - A task should touch no more than 3-4 files. If more, split it.
  - A task should be completable and verifiable on its own — if it cannot be verified
    without finishing another task first, merge them or reorder.
  - DB / BE / FE are always separate tasks. Never combine layers in one task.

  Step size rules (apply within a task — steps are sequential, no [P] marker needed):
  - A step is one action with exactly one expected result. If the Expected result needs
    "and" to describe two separate checks, split into two steps.
  - A step should map to roughly one file, or one function/endpoint/component within a
    file. If a step's action needs 2+ files to reach its expected result, either split
    it into one step per file, or the task itself is over the file-count rule above.
  - A step's Expected result must be checkable immediately (read the diff, run one
    command, glance at output) — not "only provable once a later step is also done."

  Task naming convention: [Layer] [Feature Name], or [Layer] [P] [Feature Name] when
  marked parallel-safe (see below).
  Layer prefixes: DB / BE / FE / MOD / INF

  Parallel marker [P]: mark a task [P] when it has no dependency on any other
  not-yet-completed task in the plan (e.g. two unrelated INF tasks, or DB tasks for two
  different features in the same sprint). This framework executes one Current Task at a
  time, so [P] does not mean "run simultaneously" — it means "not blocked, safe to pull
  forward out of order if priorities shift." Do not mark a task [P] if it depends on
  another layer in the same vertical slice (e.g. BE depending on its own DB task).

  Code quality tasks (added by code-quality-check.md) use the prefix [CODE QUALITY]
  and are inserted at the end of the current sprint when found.
  After completing [CODE QUALITY] tasks, review all remaining tasks and update any
  that reference changed function names, module interfaces, or file paths.
-->

---

## Sprint 1: Shared Foundation

Tasks in this sprint:
- Task 1: INF [Foundation Name]

### Task 1: INF [Foundation Name]

**Goal:** [What this task achieves]

**Context:** `[file path]` — [why it needs to be read before starting]

**Files:**
- Create: `[file path]`
- Modify: `[file path]`

**Doc Checklist:**
<!--
  List only the documents that could need updating when this specific task completes.
  This is copied into current-state.md when the task starts — it becomes the only
  checklist the Agent runs at task completion (no need to open AGENTS.md).

  Pick from:
  - DB task:            data-model.md, database.md, business-objects.md
  - BE endpoint task:   api-contract.md, permissions.md, module-data-flow.md, module-flow.md, logging-spec.md
  - FE task:            frontend.md, codebase-map.md (page structure)
  - Config/infra task:  deployment.md, quickstart.md
  - Business logic:     business-rules.md, business-process.md, business-objects.md
  - Script/utility:     (usually none)
  - Prompt/LLM task:    llm-contract.md, prompt-library.md, prompts/[id]-prompt.md, eval-spec.md
  - Eval run task:      eval-log.md (append one row), eval-spec.md (if criteria changed)
  - RAG task:           rag-contract.md, llm-contract.md (Context Window Strategy)
  - MCP server task:    mcp-contract.md, llm-contract.md (Tool Calling section)
  - Pipeline stage:     pipeline-contract.md, module-data-flow.md
  - ML model task:      model-contract.md, experiment-log.md
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

## Sprint 2: [Feature A]

Tasks in this sprint:
- Task 2: DB [Feature A] Schema
- Task 3: BE [Feature A]
- Task 4: FE [Feature A]

### Task 2: DB [Feature A] Schema

**Goal:** [Description]

**Context:** `[schema file]` — [why]

**Files:**
- Create: `[migration file path]`

**Doc Checklist:**
- [ ] `docs/specs/data-model.md` — update schema, indexes, state machine if changed
- [ ] `docs/architecture/database.md` — update if main entities or relationships changed

- [ ] **Step 1: [Step name]**
  [Description. Expected result: [description]]

- [ ] **Verify**
  Run: `[exact command]`
  Expected: `[exact output]`
  Do not mark this task complete until the expected output is confirmed.

---

### Task 3: BE [Feature A]

**Goal:** [Description]

**Context:** `[file path]` — [why]

**Files:**
- Create: `[file path]`
- Modify: `[file path]`

**Doc Checklist:**
- [ ] `docs/specs/api-contract.md` — update if endpoints or error codes changed
- [ ] `docs/specs/permissions.md` — update if roles or endpoint access changed
- [ ] `docs/specs/logging-spec.md` — add module name if new module introduced
- [ ] `docs/business/business-rules.md` — update if business constraints changed

- [ ] **Step 1: [Step name]**
  [Description. Expected result: [description]]

- [ ] **Verify**
  Run: `[exact command]`
  Expected: `[exact output]`
  Do not mark this task complete until the expected output is confirmed.

---

### Task 4: FE [Feature A]

**Goal:** [Description]

**Context:** `[file path]` — [why]

**Files:**
- Create: `[file path]`

**Doc Checklist:**
- [ ] `docs/architecture/frontend.md` — update if page structure or component strategy changed
- [ ] `docs/codebase-map.md` (page structure block) — update if new pages/screens added

- [ ] **Step 1: [Step name]**
  [Description]

- [ ] **Verify**
  Run: `[exact command or manual step]`
  Expected: `[exact output or behaviour]`
  Do not mark this task complete until the expected output is confirmed.

<!--
  Insert [CODE QUALITY] tasks here if Medium/Low issues were found during code-quality-check.md.
  Complete these before starting Sprint 3.
  After completing, review Sprint 3+ tasks and update any affected function names or file paths.

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

## Sprint 3: [Feature B]

Tasks in this sprint:
- Task 5: DB [Feature B] Schema
- Task 6: BE [Feature B]
- Task 7: FE [Feature B]

### Task 5: DB [Feature B] Schema

**Goal:** [Description]

**Context:** `[file path]` — [why]

**Files:**
- Create: `[file path]`

**Doc Checklist:**
- [ ] `docs/specs/data-model.md` — update schema, indexes, state machine if changed
- [ ] `docs/architecture/database.md` — update if main entities or relationships changed

- [ ] **Step 1: [Step name]**
  [Description]

- [ ] **Verify**
  Run: `[exact command]`
  Expected: `[exact output]`
  Do not mark this task complete until the expected output is confirmed.

---

### Task 6: BE [Feature B]

**Goal:** [Description]

**Context:** `[file path]` — [why]

**Files:**
- Create: `[file path]`

**Doc Checklist:**
- [ ] `docs/specs/api-contract.md` — update if endpoints or error codes changed
- [ ] `docs/specs/permissions.md` — update if roles or endpoint access changed
- [ ] `docs/specs/logging-spec.md` — add module name if new module introduced
- [ ] `docs/business/business-rules.md` — update if business constraints changed

- [ ] **Step 1: [Step name]**
  [Description]

- [ ] **Verify**
  Run: `[exact command]`
  Expected: `[exact output]`
  Do not mark this task complete until the expected output is confirmed.

---

### Task 7: FE [Feature B]

**Goal:** [Description]

**Context:** `[file path]` — [why]

**Files:**
- Create: `[file path]`

**Doc Checklist:**
- [ ] `docs/architecture/frontend.md` — update if page structure or component strategy changed
- [ ] `docs/codebase-map.md` (page structure block) — update if new pages/screens added

- [ ] **Step 1: [Step name]**
  [Description]

- [ ] **Verify**
  Run: `[exact command or manual step]`
  Expected: `[exact output or behaviour]`
  Do not mark this task complete until the expected output is confirmed.

---

## Completed

* [Task name] — [completion date]
