#!/usr/bin/env python3
"""
verify_framework.py — Internal consistency audit for the project_starter_v5 framework.

Checks that file references, token budget, document matrix, sprint-sync checklist,
document-purposes coverage, cross-references, type completeness, script type
synchronization, and registry ↔ matrix sync are all in sync.
Run after each Phase before merging.

Usage:
  python3 templates/script/framework/verify_framework.py
  python3 templates/script/framework/verify_framework.py --strict
  python3 templates/script/framework/verify_framework.py --json
"""

import argparse
import json
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from _registry import VALID_TYPES as _REGISTRY_VALID_TYPES

# Script lives at <root>/templates/script/framework/ — framework root is 4 levels up.
FRAMEWORK_ROOT = Path(__file__).resolve().parent.parent.parent.parent

AGENTS_MD       = FRAMEWORK_ROOT / "AGENTS.md"
DOCUMENT_MATRIX = FRAMEWORK_ROOT / "templates/init/document-matrix.md"
SPRINT_SYNC     = FRAMEWORK_ROOT / "templates/sprint-sync.md"
TEMPLATES_DIR   = FRAMEWORK_ROOT / "templates"
PURPOSES_DIR    = FRAMEWORK_ROOT / "guidance"

AGENTS_LINE_BUDGET = 200

TEMPLATE_SUBDIRS = ["architecture", "specs", "business"]

PURPOSES_FILES = {
    "web-app":       "document-purposes-web-app.md",
    "cli-tool":      "document-purposes-cli-tool.md",
    "library":       "document-purposes-library.md",
    "data-pipeline": "document-purposes-data-pipeline.md",
    "ml-pipeline":   "document-purposes-ml-pipeline.md",
    "microservices": "document-purposes-microservices.md",
    "llm-app":       "document-purposes-llm-app.md",
    "iac":           "document-purposes-iac.md",
    "mobile-app":    "document-purposes-mobile-app.md",
}

# Init file slugs to skip when extracting types from AGENTS.md
# (these appear in AGENTS.md but are not project types)
INIT_SKIP = {"document-matrix", "retrofit"}

# Templates that exist for supplementary use but are intentionally absent from
# the R/O/N matrix (project teams use them if needed — they're not type-gated).
TEMPLATE_MATRIX_EXEMPT = {
    # glossary.md and dependencies.md are always-optional utilities created on demand —
    # they are not gated by project type and are registered in the matrix as ⚠️ for all types.
    # They remain exempt from the strict matrix ↔ template check because their Optional status
    # across all 9 types is intentional, not a gap.
    "specs/glossary.md",
    "specs/dependencies.md",
    # spec-review.md and spec-challenge.md are process templates (sprint-end LLM prompts),
    # not project documents — they are intentionally absent from the document matrix.
    "specs/spec-review.md",
    "specs/spec-challenge.md",
}

