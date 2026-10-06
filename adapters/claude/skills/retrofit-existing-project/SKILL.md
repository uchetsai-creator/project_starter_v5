---
name: retrofit-existing-project
description: Use when documenting an existing codebase that already has code but no docs — retrofitting project_starter documentation onto it. Walks through reading the codebase, running the module inventory scan, a code quality check, filling in architecture/spec/business docs, module flow files, project status docs, and generating the PDF. Also use (see "Update recheck" section) when a project already retrofitted with this framework gets a framework-update nudge from session-start-hook.sh, to reconcile its docs against what changed upstream. Do NOT use Steps 1-5 for a brand-new project with no code yet — use the per-type init file instead (see AGENTS.md → Project Initialization).
---

# Retrofitting an Existing Project

The goal is to describe what already exists — not to redesign it. Read the codebase first, then fill in the documents to reflect reality.

Do not scan the entire repository at once. Work module by module.

> **Non-default `docs_path`** (e.g. this project is a subdirectory of a larger monorepo and
> its docs can't live at the repo-root `docs/`): set `docs_path` in `.project-starter.yml`
> to the actual location (e.g. `docs/isbg/`) *before* Step 1, and move `docs/script/`
> (validators/generators/scanners copied in by `init.py`) to `{docs_path}/script/` as well —
> it travels with the rest of the docs, not with the root-level framework files
> (`document-registry.yaml`, `workflow-registry.yaml`, `AGENTS.md`, etc., which always stay
> at the repo root regardless of `docs_path`). `orchestrator.py` and the `.githooks/`
> hooks resolve validator paths from `docs_path` at runtime, so once both are moved
> together nothing further is needed.

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

If the output shows `Coverage: 0/0 (100%)` alongside a `[WARN]` about real files existing, do
NOT treat that as "nothing to document" — it means the src layout defeated folder-based
classification (flat files with no subfolders, `--depth` too shallow, or a naming collision with
the Shared/Infrastructure patterns). Re-run with a higher `--depth`, or ask the user to confirm
the actual module boundaries by hand before proceeding.

Classify every folder before proceeding. Do not proceed until the user confirms the inventory is complete.

## Step 1c — Code Quality Check

Read and follow `code-quality-check.md`. Do not proceed to Step 2 until the check is complete and acknowledged by the user.

---

## Step 2 — Fill in architecture and spec documents (describe what exists)

Documents 1–8 are read directly off the code (schema, routes, config, middleware) — low
inference, and the user can spot-check each one against its source file in seconds.
Documents 9–12 require judging *intent* (why a rule exists, why a workflow is shaped this
way, why a technology was chosen) — the same code can be read two different ways, so these
need the user's eyes on each individual item, not just a final skim. Confirmation cost
should track how much was inferred, not be uniform across all twelve.

### 2a — Mechanical documents (draft all, then one combined review)

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

After drafting all of 1–8, show the user one combined summary (one line per document: what
it covers, the source files it was read from) and ask them to confirm it matches reality.
Fix anything they flag before moving to 2b. Do not ask for a per-document sign-off here —
that turns an easy spot-check into thoughtless clicking-through, which buries the review
that 2b actually needs.

### 2b — Inferred documents (confirm one item at a time before finalizing)

9. Draft `docs/business/business-process.md` — describe the actual business workflows.
10. Draft `docs/business/business-objects.md` — describe the actual business entities.
11. Draft `docs/business/business-rules.md` — describe the actual constraints enforced in code.
12. Draft `docs/specs/research.md` — document the technology choices already made and why (if known).

Every individual rule, process step, object, or decision drafted in 9–12 is inference, not
transcription — mark it `[NEEDS CONFIRMATION]` inline as you write it. Then walk the user
through them one at a time (or in small batches of clearly related items), each with the
code it was inferred from, and get one of: confirm, edit, or reject. Only clear the
`[NEEDS CONFIRMATION]` marker once the user has actually responded to that item — an
inference nobody looked at does not belong in these documents. Do not proceed to Step 3
while any `[NEEDS CONFIRMATION]` marker remains in 9–12.

For items 9-12 specifically, do not write the WHY from a blind read — those are exactly
the fields that require understanding intent, not just syntax, and a wrong guess there is
worse than an empty one (same principle as Step 3's `draft_module_flow.py` note below).
Continue to Step 2b before writing the Reason / rationale columns for these four documents.

---

## Step 2b — Infer business logic candidates (confirm with the user)

`scan_codebase.py` and `draft_module_flow.py` pre-fill what is mechanically true (folder
names, class/function names). Business rules, process steps, and design rationale — items
9-12 in Step 2 above — are meaning, not syntax, so a script cannot fill them the same way.
It can, however, point at where the enforcement already lives in code, which is most of the
work of writing a rule down. Run this per module, after Step 1b's inventory is confirmed:

```
python3 docs/script/generators/infer_business_logic.py <module_src_dir> --project-type <type> --docs docs
```

This writes a staging file to `docs/_inferred/[module]/[module]-inferred.md` — never
directly into `business-rules.md`, `business-process.md`, `business-objects.md`, or
`research.md`. Every candidate carries a confidence tier and a source pointer:

- **High** — a guard clause that rejects/raises in code right now. The WHAT is settled;
  only the wording and the Reason column need confirming.
- **Medium** — a comment or docstring near a guard clause implies a reason. May be stale or
  wrong — confirm, don't assume.
- **Low** — a commit message touching the module matches rationale language, with no guard
  clause changed alongside it. Weak evidence; expect most of these to be rejected.

Add `--history` to also mine `git log` for Low-confidence items — slower, and often noisy
this early, so leave it off on the first pass through a large module.

**Confirmation round with the user, one module at a time:**
1. Present the High-confidence items first — for each, ask the user to confirm the
   paraphrase and supply the Reason (the script never invents Reason text).
2. Present Medium, then Low — for each, confirm, edit, or reject. A rejected item is
   simply dropped; do not carry it forward or re-ask in a later round.
3. Only a confirmed item gets transcribed into the real document (`business-rules.md`'s
   BR-XXX table, `business-process.md`'s Decision Points / Exceptions tables,
   `business-objects.md`, or `research.md`'s rationale column) — in the user's confirmed
   wording, not the script's raw paraphrase.
4. Anything with no candidate at all — or confirmed-empty after review — still gets a
   `[NEEDS CLARIFICATION]` entry in the real document, same convention Step 4 already uses
   for `project-requirements.md`. Do not leave a silent gap.
5. Delete `docs/_inferred/[module]/` for a module once every item has been confirmed,
   edited, or rejected — it is a staging area, not a permanent doc, and is not part of
   `document-registry.yaml`.

Do not proceed to Step 3 for a module until its business-logic candidates (if any were
found) have been through this confirmation round.

---

## Step 3 — Fill in module flow files (one module at a time)

Follow the confirmed inventory from Step 1b. For each module:

0. Verify `docs/modules/module-data-flow.md` contains a "## Module Types" section. If missing, copy from `templates/flows/module-data-flow.md` before proceeding.
1. Determine the module type: Feature / Background Job / Pipeline Stage / Shared Utility.
2. Run `python3 docs/script/generators/draft_module_flow.py <module_src_dir> --project-type <type> --docs docs`
   to generate a starting draft at `docs/modules/[module]/[module]-module-data-flow.md` with real
   class/function names pre-filled from static analysis (Python/JS/TS only — other languages get
   a bare template). This replaces starting from an empty file, not the work of writing the
   Overview and Flow Format sections — those still require understanding what the code does.
3. Update `docs/modules/module-data-flow.md` index with the new module entry.
4. Update `docs/codebase-map.md` with the files in this module.

After all modules are documented, re-run the inventory scan to confirm full coverage:
```
python3 docs/script/scanners/scan_codebase.py <src_dir> --docs docs
```
If any ❌ remain, document those modules before proceeding to Step 4.

---

## Step 4 — Fill in project status documents

1. Create `docs/project-requirements.md` — reconstruct from the actual features that exist. Group them into slices (one observable behavior each — `guidance/decomposition/common.md`, nouns from `guidance/decomposition/[project-type].md`) in `## Slices`, and put each FR / AC under its `### SL-n` sub-heading. Mark anything uncertain as [NEEDS CLARIFICATION].
   **Form (required, checked by `templates/script/validators/verify_requirements_form.py --docs docs`):**
   - Every FR states its trigger and response in EARS form (`WHEN / WHILE / IF / WHERE … THE SYSTEM SHALL …`). Rewrite legacy one-line titles such as `使用者登入(LDAP…)` into that form; keep the old wording in the sentence so nothing is lost.
   - Each slice has at least one scenario written as Given / When / Then, taken from the behaviour the code actually has.
   - `## User Journeys`: one sub-heading per role task (who, why, steps, result). Draft these from the existing business-process documents and confirm with the user.
   - If the project uses domain terms, abbreviations or role names that readers need explained, create `docs/specs/glossary.md` as a table of term | meaning rows. Skip it otherwise; the validator only checks the format when the file exists.
   Do not mark the retrofit complete until the validator passes or each remaining failure is listed as a known gap.
2. Create `docs/specs/test-plan.md` from `templates/specs/test-plan.md` — describe the existing testing strategy, tools, and CI gate. If no tests exist, note it as a gap.
3. Create `docs/specs/test-report.md` from `templates/specs/test-report.md` — record the results of any existing test run, or fill in Known Issues / Known Gaps if no tests have been run yet.
4. Create `docs/project-plan.md` — list all modules found. Mark all existing ones as completed. Add any known remaining work as incomplete tasks, one milestone per slice, each task with a `**Covers:**` line naming the FR / AC ids it implements.
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

---

## Update recheck (project already retrofitted, framework has since updated)

Use this instead of Steps 1-5 when session-start-hook.sh's framework-update nudge fires
(`.project-starter.yml`'s `framework_commit` is behind project_starter_v5's upstream
HEAD) — the project already has docs, so the goal is to find what changed upstream and
apply only that, not redo the retrofit from scratch.

1. Confirm with the user this is what they want (the nudge already asks via
   AskUserQuestion before this Skill is invoked).
2. Pull or re-clone the latest project_starter_v5 to a local path.
3. Diff `document-registry.yaml` (new project vs. this project's copy) — new required
   documents, changed `required_sections`, or a document dropped for this project's type
   are the signal for what to add or update. If a document key present in this project's
   copy is missing upstream, do not treat it as a simple deletion: check upstream's
   `related:` fields and `CHANGELOG.md` for whether it was renamed or split into multiple
   new keys. A rename/split means the existing file's content needs to be migrated into
   the new key(s) (copied, then divided by section if split) before the old file is
   removed — deleting it outright loses already-confirmed project content.
4. Diff `templates/script/validators/` and `.githooks/pre-commit` for gates that didn't
   exist at this project's last sync — a new gate silently failing every commit afterward
   is worse than not adopting it yet, so confirm each one with the user before wiring it in.
5. Skim `CHANGELOG.md`'s entries newer than this project's recorded `framework_commit`
   for anything else user-facing (renamed fields, new `.project-starter.yml` keys).
6. Update the specific docs/config the diff above actually calls for — not a full re-run
   of Step 2's document list.
7. Set `framework_commit` in `.project-starter.yml` to the new upstream SHA (`git
   rev-parse HEAD` in the pulled checkout) so the nudge doesn't repeat next session.
