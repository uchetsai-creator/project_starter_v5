"""
_module_types.py — single source of truth for the module-type taxonomy shared across
scan_codebase.py, verify_module_docs.py, and draft_module_flow.py.

Background: scan_codebase.py's guess_type()/MODULE_VOCAB can label a folder with any of 9
raw types (one per project type, plus the shared-folder bucket). Before this registry existed,
verify_module_docs.py and draft_module_flow.py each hand-rolled their own, separately-maintained
list of "labels I recognize" — and each had silently fallen out of sync with what
scan_codebase.py actually produces:

  - verify_module_docs.py's detect_module_type() only recognized 5 of the 9 raw labels
    ('Pipeline Stage', 'Feature', 'Background Job', 'Shared Utility', 'Resource Group').
    'Command' (cli-tool), 'Namespace' (library), 'Service' (microservices), 'Screen'
    (mobile-app), and 'Shared / Infrastructure' (the actual shared-folder label
    scan_codebase.py emits — note the different wording from 'Shared Utility') all failed to
    match, so check_quality() fell through to module_type='' and reported a confusing
    "Unrecognized module type ''" for any cli-tool/library/microservices/mobile-app module
    scaffolded via `scan_codebase.py --scaffold`.
  - draft_module_flow.py's _FORMAT_A/B/C_LABELS sets covered 8 of the 9 (missing
    'Resource Group' — a documented, tested gap, since module-data-flow.md genuinely has no
    matching format for it yet).

Both consumers should read this registry instead of maintaining their own label list, so a
label scan_codebase.py can produce is guaranteed to resolve the same way everywhere — adding a
new module type means adding one row here, not editing two files that can each independently
forget.

quality_bucket: which of verify_module_docs.py's check_quality() buckets a label is graded
                against. Derived from verify_module_docs.py's own PRIMARY_MODULE_TYPE hint
                (the mapping the original authors already wrote down for "which bucket does
                this project type's modules conceptually belong to"), not guessed.
draft_format:   which module-data-flow.md format letter draft_module_flow.py should use, or
                None when module-data-flow.md has no matching format yet (currently just
                'Resource Group' — see tests/unit/test_draft_module_flow.py's
                test_unmapped_module_type_falls_back_honestly_instead_of_guessing).

Two spellings exist for the same "shared" bucket because two different generators produce it:
scan_codebase.py --scaffold writes the raw guess_type() label 'Shared / Infrastructure', while
draft_module_flow.py normalizes to 'Shared Utility' (its format-C canonical_type). Both must
resolve to the same quality_bucket so a doc is graded the same way regardless of which
generator wrote it.
"""

MODULE_TYPE_REGISTRY: dict[str, dict[str, str | None]] = {
    "Feature":                 {"quality_bucket": "Feature",         "draft_format": "A"},
    "Command":                 {"quality_bucket": "Feature",         "draft_format": "A"},
    "Namespace":                {"quality_bucket": "Shared Utility",  "draft_format": "A"},
    "Service":                  {"quality_bucket": "Feature",         "draft_format": "A"},
    "Screen":                   {"quality_bucket": "Feature",         "draft_format": "A"},
    "Background Job":           {"quality_bucket": "Background Job",  "draft_format": "B"},
    "Shared / Infrastructure":  {"quality_bucket": "Shared Utility",  "draft_format": "C"},
    "Shared Utility":           {"quality_bucket": "Shared Utility",  "draft_format": "C"},
    "Pipeline Stage":           {"quality_bucket": "Pipeline Stage",  "draft_format": "D"},
    "Resource Group":           {"quality_bucket": "Resource Group",  "draft_format": None},
}
