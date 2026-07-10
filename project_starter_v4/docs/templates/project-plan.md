# Project Plan

<!--
  Ordering principles:
  1. Shared foundation first
  2. Each feature as a vertical slice: DB → BE → FE
  3. Each task should be roughly half a day to one day of work
  4. Group tasks into sprints — a sprint is a logical chunk of work, typically 3-5 tasks

  Task size rules:
  - A task should have no more than 5 steps (excluding Verify).
  - If a task has more than 5 steps, split it into two tasks.
  - A task should touch no more than 3-4 files. If more, split it.
  - A task should be completable and verifiable on its own — if it cannot be verified
    without finishing another task first, merge them or reorder.
  - DB / BE / FE are always separate tasks. Never combine layers in one task.

  Task naming convention: [Layer] [Feature Name]
  Layer prefixes: DB / BE / FE / MOD / INF

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
