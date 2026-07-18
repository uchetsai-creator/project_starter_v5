"""pdf_allowlist.py — Single source of truth for the PDF file list.

Imported by build_pdf.py.
Edit only this file when adding or removing documents from the PDF.

Chapter structure:
  1. Introduction   — system overview, stakeholders, glossary
  2. Plan           — project plan, changelog
  3. Design         — architecture, data model, interface design
  4. Build          — module flows, codebase map, dependencies
  5. Test           — test plan and report
  6. Deployment     — deployment topology, environment, logging

Rules:
  - Each entry is (section_key, relative_path_from_docs_dir, project_types).
  - section_key must match a key in STRINGS["en"]["sections"] in build_pdf.py.
  - project_types is a frozenset of project type strings. Use the TYPE constants below.
    When build_pdf.py is run with --project-type, only entries whose project_types
    include that type are rendered. Without --project-type, all entries are rendered.
  - Order determines the order documents appear in the PDF.
  - Files under business/*-process.md, business/*-object.md, modules/*/*-module-data-flow.md,
    and specs/prompts/*-prompt.md are auto-scanned — see AUTO_SCAN_TYPES below.
  - log-*.md files are intentionally excluded — dev reference only, not PDF audience.
"""

# ── Project type constants ───────────────────────────────────────────────────
ALL      = frozenset({"web-app", "cli-tool", "library", "data-pipeline",
                      "ml-pipeline", "microservices", "llm-app"})
IAC      = frozenset({"iac"})
MOBILE   = frozenset({"mobile-app"})
ALL9     = ALL | IAC | MOBILE                                # all nine project types
WEB_MS   = frozenset({"web-app", "microservices"})           # user-facing web/services
PIPELINE = frozenset({"data-pipeline", "ml-pipeline"})       # data-oriented pipelines
DIST     = frozenset({"cli-tool", "library"})                # distributed as package/binary
NO_LIB   = ALL - {"library"}                                 # everything except library
INFRA    = ALL - {"cli-tool", "library"}                     # types with hosted deployment

