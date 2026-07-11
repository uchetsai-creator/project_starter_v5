# AGENTS

## Path Convention

Module flow files live in: `docs/modules/`
Codebase map lives in: `docs/codebase-map.md`
Document purposes reference lives in: `document-purposes.md` (repo root)

If your project uses different folder names, search-replace the paths in this file
before starting. For example, if you use `docs/flows/` instead of `docs/modules/`:
  - Search: `docs/modules/`
  - Replace: `docs/flows/`
  - Also update `pdf_allowlist.py` to match.

---

## Project Initialization

If starting a new project:
1. Create docs/project-requirements.md from templates/project-requirements.md.
2. Create docs/specs/research.md from templates/specs/research.md (resolve all NEEDS CLARIFICATION).
3. Create docs/specs/quickstart.md from templates/specs/quickstart.md.
4. Create docs/architecture/architecture.md from templates/architecture/architecture.md.
5. Create docs/architecture/backend.md, frontend.md, database.md, deployment.md from templates/architecture/.
6. Create docs/specs/data-model.md from templates/specs/data-model.md.
7. Create docs/specs/api-contract.md from templates/specs/api-contract.md.
8. Create docs/specs/permissions.md from templates/specs/permissions.md.
9. Create docs/specs/logging-spec.md from templates/specs/logging-spec.md.
10. Create docs/business/business-process.md from templates/business/business-process-v2.md.
11. Create docs/business/business-objects.md from templates/business/business-objects-v2.md.
12. Create docs/business/business-rules.md from templates/business/business-rules.md.
13. Create docs/modules/module-data-flow.md from templates/modules/module-data-flow-v2.md.
14. Create docs/modules/module-flow.md from templates/modules/module-flow-v2.md.
15. Create docs/codebase-map.md from templates/codebase-map.md.
16. Create docs/project-plan.md from templates/project-plan.md.
17. Create docs/task-log.md from templates/task-log.md.
18. Create docs/sprint-change-log.md from templates/sprint-change-log.md.
19. Create docs/current-state.md from templates/current-state.md.

---

If retrofitting an existing project (code already exists, no docs yet):

The goal is to describe what already exists — not to redesign it. Read the codebase first, then fill in the documents to reflect reality.

Do not scan the entire repository at once. Work module by module.

Step 1 — Understand the system (read before writing anything):
1. Read the entry point to understand the overall structure
   (e.g. main file, router, app bootstrap, CLI entry, index)
2. Read the data layer to understand the data model
   (e.g. Prisma schema, SQL DDL, ORM models, migration files)
3. Read one complete vertical slice to understand the layering pattern
   (e.g. controller → service → repository, view → serializer → model, handler → usecase → store)

Step 1b — Run the module inventory scan:

   python3 docs/script/scan_codebase.py <src_dir> --docs docs

Review the output with the user:
- ✅ folders are confirmed as documented
- ❌ folders → ask the user: "Is this a module that needs documentation, a shared utility, or something else?"
- — folders → confirm they do not need a flow file

Classify every folder before proceeding. Do not proceed until the user confirms the inventory is complete.

Step 1c — Code Quality Check:
Read and follow code-quality-check.md. Do not proceed to Step 2 until the check is complete and acknowledged by the user.

Step 2 — Fill in architecture and spec documents (describe what exists):
1. Create docs/architecture/architecture.md — describe the actual components and data flows found.
   Then run: `# Edit the ```plantuml block in architecture.md, then rebuild PDF`
   Note: the architecture diagram is injected into `architecture/architecture.md` by `build_pdf.py`.
   The page structure component diagram (from `codebase-map.md`) is injected into `codebase-map.md`
   — run `# Edit the ```plantuml block in codebase-map.md, then rebuild PDF` after updating the
   component block in codebase-map.md.
2. Create docs/architecture/backend.md — describe the actual stack, layering, and module pattern.
   Use the real layer names from the codebase — do not assume Controller/Service/Repository.
   Then run: `# Edit the ```plantuml block in backend.md, then rebuild PDF`
3. Create docs/architecture/frontend.md (if applicable) — describe the actual frontend structure.
   Then run: `# Edit the ```plantuml block in frontend.md, then rebuild PDF`
