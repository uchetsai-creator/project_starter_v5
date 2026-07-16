# Module Completion Check

Run this check after every task — most of the time the answer will be "no," but the check itself must not be skipped.

Do NOT create or update `[module]-module-data-flow.md` or `[module]-flow.md` during a task
unless the module is 100% complete (all tasks for this module are marked done in project-plan.md).
Creating these files mid-module causes repeated read/write cycles during review. Defer until completion.

* Does completing this task finish all work for its module in docs/project-plan.md?
  * If no: this module is not yet complete. Skip the rest of this file.
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