# Documents legitimately absent from sprint-sync (debug guides and per-run logs
# are updated on demand, not on a sprint cadence).
SPRINT_SYNC_EXEMPT = {
    "pipeline-debug.md",
    "llm-debug.md",
    "experiment-log.md",
    "eval-log.md",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def read_text(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except FileNotFoundError:
        return ""


def parse_matrix(content: str) -> dict[str, dict[str, str]]:
    """Parse document-matrix.md table.

    Returns {doc_name: {type_key: status}} where status is 'R', 'O', or 'N'.
    """
    COL_NORM = {
        "Web App": "web-app", "CLI": "cli-tool", "Library": "library",
        "Data Pipeline": "data-pipeline", "ML Pipeline": "ml-pipeline",
        "Microservices": "microservices", "AI / LLM App": "llm-app",
        "IaC / DevOps": "iac", "Mobile App": "mobile-app",
    }
    SYMBOL_MAP = {"✅": "R", "⚠️": "O", "❌": "N"}

    lines = content.splitlines()
    matrix: dict[str, dict[str, str]] = {}
    headers: list[str] = []

    for line in lines:
        if not line.strip().startswith("|"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if not cells:
            continue
        if cells[0] == "Document":
            headers = [COL_NORM.get(c.strip(), c.strip()) for c in cells[1:]]
            continue
        if all(set(c) <= set("-| ") for c in cells):
            continue
        m = re.match(r"`([^`]+)`", cells[0])
        if not m:
            continue
        doc_name = m.group(1)
        row: dict[str, str] = {}
        for i, col in enumerate(headers):
            if i + 1 < len(cells):
                cell = cells[i + 1].strip()
                status = "N"
                for sym, val in SYMBOL_MAP.items():
                    if sym in cell:
                        status = val
                        break
                row[col] = status
        matrix[doc_name] = row
    return matrix


def find_template(doc_name: str) -> Path | None:
    """Return the first matching template file, including versioned variants (e.g. -v2)."""
    stem = Path(doc_name).stem
    for subdir in TEMPLATE_SUBDIRS:
        d = TEMPLATES_DIR / subdir
        if not d.exists():
            continue
        for f in sorted(d.glob("*.md")):
            if f.name == doc_name or f.stem == stem:
                return f
            if f.stem.startswith(stem + "-") or f.stem.startswith(stem + "_"):
                return f
    return None


def resolve_agent_pointer(path_str: str) -> Path:
    """Resolve an AGENTS.md file reference to its actual location in the framework.

    AGENTS.md paths are written for the user's project, where:
      - `templates/init/web-app.md` → templates/init/web-app.md (framework root)
      - `docs/current-state.md` → templates/current-state.md (template copy)
      - `docs/specs/X.md` → templates/specs/X.md (template copy)
    """
    if path_str.startswith("templates/"):
        return FRAMEWORK_ROOT / path_str
    elif path_str.startswith("docs/"):
        rest = path_str[len("docs/"):]
        return FRAMEWORK_ROOT / "templates" / rest
    return FRAMEWORK_ROOT / path_str


def section_names(content: str) -> set[str]:
    """Return basenames from `### X.md` section headers in a document-purposes file."""
    names: set[str] = set()
    for line in content.splitlines():
        m = re.match(r"^### (.+\.md)$", line.strip())
        if m:
            names.add(Path(m.group(1)).name)
    return names


# ---------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------

def check_stale_pointers() -> list[dict]:
    """Check 1: Every .md file reference in AGENTS.md resolves to an existing file."""
    content = read_text(AGENTS_MD)
    if not content:
        return [_issue("stale-pointer", "error", f"AGENTS.md not found at {AGENTS_MD}")]

    issues = []
    total = 0
    for lineno, line in enumerate(content.splitlines(), start=1):
        for m in re.finditer(r"`([^`]+)`", line):
            val = m.group(1)
            # Only check .md file references (skip dirs, commands, code snippets)
            if not val.endswith(".md"):
                continue
            if not (val.startswith("templates/") or val.startswith("docs/")):
                continue
            total += 1
            resolved = resolve_agent_pointer(val)
            if not resolved.exists():
                issues.append(_issue(
                    "stale-pointer", "fail",
                    f"Line {lineno}: `{val}` → `{resolved.relative_to(FRAMEWORK_ROOT)}` not found"
                ))

    if not issues:
        return [_issue("stale-pointer", "pass",
                       f"All {total} .md references in AGENTS.md resolve")]
    return issues


def check_token_budget() -> list[dict]:
    """Check 2: AGENTS.md line count ≤ 200."""
    content = read_text(AGENTS_MD)
    if not content:
        return [_issue("token-budget", "error", "AGENTS.md not found")]
    count = len(content.splitlines())
    if count > AGENTS_LINE_BUDGET:
        return [_issue("token-budget", "fail",
                       f"AGENTS.md is {count} lines — exceeds {AGENTS_LINE_BUDGET}-line budget "
                       f"by {count - AGENTS_LINE_BUDGET}")]
    return [_issue("token-budget", "pass",
                   f"AGENTS.md is {count} lines (budget: {AGENTS_LINE_BUDGET})")]


def check_matrix_templates(matrix: dict) -> list[dict]:
    """Check 3: Every matrix row has a template; every template has a matrix row."""
    issues = []
    covered: set[Path] = set()

    for doc_name, row in matrix.items():
        tpl = find_template(doc_name)
        if tpl:
            covered.add(tpl)
        elif any(v in ("R", "O") for v in row.values()):
            issues.append(_issue("matrix-templates", "warn",
                                 f"No template file found for `{doc_name}` (R/O for at least one type)"))

    for subdir in TEMPLATE_SUBDIRS:
        d = TEMPLATES_DIR / subdir
        if not d.exists():
            continue
        for f in d.glob("*.md"):
            if f in covered:
                continue
            rel = str(f.relative_to(TEMPLATES_DIR))
            if rel in TEMPLATE_MATRIX_EXEMPT:
                continue
            stem = f.stem
            matched = any(
                stem == Path(doc).stem or stem.startswith(Path(doc).stem + "-")
                for doc in matrix
            )
            if not matched:
                issues.append(_issue("matrix-templates", "warn",
                                     f"Template `{rel}` has no row in document-matrix.md"))

    if not issues:
        return [_issue("matrix-templates", "pass",
                       f"All {len(matrix)} matrix rows have matching templates")]
    return issues


def check_sprint_sync_coverage(matrix: dict) -> list[dict]:
    """Check 4: Every non-exempt R/O doc in the matrix has a sprint-sync checklist item."""
    content = read_text(SPRINT_SYNC)
    if not content:
        return [_issue("sprint-sync", "error", f"sprint-sync.md not found at {SPRINT_SYNC}")]

    mentioned: set[str] = set()
    for line in content.splitlines():
        if not line.strip().startswith("- [ ]"):
            continue
        for m in re.finditer(r"([a-z][a-z0-9-]+\.md)", line):
            mentioned.add(m.group(1))

    issues = []
    for doc_name, row in matrix.items():
        if doc_name in SPRINT_SYNC_EXEMPT:
            continue
        if not any(v in ("R", "O") for v in row.values()):
            continue
        if doc_name not in mentioned:
            issues.append(_issue("sprint-sync", "warn",
                                 f"`{doc_name}` is R/O for at least one type but has no sprint-sync checklist item"))

    if not issues:
        return [_issue("sprint-sync", "pass",
                       "All non-exempt R/O documents have sprint-sync checklist items")]
    return issues


def check_purposes_coverage(matrix: dict) -> list[dict]:
    """Check 5: For each (type, doc) where doc is Required, the doc appears in
    document-purposes-common.md or document-purposes-[type].md as a ### header."""
    common_names = section_names(read_text(PURPOSES_DIR / "document-purposes-common.md"))

    issues = []
    for type_key, purposes_file in PURPOSES_FILES.items():
        path = PURPOSES_DIR / purposes_file
        if not path.exists():
            issues.append(_issue("purposes-coverage", "fail",
                                 f"Missing purposes file: `{purposes_file}`"))
            continue

        type_names = section_names(read_text(path))
        all_covered = common_names | type_names

        for doc_name, row in matrix.items():
            # Only flag Required docs — Optional docs may intentionally live in other type files
            if row.get(type_key) != "R":
                continue
            if doc_name not in all_covered:
                issues.append(_issue("purposes-coverage", "warn",
                                     f"`{doc_name}` is Required for {type_key} but missing "
                                     f"from `{purposes_file}` (and common)"))

    if not issues:
        return [_issue("purposes-coverage", "pass",
                       "All Required documents appear in the matching document-purposes file")]
    return issues


def check_cross_references(matrix: dict) -> list[dict]:
    """Check 6: Every `### X.md` header in document-purposes-*.md files that names
    a known matrix document has a corresponding template file."""
    matrix_docs = set(matrix.keys())
    issues = []
    checked = 0

    all_purposes = [PURPOSES_DIR / "document-purposes-common.md"]
    for f in PURPOSES_FILES.values():
        p = PURPOSES_DIR / f
        if p.exists():
            all_purposes.append(p)

    for path in all_purposes:
        for line in read_text(path).splitlines():
            m = re.match(r"^### (.+\.md)$", line.strip())
            if not m:
                continue
            doc_name = Path(m.group(1)).name
            if doc_name not in matrix_docs:
                continue
            checked += 1
            if not find_template(doc_name):
                issues.append(_issue("cross-ref", "warn",
                                     f"`{path.name}` → `### {doc_name}` but no template file found"))

    if not issues:
        return [_issue("cross-ref", "pass",
                       f"All {checked} document-purposes section headers resolve to template files")]
    return issues


def check_type_completeness() -> list[dict]:
    """Check 7: For every type slug in AGENTS.md's init table:
    - templates/init/[slug].md exists
    - document-purposes-[slug].md exists
    - type is registered in PURPOSES_FILES (so purposes-coverage check covers it)
    """
    content = read_text(AGENTS_MD)
    slugs = sorted({
        m.group(1)
        for m in re.finditer(r'templates/init/([a-z][a-z-]+)\.md', content)
        if m.group(1) not in INIT_SKIP
    })

    issues = []
    for slug in slugs:
        init_path = TEMPLATES_DIR / "init" / f"{slug}.md"
        purposes_path = PURPOSES_DIR / f"document-purposes-{slug}.md"

        if not init_path.exists():
            issues.append(_issue("type-completeness", "fail",
                                 f"`{slug}`: init file missing — templates/init/{slug}.md"))

        if not purposes_path.exists():
            issues.append(_issue("type-completeness", "fail",
                                 f"`{slug}`: purposes file missing — guidance/document-purposes-{slug}.md"))

        if slug not in PURPOSES_FILES:
            issues.append(_issue("type-completeness", "warn",
                                 f"`{slug}` not in PURPOSES_FILES — purposes-coverage check will skip it"))

    if not issues:
        return [_issue("type-completeness", "pass",
                       f"All {len(slugs)} types have init file + purposes file + are registered")]
    return issues


def check_script_type_sync() -> list[dict]:
    """Check 8: scan_codebase.py and verify_docs.py declare the same set of project types."""
    scan_path  = TEMPLATES_DIR / "script" / "scanners" / "scan_codebase.py"
    verify_path = TEMPLATES_DIR / "script" / "validators" / "verify_docs.py"

    for p in (scan_path, verify_path):
        if not p.exists():
            return [_issue("script-type-sync", "error", f"{p.name} not found")]

    # Extract keys from MODULE_VOCAB dict in scan_codebase.py
    scan_types: set[str] = set()
    in_vocab = False
    for line in scan_path.read_text(encoding="utf-8").splitlines():
        if "MODULE_VOCAB" in line and "dict" in line:
            in_vocab = True
        if in_vocab:
            m = re.search(r'"([a-z][a-z-]+)":\s+\(', line)
            if m:
                scan_types.add(m.group(1))
            if line.strip() == "}":
                in_vocab = False

    # VALID_TYPES is now sourced from document-registry.yaml via _registry.py
    verify_types: set[str] = set(_REGISTRY_VALID_TYPES)

    issues = []
    for t in sorted(scan_types - verify_types):
        issues.append(_issue("script-type-sync", "fail",
                             f"`{t}` in scan_codebase.py MODULE_VOCAB but NOT in document-registry.yaml VALID_TYPES"))
    for t in sorted(verify_types - scan_types):
        issues.append(_issue("script-type-sync", "fail",
                             f"`{t}` in document-registry.yaml VALID_TYPES but NOT in scan_codebase.py MODULE_VOCAB"))

    if not issues:
        return [_issue("script-type-sync", "pass",
                       f"scan_codebase.py and document-registry.yaml share the same {len(scan_types)} types: "
                       f"{', '.join(sorted(scan_types))}")]
    return issues


def check_build_pdf_type_sync() -> list[dict]:
    """Check 9: build_pdf.py VALID_PROJECT_TYPES matches PURPOSES_FILES (all 9 types)."""
    build_pdf_path = TEMPLATES_DIR / "script" / "generators" / "build_pdf.py"
    if not build_pdf_path.exists():
        return [_issue("build-pdf-type-sync", "error", "build_pdf.py not found")]

    pdf_types: set[str] = set()
    in_valid = False
    for line in build_pdf_path.read_text(encoding="utf-8").splitlines():
        if re.match(r"\s*VALID_PROJECT_TYPES\s*=\s*\{", line):
            in_valid = True
        if in_valid:
            for m in re.finditer(r'"([a-z][a-z-]+)"', line):
                pdf_types.add(m.group(1))
            if "}" in line and "VALID_PROJECT_TYPES" not in line:
                in_valid = False

    expected = set(PURPOSES_FILES.keys())
    issues = []
    for t in sorted(expected - pdf_types):
        issues.append(_issue("build-pdf-type-sync", "fail",
                             f"`{t}` is a known project type but missing from build_pdf.py VALID_PROJECT_TYPES"))
    for t in sorted(pdf_types - expected):
        issues.append(_issue("build-pdf-type-sync", "warn",
                             f"`{t}` in build_pdf.py VALID_PROJECT_TYPES but not in PURPOSES_FILES"))

    if not issues:
        return [_issue("build-pdf-type-sync", "pass",
                       f"build_pdf.py VALID_PROJECT_TYPES matches all {len(expected)} known project types")]
    return issues


def check_content_coverage() -> list[dict]:
    """Check 10: document-registry.yaml exists with valid schema, and all document
    checker functions exist in verify_content.py."""
    registry_path = FRAMEWORK_ROOT / "document-registry.yaml"
    script_path = TEMPLATES_DIR / "script" / "validators" / "verify_content.py"
    issues = []

    # Validate registry exists and covers all 9 project types
    if not registry_path.exists():
        return [_issue("content-coverage", "error", "document-registry.yaml not found at repo root")]

    registry_text = registry_path.read_text(encoding="utf-8")
    required_fields = {"file", "path", "required_for", "optional_for"}
    expected_types = set(_REGISTRY_VALID_TYPES)
    seen_types: set[str] = set()
    current_doc: str | None = None
    current_fields: set[str] = set()

    for raw_line in registry_text.splitlines():
        line = raw_line.rstrip()
        doc_m = re.match(r'^  ([a-z][a-z0-9-]+):$', line)
        if doc_m:
            if current_doc and not required_fields <= current_fields:
                missing = sorted(required_fields - current_fields)
                issues.append(_issue("content-coverage", "fail",
                                     f"registry entry `{current_doc}` missing fields: {missing}"))
            current_doc = doc_m.group(1)
            current_fields = set()
            continue
        if current_doc and line.startswith('    '):
            field_m = re.match(r'^    ([a-z_]+):\s*(.*)', line)
            if field_m:
                key, val = field_m.group(1), field_m.group(2).strip()
                current_fields.add(key)
                if key in ('required_for', 'optional_for') and val.startswith('['):
                    for t in re.findall(r'[a-z][a-z-]+', val):
                        if t in expected_types:
                            seen_types.add(t)

    # Check last entry
    if current_doc and not required_fields <= current_fields:
        missing = sorted(required_fields - current_fields)
        issues.append(_issue("content-coverage", "fail",
                             f"registry entry `{current_doc}` missing fields: {missing}"))

    for t in sorted(expected_types - seen_types):
        issues.append(_issue("content-coverage", "fail",
                             f"`{t}` not referenced in document-registry.yaml"))

    # Check all document checker functions exist in verify_content.py
    if not script_path.exists():
        issues.append(_issue("content-coverage", "error", "verify_content.py not found"))
        return issues
    text = script_path.read_text(encoding="utf-8")

    required_checkers = {
        "architecture.md":          "check_architecture",
        "quickstart.md":            "check_quickstart",
        "research.md":              "check_research",
        "test-plan.md":             "check_test_plan",
        "api-contract.md":          "check_api_contract",
        "permissions.md":           "check_permissions",
        "data-model.md":            "check_data_model",
        "backend.md":               "check_backend",
        "pipeline-contract.md":     "check_pipeline_contract",
        "pipeline-debug.md":        "check_pipeline_debug",
        "model-contract.md":        "check_model_contract",
        "experiment-log.md":        "check_experiment_log",
        "cli-contract.md":          "check_cli_contract",
        "release-guide.md":         "check_release_guide",
        "public-api.md":            "check_public_api",
        "compatibility-matrix.md":  "check_compatibility_matrix",
        "service-catalog.md":       "check_service_catalog",
        "service-contract.md":      "check_service_contract",
        "llm-contract.md":          "check_llm_contract",
        "eval-spec.md":             "check_eval_spec",
        "prompt-library.md":        "check_prompt_library",
        "topology.md":              "check_topology",
        "runbook.md":               "check_runbook",
        "drift-policy.md":          "check_drift_policy",
        "mobile-contract.md":       "check_mobile_contract",
        "deployment.md":            "check_deployment",
        "database.md":              "check_database",
        "distribution.md":          "check_distribution",
        "frontend.md":              "check_frontend",
        "business-rules.md":        "check_business_rules",
        "business-process.md":      "check_business_process",
        "business-objects.md":      "check_business_objects",
    }
    for doc, func in required_checkers.items():
        if f"def {func}(" not in text:
            issues.append(_issue("content-coverage", "fail",
                                 f"verify_content.py missing checker function `{func}` "
                                 f"for `{doc}`"))

    if not issues:
        return [_issue("content-coverage", "pass",
                       f"verify_content.py covers all {len(expected_types)} project types "
                       f"and all {len(required_checkers)} document checkers")]
    return issues


def check_registry_matrix_sync() -> list[dict]:
    """Check 11: Every entry in document-registry.yaml has a row in document-matrix.md,
    and every matrix row has a registry entry."""
    registry_path = FRAMEWORK_ROOT / "document-registry.yaml"
    issues = []

    if not registry_path.exists():
        return [_issue("registry-matrix-sync", "error", "document-registry.yaml not found")]
    matrix_content = read_text(DOCUMENT_MATRIX)
    if not matrix_content:
        return [_issue("registry-matrix-sync", "error", "document-matrix.md not found")]

    # Registry keys are YAML keys like `architecture:` at 2-space indent
    registry_text = registry_path.read_text(encoding="utf-8")
    registry_keys: set[str] = set()
    for line in registry_text.splitlines():
        m = re.match(r'^  ([a-z][a-z0-9-]+):$', line.rstrip())
        if m:
            registry_keys.add(m.group(1))

    # Matrix rows: `| \`architecture.md\` |` — strip path components and .md suffix
    matrix_keys: set[str] = set()
    for line in matrix_content.splitlines():
        m = re.match(r'^\| `([^`]+)` \|', line)
        if m:
            name = re.sub(r'\.md$', '', Path(m.group(1)).name)
            matrix_keys.add(name)

    in_registry_not_matrix = registry_keys - matrix_keys
    in_matrix_not_registry = matrix_keys - registry_keys

    for key in sorted(in_registry_not_matrix):
        issues.append(_issue("registry-matrix-sync", "warn",
                             f"Registry entry `{key}` has no row in document-matrix.md"))
    for key in sorted(in_matrix_not_registry):
        issues.append(_issue("registry-matrix-sync", "warn",
                             f"Matrix row `{key}.md` has no registry entry"))

    if not issues:
        return [_issue("registry-matrix-sync", "pass",
                       f"Registry and matrix are in sync ({len(registry_keys)} documents)")]
    return issues


# ---------------------------------------------------------------------------
# Issue factory and output
# ---------------------------------------------------------------------------

def _issue(check: str, level: str, msg: str) -> dict:
    return {"check": check, "level": level, "msg": msg}


CHECK_ORDER = [
    "stale-pointer",
    "token-budget",
    "matrix-templates",
    "sprint-sync",
    "purposes-coverage",
    "cross-ref",
    "type-completeness",
    "script-type-sync",
    "build-pdf-type-sync",
    "content-coverage",
    "registry-matrix-sync",
]

CHECK_LABELS = {
    "stale-pointer":        "Stale pointer check          (AGENTS.md .md file refs)",
    "token-budget":         "Token budget check           (AGENTS.md ≤ 200 lines)",
    "matrix-templates":     "Matrix ↔ template consistency",
    "sprint-sync":          "Sprint-sync coverage",
    "purposes-coverage":    "Per-type purposes coverage   (Required docs only)",
    "cross-ref":            "Cross-reference integrity    (document-purposes → templates)",
    "type-completeness":    "Type completeness            (init file + purposes file per type)",
    "script-type-sync":     "Script type sync             (scan_codebase.py ↔ verify_docs.py)",
    "build-pdf-type-sync":  "Build PDF type sync          (build_pdf.py VALID_PROJECT_TYPES)",
    "content-coverage":     "Content coverage             (verify_content.py completeness)",
    "registry-matrix-sync": "Registry ↔ matrix sync      (document-registry.yaml ↔ document-matrix.md)",
}

LEVEL_ICON = {"pass": "✅", "warn": "⚠️ ", "fail": "❌", "error": "❌"}


def print_results(all_issues: list[dict]) -> None:
    by_check: dict[str, list[dict]] = {}
    for issue in all_issues:
        by_check.setdefault(issue["check"], []).append(issue)

    any_fail = any(i["level"] in ("fail", "error") for i in all_issues)
    any_warn = any(i["level"] == "warn" for i in all_issues)

    print(f"\nFramework integrity audit — {FRAMEWORK_ROOT.name}\n")

    for check_key in CHECK_ORDER:
        items = by_check.get(check_key, [])
        if not items:
            print(f"  ⚠️  {CHECK_LABELS[check_key]}  — check did not run")
            continue

        # Determine overall status for this check
        lvls = {i["level"] for i in items}
        if "error" in lvls or "fail" in lvls:
            top_icon = "❌"
        elif "warn" in lvls:
            top_icon = "⚠️ "
        else:
            top_icon = "✅"

        print(f"  {top_icon} {CHECK_LABELS[check_key]}")

        for item in items:
            if item["level"] != "pass":
                icon = LEVEL_ICON.get(item["level"], "?")
                print(f"       {icon} {item['msg']}")

    print()
    if any_fail:
        print("  Result: FAIL — one or more checks failed.")
    elif any_warn:
        print("  Result: PASS with warnings — review ⚠️  items above.")
    else:
        print("  Result: PASS — all checks passed.")
    print()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Audit internal consistency of the project_starter_v5 framework.",
    )
    parser.add_argument(
        "--strict", action="store_true",
        help="Exit with code 1 if any check fails or warns",
    )
    parser.add_argument(
        "--json", action="store_true", dest="json_output",
        help="Output results as JSON",
    )
    args = parser.parse_args()

    matrix_content = read_text(DOCUMENT_MATRIX)
    if not matrix_content:
        print(f"error: document-matrix.md not found at {DOCUMENT_MATRIX}", file=sys.stderr)
        sys.exit(2)

    matrix = parse_matrix(matrix_content)

    all_issues: list[dict] = []
    all_issues += check_stale_pointers()
    all_issues += check_token_budget()
    all_issues += check_matrix_templates(matrix)
    all_issues += check_sprint_sync_coverage(matrix)
    all_issues += check_purposes_coverage(matrix)
    all_issues += check_cross_references(matrix)
    all_issues += check_type_completeness()
    all_issues += check_script_type_sync()
    all_issues += check_build_pdf_type_sync()
    all_issues += check_content_coverage()
    all_issues += check_registry_matrix_sync()

    if args.json_output:
        print(json.dumps(
            {"framework_root": str(FRAMEWORK_ROOT), "results": all_issues},
            ensure_ascii=False, indent=2,
        ))
    else:
        print_results(all_issues)

    if args.strict:
        if any(i["level"] in ("fail", "error", "warn") for i in all_issues):
            sys.exit(1)


if __name__ == "__main__":
    main()