4. Create docs/architecture/database.md — describe the actual entities and key relationships.
5. Create docs/architecture/deployment.md — describe the actual services, startup flow, and deployment topology.
   Then run: `# Edit the ```plantuml block in deployment.md, then rebuild PDF`
6. Create docs/specs/data-model.md — fill in from the actual schema file.
   Then run: `Edit the ```plantuml block in the file, then run build_pdf.py`
   (output must go inside docs/ so build_pdf.py can find it)
   Then run: `# Edit the ```plantuml block in data-model.md, then rebuild PDF`
7. Create docs/specs/api-contract.md — fill in from the actual routes and controllers.
8. Create docs/specs/permissions.md — fill in from the actual auth middleware and role logic.
   Then run: `# Edit the ```plantuml block in permissions.md, then rebuild PDF`
9. Create docs/business/business-process.md — describe the actual business workflows supported.
10. Create docs/business/business-objects.md — describe the actual business entities.
11. Create docs/business/business-rules.md — describe the actual constraints enforced in code.
12. Create docs/specs/research.md — document the technology choices already made and why (if known).

Step 3 — Fill in module flow files (one module at a time, following the confirmed inventory from Step 1b):

For each module in the confirmed inventory:
0. Verify docs/modules/module-data-flow.md contains a "## Module Types" section defining
   Feature / Background Job / Shared Utility. If it is missing (older copy of this template),
   copy the current templates/modules/module-data-flow-v2.md content into it before proceeding —
   do not invent your own module type definitions.
1. Determine the module type: Feature / Background Job / Shared Utility
   (follow the rules in docs/modules/module-data-flow.md)
