# Decomposition — Requirement → Slice → Task → Step

Referenced from `guidance/approach-proposal.md` (step 2, Breakdown) and `templates/project-plan.md`.
Load this file plus `guidance/decomposition/[your-declared-type].md` before proposing a breakdown.
For a hybrid type (`data-pipeline+web-app`), load the type file of the component each task touches.

The method is the same for every project type. Only the nouns change — who observes the
behavior, where they enter, what each artifact kind is called, and how it is verified — and
those live in the type file, not here.

---

## Level 1 — Requirement → Slices

A **slice** is one behavior an external observer can see and check from the system's entry
point, without reading the code.

- **Observer** — who sees the behavior: an end user, a calling service, a CLI caller, a
  library consumer, a downstream data consumer, an operator. The type file names it.
- **Entry point** — where the observer meets the system: a screen, an endpoint, a command, a
  public function, an output table, an infrastructure state. The type file names it.

Rules:

1. **One behavior, one sentence.** If stating the slice needs "and" joining two behaviors, it
   is two slices.
2. **Independently testable.** Built alone, the slice can be verified from its entry point.
   Write this as the slice's `Independent Test`.
3. **Not testable alone → merge or reorder.** If a slice can only be checked once another
   slice also exists, merge the two or move the dependency earlier.
4. **Prioritise.** P1 is the smallest slice that is worth shipping on its own (the MVP); P2+
   follow in order. Shared groundwork that no slice owns goes into a foundation milestone.
5. **Every FR belongs to one slice; every AC belongs to the slice whose behavior it checks.**
   In `project-requirements.md`, slices are declared in `## Slices` and FR / AC entries are
   grouped under `### SL-n` sub-headings inside their own sections.

A requirement from the user usually produces one to three slices. One slice = one milestone in
`project-plan.md`.

---

## Level 2 — Slice → Tasks (by artifact kind, not by technical layer)

Inside a slice, split by the **kind of artifact** each task produces. Order the tasks
Contract → State → Logic → Guard → Entry, so the last task wires the entry point onto
behavior that already handles its failures and can run the slice's Independent Test:

| Kind | What it produces |
|---|---|
| **Contract** | The interface the observer depends on — its shape, types, parameters, schema |
| **State** | Where data lives — storage, migrations, persisted config, infrastructure state |
| **Logic** | The core processing that turns input into the observable result |
| **Guard** | Behavior on bad input, failure, missing permission, or broken data |
| **Entry** | Wiring the logic to the entry point the observer uses |

Rules:

1. **One task produces one kind.** Skip kinds the slice does not need (a library slice often
   has no State; a docs-only change may have only Contract).
2. **Guard is always its own task.** The happy path and its failure handling are separate
   tasks, so each can be verified on its own.
3. **Each task covers at least one AC or FR of its slice.** Write it on the task's
   `**Covers:**` line. A task that covers nothing either belongs to a different slice or
   should be merged into a task that does. `verify_acceptance.py` checks that every declared
   FR / AC is covered by at least one task once the plan uses `**Covers:**`.
4. **At most three failure cases per Guard task.** More than that → split by failure family
   (input validation / permission / downstream failure).
5. **Task prefix** — use the prefix the type file gives for each kind. `web-app` keeps
   `DB` / `BE` / `FE` (the Milestone Documentation Sync trigger reads those prefixes). Every
   other type uses the kind name itself: `CONTRACT`, `STATE`, `LOGIC`, `ENTRY`, `GUARD`.
   Shared foundation tasks use `INF`. Put the slice id right after the prefix:
   `### Task 15: BE [SL-2] Alarm acknowledge API — error handling`.

The size rules in `templates/project-plan.md` still apply to every task: one-sentence intent,
at most 5 steps (excluding Verify), at most 3-4 files, completable and verifiable on its own.

---

## Level 3 — Task → Steps

1. **The first step writes a check that fails.** It does not have to be a unit test — use the
   check the type file names (an HTTP test, a CLI exit-code assertion, a data assertion, an eval
   case, an expected `plan` diff). Expected result: the check fails for the right reason.
2. **One step = one file (or one function / endpoint / component within a file) = one result.**
   If the expected result needs "and" for two separate checks, split the step.
3. **Each expected result is checkable immediately** — read the diff, run one command, glance
   at output. Not "only provable once a later step is done".
4. **Verify runs the slice-level check when the task completes the slice.** The last task of a
   slice runs the slice's `Independent Test`.

---

## Worked example (shape only — nouns come from the type file)

```
Requirement: "When equipment faults an alarm appears; a line lead can acknowledge it,
              which removes it from the list and records who acknowledged it."

SL-1 (P1)  Fault raises a visible alarm
           Independent Test: trigger a fault → the alarm appears at the entry point
SL-2 (P2)  A line lead acknowledges an alarm
           Independent Test: acknowledge one alarm → it leaves the list; who/when recorded

Milestone: SL-2
  Task  State  [SL-2]  acknowledgedBy / acknowledgedAt fields         Covers: FR-008
  Task  Logic  [SL-2]  acknowledge an alarm (happy path)              Covers: FR-008, AC-005
  Task  Guard  [SL-2]  already acknowledged → conflict; no permission → forbidden
                                                                      Covers: AC-006, AC-007
  Task  Entry  [SL-2]  acknowledge action at the entry point          Covers: AC-005
        Verify: run SL-2's Independent Test
```

The same skeleton fits a pipeline (Contract = output table schema, Logic = transform,
Entry = DAG wiring, Guard = data quality check) or a CLI (Contract = flags, Logic = core
function, Entry = command wiring, Guard = exit code on bad input). See the type file.