PDF_ALLOWLIST = [
    # ── Chapter 1: Introduction ──────────────────────────────────────────────
    ("introduction", "project-requirements.md",          ALL9),
    ("introduction", "business/business-rules.md",       NO_LIB | MOBILE),
    ("introduction", "business/business-objects.md",     WEB_MS),        # index
    ("introduction", "business/business-process.md",     WEB_MS | frozenset({"cli-tool", "data-pipeline"}) | MOBILE),  # index
    # *-object.md and *-process.md auto-scanned (see AUTO_SCAN_TYPES)
    ("introduction", "specs/glossary.md",                ALL9),

    # ── Chapter 2: Plan ──────────────────────────────────────────────────────
    ("plan",         "project-plan.md",                  ALL9),
    ("plan",         "changelog.md",                     ALL9),

    # ── Chapter 3: Design ────────────────────────────────────────────────────
    ("design",       "architecture/architecture.md",     ALL | MOBILE),  # IaC uses topology.md instead
    ("design",       "architecture/backend.md",          NO_LIB | MOBILE),
    ("design",       "architecture/frontend.md",         WEB_MS | frozenset({"llm-app"}) | MOBILE),
    ("design",       "architecture/database.md",         NO_LIB - {"cli-tool"} | MOBILE),
    ("design",       "architecture/distribution.md",     DIST | MOBILE),
    ("design",       "architecture/topology.md",         IAC),           # IaC-specific
    ("design",       "specs/data-model.md",              NO_LIB - {"cli-tool"} | MOBILE),
    ("design",       "specs/api-contract.md",            WEB_MS | frozenset({"llm-app"}) | MOBILE),
    ("design",       "specs/permissions.md",             WEB_MS | frozenset({"llm-app"}) | MOBILE),
    ("design",       "specs/pipeline-contract.md",       PIPELINE),
    ("design",       "specs/cli-contract.md",            frozenset({"cli-tool"})),
    ("design",       "specs/public-api.md",              frozenset({"library"})),
    ("design",       "specs/model-contract.md",          frozenset({"ml-pipeline"})),
    ("design",       "specs/service-catalog.md",         frozenset({"microservices"})),
    ("design",       "specs/service-contract.md",        frozenset({"microservices"})),
    ("design",       "specs/llm-contract.md",            frozenset({"llm-app"})),
    ("design",       "specs/prompt-library.md",          frozenset({"llm-app"})),  # index; *-prompt.md auto-scanned
    ("design",       "specs/rag-contract.md",            frozenset({"llm-app"})),
    ("design",       "specs/mcp-contract.md",            frozenset({"llm-app"})),
    ("design",       "specs/mobile-contract.md",         MOBILE),        # Mobile-specific
    # specs/research.md excluded until filled. Uncomment once it has real content:
    # ("design",     "specs/research.md",                ALL9),
    # *-module-data-flow.md auto-scanned (ALL + MOBILE types)
    # *-flow.md auto-scanned (ALL + MOBILE types)
    # specs/prompts/*-prompt.md auto-scanned (llm-app only)

    # ── Chapter 4: Build ─────────────────────────────────────────────────────
    ("build",        "modules/module-data-flow.md",      ALL | MOBILE),  # index (section-filtered)
    ("build",        "modules/module-flow.md",           ALL | MOBILE),  # index (section-filtered)
    ("build",        "codebase-map.md",                  ALL9),
    ("build",        "specs/dependencies.md",            ALL9),
    ("build",        "architecture/deployment.md",       INFRA),
    ("build",        "specs/experiment-log.md",          frozenset({"ml-pipeline"})),
    ("build",        "specs/eval-spec.md",               frozenset({"llm-app"})),

    # ── Chapter 5: Test ──────────────────────────────────────────────────────
    ("test",         "specs/test-plan.md",               ALL9),
    ("test",         "specs/test-report.md",             ALL9),
    ("test",         "specs/eval-log.md",                frozenset({"llm-app"})),

    # ── Chapter 6: Deployment ────────────────────────────────────────────────
    ("deployment",   "specs/logging-spec.md",            NO_LIB | MOBILE),
    ("deployment",   "specs/quickstart.md",              ALL9),
    ("deployment",   "specs/release-guide.md",           DIST),
    ("deployment",   "specs/compatibility-matrix.md",    DIST | MOBILE),
    ("deployment",   "specs/runbook.md",                 IAC),           # IaC-specific
    ("deployment",   "specs/drift-policy.md",            IAC),           # IaC-specific
]


# ── Auto-scan patterns ───────────────────────────────────────────────────────
# Glob patterns for files that are auto-discovered (not listed individually above).
# Maps glob pattern → frozenset of project types that should scan it.
# build_pdf.py reads this dict to decide which patterns to run per project type.
AUTO_SCAN_TYPES = {
    "modules/*/*-module-data-flow.md": ALL | MOBILE,   # mobile apps have Screen modules
    "modules/*/*-flow.md":             ALL | MOBILE,
    "business/*-process.md":          WEB_MS | frozenset({"cli-tool", "data-pipeline"}) | MOBILE,
    "business/*-object.md":           WEB_MS,
    "specs/prompts/*-prompt.md":      frozenset({"llm-app"}),
}


# ── Per-file section filter ──────────────────────────────────────────────────
# Only the listed ## headings (and their content) are kept.
# Everything else in the file is stripped before rendering.
PDF_SECTION_FILTER = {
    "modules/module-data-flow.md":  ["## Module Flow Files"],
    "modules/module-flow.md":       ["## Flow Files"],
    "business/business-objects.md": ["## Object Files", "## Relationships"],
    "business/business-process.md": ["## Process Files"],
    # business-rules.md: keep real rule sections, strip placeholder BR-001/BR-002 blocks
    "business/business-rules.md":   ["## Approval Rules", "## Validation Rules",
                                     "## Notification Rules", "## Audit Rules"],
    # prompt-library.md: index only — show active prompts table, hide retired section
    "specs/prompt-library.md":      ["## Active Prompts"],
}