2. Create docs/modules/[module]/[module]-module-data-flow.md following the matching format.
   Use real function names and file paths from the actual code.
   Then run: `Edit the ```plantuml block in the file, then run build_pdf.py`
3. Update docs/modules/module-data-flow.md index with the new module entry.
4. Update docs/codebase-map.md with the files in this module.

After all modules are documented, re-run the inventory scan to confirm full coverage:
   python3 docs/script/scan_codebase.py <src_dir> --docs docs
If any ❌ remain, document those modules before proceeding to Step 4.

Step 4 — Fill in project status documents:
1. Create docs/project-requirements.md — reconstruct from the actual features that exist.
   Mark anything uncertain as [NEEDS CLARIFICATION].
2. Create docs/project-plan.md — list all modules found. Mark all existing ones as completed.
   Add any known remaining work as incomplete tasks.
3. Create docs/current-state.md — set the Current Task to the next incomplete item in project-plan.md,
   or write "Documentation retrofit complete — ready for new tasks" if everything is done.

Step 5 — Generate the PDF:

Before running build_pdf.py, verify flow tables are not empty:
1. Open `docs/modules/module-data-flow.md` — if the Module Flow Files table contains only placeholder rows (no real module names), Step 3 is incomplete. Finish all module flow files first.
2. Open `docs/modules/module-flow.md` — same check for the Flow Files table.
Do not generate the PDF with empty flow index tables.

`python3 docs/script/build_pdf.py docs --lang en -o docs/project-documentation-en.pdf`

---

If continuing an existing project:

**Startup sequence — read in this order, stop as soon as you have enough context:**

1. `docs/current-state.md` — this is the only mandatory read at startup.
   It tells you the current task AND lists exactly which other documents to read.
2. Required Context only — read the documents listed in `docs/current-state.md → Required Context`.
   Nothing else.

Do NOT read docs/project-plan.md, docs/project-requirements.md, or docs/changelog.md
at startup unless docs/current-state.md explicitly lists them in Required Context.

If docs/current-state.md is missing, empty, or ambiguous — read AGENTS.md to orient yourself,
then determine the next step from project-plan.md. Do not read AGENTS.md otherwise.

Do not scan repository.

For what each document is for and when it changes, read document-purposes.md — reference only, not required every task.

---

## Development Principles

- Prefer maintainable architecture over temporary shortcuts
- Maintainability First
- Package First
- Glue Code
- Incremental Changes
- No Unrelated Refactor

---

## Package First

Priority:
1. Existing package
2. Existing utility
3. Framework convention
4. Custom code

Custom code only for:
- Business Logic
- Domain Rules
- Data Mapping
- System Integration

---

## Current State

docs/current-state.md is the active task. It is self-contained — reading it should give you
everything needed to start work and to close out the task when done.

### Starting work

1. Read `docs/current-state.md`.
2. If **Current Task** is filled in:
   - Read the files listed under **Required Context**.
   - Start implementation.
3. If **Current Task** is empty or says "See project-plan.md":
   - Read `docs/project-plan.md` (this is the only time you need to).
   - Copy the next incomplete task's name, goal, required context, and the task after that into current-state.md.
   - Start implementation.

### Closing out a task

current-state.md is a state machine with two fields:

- **Current Task** → the task being worked on now
- **Next Task** → pre-filled when current task was set up; becomes the new Current Task on closeout

**When setting up a new Current Task** (not at closeout):
- Filter the full Document Update Checklist in AGENTS.md down to only items relevant to this task.
- Write the filtered list into `docs/current-state.md → Doc Checklist`.
- This is the ONLY time you open AGENTS.md during normal task work.
- This filtered list is NOT the full 18-item Document Update Checklist (which runs at Sprint Documentation Sync only).

**When all Steps are done and Verify passes**, follow **## Task Completion** below — all current-state.md edits happen there, once. No external files need to be read at closeout.

### Module Completion Check

Run this check after every task — most of the time the answer will be "no," but the check itself must not be skipped.

Do NOT create or update `[module]-module-data-flow.md` or `[module]-flow.md` during a task
unless the module is 100% complete (all tasks for this module are marked done in project-plan.md).
Creating these files mid-module causes repeated read/write cycles during review. Defer until completion.

* Does completing this task finish all work for its module in docs/project-plan.md?
  * If no: this module is not yet complete. Skip the rest of this section.
  * If yes: this module is now complete. Do all of the following:
    1. Insert logger calls into the module's code, following the rules in docs/specs/logging-spec.md.
       Use the logger instantiation pattern defined in logging-spec.md for this project's language/framework.
       Direct print/console statements are not allowed.
       logging-spec.md itself is the rule definition — do not add module-specific content to it.
       Create or update docs/modules/<module-name>/log-<module-name>.md to list every log point added, in call order.
    2. Ask: "Would you like to add debug instrumentation to this module? (follows debug-instrumentation-rules.md)"
       * If yes: follow debug-instrumentation-rules.md and instrument the module.
       * If no: continue.
    3. If the module flow file contains multiple sequence or class blocks, each block
       generates its own diagram file (named by title slug). All are picked up automatically
       by build_pdf.py — no extra configuration needed.
    4. Rebuild the PDF only if ANY of the following conditions are met:
       - This is a Sprint Documentation Sync (always rebuild at sprint end), OR
       - 3 or more diagram blocks (plantuml) have changed since the last PDF build.
       If neither condition is met, skip the PDF rebuild — it will happen at sprint end.

       When rebuilding:
       `python3 docs/script/build_pdf.py docs --lang en -o docs/project-documentation-en.pdf`
       Chinese PDF is manual only — run when requested:
       `python3 docs/script/build_pdf.py docs-zh --lang zh -o docs/project-documentation-zh.pdf`
       Note: to add a new doc to the PDF, add it to docs/script/pdf_allowlist.py only —
       do not edit build_pdf.py for this purpose.

### Document Update Checklist

**Pre-filter before running any checklist item:**
Only check items whose trigger condition could plausibly be true given what this task actually changed.
Skip an item immediately if the task did not touch the relevant area — do not read the item's full detail.

Quick filter guide:
| If the task only touched… | Skip these checklist items entirely |
|---|---|
| Python/JS scripts only | architecture.md, backend.md, frontend.md, database.md, data-model.md, business-objects.md |
| Frontend UI only | data-model.md, api-contract.md (unless new endpoints), backend.md, deployment.md, business-rules.md |
| DB schema only | frontend.md, codebase-map.md page structure, business-process.md, module-flow.md |
| Documentation only | All code-related items (data-model, api-contract, permissions, architecture, backend, frontend) |
| Config / env vars only | All items except deployment.md and quickstart.md |

Apply this filter first. Then run only the remaining items.

- [ ] docs/specs/research.md — did this task involve a new technology decision, or resolve a NEEDS CLARIFICATION? If yes, update. Note: research.md is excluded from the PDF by default (pdf_allowlist.py) — uncomment its entry once it has real content.
- [ ] docs/specs/data-model.md — did the schema, entities, relationships, or indexes change? If yes, update, then:
  - Regenerate ERD: `Edit the ```plantuml block in the file, then run build_pdf.py`
    (output must go inside docs/ so build_pdf.py can find it)
  - Regenerate state diagram: `# Edit the ```plantuml block in data-model.md, then rebuild PDF`
  State Machine Consistency check: if this task touched an entity with a status lifecycle, confirm the State Machine section here matches the canonical definition in docs/business/[object-name]-object.md exactly. If they differ, update this file to match — the object file wins.
- [ ] docs/specs/api-contract.md — were endpoints added/changed, did error codes or validation rules change, or were WebSocket/Socket.IO events / GraphQL queries or mutations / gRPC methods / CLI commands added or changed? If yes, update the relevant protocol section.
  API Endpoint Overlap check: if this task added an endpoint whose purpose overlaps with an existing one (e.g. two endpoints affecting the same state), add a **Design Note:** under each explaining why they are separate, or consolidate into one.
- [ ] docs/specs/permissions.md — were roles, the permission matrix, or API endpoints changed? If yes, update, then regenerate use case diagram: `# Edit the ```plantuml block in permissions.md, then rebuild PDF`
  After updating: cross-check every role listed as "Responsible role" in any `*-process.md` against the API Endpoint Access table and Page Access Matrix. If a role is responsible for an action but has no access to the required page or endpoint, check the Source column:
  - `Hardcoded` → this is a logical contradiction — resolve it before proceeding.
  - `Seeded default` → this may be intentional (the default simply hasn't been granted yet). Confirm with the project owner whether to update the default, then mark the row "(Default)" — do not write it into business-rules.md as a permanent rule.
- [ ] docs/architecture/architecture.md — did components or data flows change? If yes, update, then regenerate diagram: `# Edit the ```plantuml block in architecture.md, then rebuild PDF`
- [ ] docs/codebase-map.md Page Structure block — did the frontend page/screen structure change? If yes, update the component block, then regenerate: `# Edit the ```plantuml block in codebase-map.md, then rebuild PDF`
- [ ] docs/architecture/backend.md — did backend layering, stack, or module pattern change? If yes, update, then regenerate component diagram: `# Edit the ```plantuml block in backend.md, then rebuild PDF`
- [ ] docs/architecture/frontend.md — did frontend stack, page structure, or component strategy change? If yes, update, then regenerate component diagram: `# Edit the ```plantuml block in frontend.md, then rebuild PDF`
- [ ] docs/architecture/database.md — did main entities or relationships change (conceptual level)? If yes, update.
- [ ] docs/architecture/deployment.md — did services, env vars, build/deploy flow, or deployment topology change? If yes, update, then regenerate deployment diagram: `# Edit the ```plantuml block in deployment.md, then rebuild PDF`
- [ ] docs/specs/quickstart.md — did setup steps, prerequisites, or verification steps change? If yes, update.
- [ ] docs/specs/logging-spec.md Module Naming Convention table — does this task introduce a module name not yet listed? If yes, add one line (name + short description) to the table. Do not add module-specific logging detail here — that belongs in docs/modules/<module-name>/log-<module-name>.md.
- [ ] docs/business/business-rules.md — did business constraints or policies change? If yes, update.
- [ ] docs/business/[object-name]-object.md — were business entities added or changed? If yes, update, then regenerate state diagram: `Edit the ```plantuml block in the file, then run build_pdf.py`
- [ ] docs/business/business-objects.md — was a new business object file created or did relationships change? If yes, update the index.
- [ ] docs/business/[process-name]-process.md — did the business workflow, decision points, or exceptions change for this process? If yes, update, then regenerate activity diagram: `Edit the ```plantuml block in the file, then run build_pdf.py`
- [ ] docs/business/business-process.md — was a new business process file created? If yes, add a row to the index table.
- [ ] docs/modules/[module]/[module]-module-data-flow.md — did function names, file paths, or flow steps change for this module? If yes, update, then regenerate class diagram: `# Edit the ```plantuml block in the module data flow file, then rebuild PDF`
- [ ] docs/modules/module-data-flow.md index table — open the file and verify the current module has a row in the Module Flow Files table. If the row is missing, add it now. Do not rely on memory — read the file.
- [ ] docs/modules/[module]/[module]-flow.md — did cross-module service calls change for this module? If yes, update, then regenerate sequence diagram: `# Edit the ```plantuml block in the module flow file, then rebuild PDF`
- [ ] docs/modules/module-flow.md index table — open the file and verify the current module has a row in the Flow Files table (only if a [module]-flow.md exists for this module). If the row is missing, add it now. Do not rely on memory — read the file.

For the full explanation of why each document updates on these triggers, see document-purposes.md.

---

## Task Completion

**Workflow: Task completed → minimal writes only. Sprint completed → synchronize all documentation.**

Do NOT run the full Document Update Checklist after every task.
Do NOT update changelog.md, project-plan.md, codebase-map.md, or any spec/architecture/business document after a single task.
Run the Document Update Checklist only during Sprint Documentation Sync.

### Mandatory post-task steps (every task)

1. **Apply Doc Checklist, then update `docs/current-state.md`** (1 edit block, in this order):
   a. Apply each item in `docs/current-state.md → Doc Checklist` — update the listed doc files now.
      These are the only doc updates that happen at task level. Do not open the full Document Update Checklist in AGENTS.md.
   b. In `docs/current-state.md`, while Current Task is still the old task:
      - Set **Status** to `Complete — Pending Sprint Doc Sync`
      - Mark completed steps `[x]`
   c. Now promote Next Task → Current Task:
      - Copy **Next Task** → **Current Task** (name, goal)
      - Write upcoming task (already in **Next Task**; look up the one after it in project-plan.md) → **Next Task**
      - Update **Required Context** for the new current task
      - Update **Doc Checklist** → already filtered when this task was set up; replace with filtered list for the new task
      - Set **Status** to `In Progress`

2. **Run verification** for what was changed:

| Changed artifact | Required verification |
|---|---|
| New feature / endpoint | Call the endpoint, confirm expected response |
| Database migration / schema | Run migration, confirm schema matches expected state |
| Config / environment | Start affected service, confirm healthy |
| Network / infrastructure config | Verify connectivity between affected services (e.g. `docker exec serviceA ping serviceB`) |
| Script / utility | Run the script, confirm expected output |
| Documentation only | `python3 docs/script/build_pdf.py docs --lang en -o /tmp/test.pdf` |
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

---

## Sprint Documentation Sync

Run at the end of each sprint (or when `docs/sprint-change-log.md` has accumulated enough Pending entries).

1. Open `docs/sprint-change-log.md`
2. For each entry with **Status: Pending documentation synchronization**:
   - Check the Technical Impact flags
   - Run the relevant sections of the Document Update Checklist below for each affected document
   - Update only the affected documents — do not check unaffected ones
   - Mark the entry **Status: Documentation synchronized — [date]**
3. Run Module Completion Check for any modules touched during the sprint
4. Rebuild PDF: `python3 docs/script/build_pdf.py docs --lang en -o docs/project-documentation-en.pdf`
5. Confirm PDF renders correctly
