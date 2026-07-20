# Retrofitting an Existing Project

The goal is to describe what already exists — not to redesign it. Read the codebase first, then fill in the documents to reflect reality.

Do not scan the entire repository at once. Work module by module.

---

## Step 1 — Understand the system (read before writing anything)

1. Read the entry point to understand the overall structure
   (e.g. main file, router, app bootstrap, CLI entry, index)
2. Read the data layer to understand the data model
   (e.g. Prisma schema, SQL DDL, ORM models, migration files)
3. Read one complete vertical slice to understand the layering pattern
   (e.g. controller → service → repository, view → serializer → model, handler → usecase → store)

## Step 1b — Run the module inventory scan

```
python3 docs/script/scanners/scan_codebase.py <src_dir> --project-type <type> --docs docs
```

Review the output with the user:
- ✅ folders are confirmed as documented
- ❌ folders → ask the user: "Is this a module that needs documentation, a shared utility, or something else?"
- — folders → confirm they do not need a flow file

Classify every folder before proceeding. Do not proceed until the user confirms the inventory is complete.

## Step 1c — Code Quality Check

Read and follow `code-quality-check.md`. Do not proceed to Step 2 until the check is complete and acknowledged by the user.

---

## Step 2 — Fill in architecture and spec documents (describe what exists)

1. Create `docs/architecture/architecture.md` — describe the actual components and data flows found.
   Then rebuild the diagram: edit the ` ```plantuml ` block, then run `build_pdf.py`.
2. Create `docs/architecture/backend.md` — describe the actual stack, layering, and module pattern.
   Use the real layer names from the codebase — do not assume Controller/Service/Repository.
   Then rebuild the diagram.
3. Create `docs/architecture/frontend.md` (if applicable). Then rebuild the diagram.
4. Create `docs/architecture/database.md` — describe the actual entities and key relationships.
5. Create `docs/architecture/deployment.md` — describe the actual services, startup flow, and topology.
   Then rebuild the diagram.
6. Create `docs/specs/data-model.md` — fill in from the actual schema file. Then rebuild both diagrams.
7. Create `docs/specs/api-contract.md` — fill in from the actual routes and controllers.
8. Create `docs/specs/permissions.md` — fill in from the actual auth middleware and role logic.
   Then rebuild the use case diagram.
9. Create `docs/business/business-process.md` — describe the actual business workflows.
10. Create `docs/business/business-objects.md` — describe the actual business entities.
11. Create `docs/business/business-rules.md` — describe the actual constraints enforced in code.
12. Create `docs/specs/research.md` — document the technology choices already made and why (if known).

---

## Step 3 — Fill in module flow files (one module at a time)

Follow the confirmed inventory from Step 1b. For each module:

0. Verify `docs/modules/module-data-flow.md` contains a "## Module Types" section. If missing, copy from `templates/flows/module-data-flow-v2.md` before proceeding.
1. Determine the module type: Feature / Background Job / Pipeline Stage / Shared Utility.
2. Create `docs/modules/[module]/[module]-module-data-flow.md` using real function names and file paths.
3. Update `docs/modules/module-data-flow.md` index with the new module entry.
4. Update `docs/codebase-map.md` with the files in this module.

After all modules are documented, re-run the inventory scan to confirm full coverage:
```
python3 docs/script/scanners/scan_codebase.py <src_dir> --docs docs
```
If any ❌ remain, document those modules before proceeding to Step 4.

---

## Step 4 — Fill in project status documents

1. Create `docs/project-requirements.md` — reconstruct from the actual features that exist. Mark anything uncertain as [NEEDS CLARIFICATION].
2. Create `docs/specs/test-plan.md` from `templates/specs/test-plan.md` — describe the existing testing strategy, tools, and CI gate. If no tests exist, note it as a gap.
3. Create `docs/specs/test-report.md` from `templates/specs/test-report.md` — record the results of any existing test run, or fill in Known Issues / Known Gaps if no tests have been run yet.
4. Create `docs/project-plan.md` — list all modules found. Mark all existing ones as completed. Add any known remaining work as incomplete tasks.
5. Create `docs/current-state.md` — set Current Task to the next incomplete item, or write "Documentation retrofit complete — ready for new tasks" if everything is done.

---

## Step 5 — Generate the PDF

Before running `build_pdf.py`, verify flow tables are not empty:
1. Open `docs/modules/module-data-flow.md` — if the Module Flow Files table has only placeholder rows, Step 3 is incomplete.
2. Open `docs/modules/module-flow.md` — same check.

Do not generate the PDF with empty flow index tables.

Before running `build_pdf.py`, confirm `document-registry.yaml` is in your project root:
```bash
ls document-registry.yaml   # must exist; if not: cp /path/to/project_starter_v5/document-registry.yaml .
```

```
python3 docs/script/generators/build_pdf.py docs --lang en -o docs/project-documentation-en.pdf
```
