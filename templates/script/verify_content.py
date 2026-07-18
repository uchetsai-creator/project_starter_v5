#!/usr/bin/env python3
"""
verify_content.py — Full document content quality gate for project_starter_v4.

For every Required document in the project's declared type, verifies that each
document's required sections contain real content, gated by document × project type.
Documents already covered by verify_logs.py (logging-spec.md) and verify_tests.py
(test-report.md) are skipped here to avoid duplication.

Module flow files (docs/modules/) are delegated to verify_module_docs.py.

Usage:
  python3 docs/script/verify_content.py --project-type TYPE
  python3 docs/script/verify_content.py --project-type TYPE --docs PATH
  python3 docs/script/verify_content.py --project-type TYPE --strict
  python3 docs/script/verify_content.py --project-type TYPE --json

Valid project types: web-app | cli-tool | library | data-pipeline | ml-pipeline |
                     microservices | llm-app | iac | mobile-app
Hybrid types use +: data-pipeline+web-app
"""

import argparse
import json
import os
import re
import subprocess
import sys

VALID_TYPES = [
    'web-app', 'cli-tool', 'library',
    'data-pipeline', 'ml-pipeline', 'microservices', 'llm-app', 'iac', 'mobile-app',
]

# Document name → relative path within the docs/ directory
DOC_PATHS: dict[str, str] = {
    'architecture.md':          'architecture/architecture.md',
    'backend.md':               'architecture/backend.md',
    'topology.md':              'architecture/topology.md',
    'quickstart.md':            'specs/quickstart.md',
    'research.md':              'specs/research.md',
    'test-plan.md':             'specs/test-plan.md',
    'api-contract.md':          'specs/api-contract.md',
    'permissions.md':           'specs/permissions.md',
    'data-model.md':            'specs/data-model.md',
    'pipeline-contract.md':     'specs/pipeline-contract.md',
    'pipeline-debug.md':        'specs/pipeline-debug.md',
    'model-contract.md':        'specs/model-contract.md',
    'experiment-log.md':        'specs/experiment-log.md',
    'cli-contract.md':          'specs/cli-contract.md',
    'release-guide.md':         'specs/release-guide.md',
    'public-api.md':            'specs/public-api.md',
    'compatibility-matrix.md':  'specs/compatibility-matrix.md',
    'service-catalog.md':       'specs/service-catalog.md',
    'service-contract.md':      'specs/service-contract.md',
    'llm-contract.md':          'specs/llm-contract.md',
    'eval-spec.md':             'specs/eval-spec.md',
    'prompt-library.md':        'specs/prompt-library.md',
    'runbook.md':               'specs/runbook.md',
    'drift-policy.md':          'specs/drift-policy.md',
    'mobile-contract.md':       'specs/mobile-contract.md',
    'deployment.md':            'architecture/deployment.md',
    'database.md':              'architecture/database.md',
    'distribution.md':          'architecture/distribution.md',
    'frontend.md':              'architecture/frontend.md',
    'business-rules.md':        'business/business-rules.md',
    'business-process.md':      'business/business-process.md',
    'business-objects.md':      'business/business-objects.md',
}

# Universal documents checked for every project type
UNIVERSAL_DOCS = ['architecture.md', 'quickstart.md', 'research.md', 'test-plan.md']

# Additional Required documents per project type
TYPE_DOCS: dict[str, list[str]] = {
    'web-app':       ['api-contract.md', 'permissions.md', 'data-model.md', 'backend.md',
                      'deployment.md', 'database.md',
                      'business-rules.md', 'business-process.md', 'business-objects.md'],
    'microservices': ['api-contract.md', 'permissions.md', 'data-model.md', 'backend.md',
                      'service-catalog.md', 'service-contract.md',
                      'deployment.md', 'database.md',
                      'business-rules.md', 'business-process.md', 'business-objects.md'],
    'data-pipeline': ['pipeline-contract.md', 'pipeline-debug.md', 'data-model.md', 'backend.md',
                      'deployment.md', 'database.md', 'business-rules.md'],
    'ml-pipeline':   ['pipeline-contract.md', 'pipeline-debug.md', 'data-model.md', 'backend.md',
                      'model-contract.md', 'experiment-log.md',
                      'deployment.md', 'database.md'],
    'cli-tool':      ['cli-contract.md', 'release-guide.md', 'backend.md', 'distribution.md'],
    'library':       ['public-api.md', 'release-guide.md', 'compatibility-matrix.md',
                      'distribution.md'],
    'llm-app':       ['llm-contract.md', 'eval-spec.md', 'prompt-library.md'],
    'iac':           ['topology.md', 'runbook.md', 'drift-policy.md'],
    'mobile-app':    ['mobile-contract.md', 'frontend.md', 'distribution.md'],
}

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _verify_common import _is_placeholder


def _read_file(path: str) -> list[str] | None:
    try:
        with open(path, encoding='utf-8') as fh:
            return fh.read().splitlines()
    except OSError:
        return None


def _non_blank(lines: list[str]) -> list[str]:
    return [ln for ln in lines if ln.strip()]


def _section_body(text: str, header_re: str) -> str | None:
    """Return text from matching section header until next same-or-higher heading."""
    m = re.search(header_re, text, re.IGNORECASE | re.MULTILINE)
    if not m:
        return None
    hashes = re.match(r'^(#+)', m.group(0))
    level = len(hashes.group(1)) if hashes else 1
    after = text[m.end():]
    boundary = re.search(r'(?m)^#{1,' + str(level) + r'}\s', after)
    return after[:boundary.start()] if boundary else after


# ---------------------------------------------------------------------------
# Universal document checkers
# ---------------------------------------------------------------------------

def check_architecture(lines: list[str]) -> list[str]:
    """plantuml component block present; ≥1 real component defined."""
    issues: list[str] = []
    text = '\n'.join(lines)
    uml_m = re.search(r'@startuml(.+?)@enduml', text, re.DOTALL)
    if not uml_m:
        issues.append("plantuml block missing (@startuml / @enduml not found)")
        return issues
    block = uml_m.group(1)
    components = re.findall(r'\[([^\]]+)\]|component\s+"([^"]+)"', block)
    real = [c for pair in components for c in pair if c and not _is_placeholder(c)]
    if not real:
        issues.append("plantuml block: no real component defined (only placeholders or empty)")
    return issues


def check_quickstart(lines: list[str]) -> list[str]:
    """Prerequisites ≥1 real item; ≥1 numbered setup step; Verification step present."""
    issues: list[str] = []
    text = '\n'.join(lines)

    prereq_body = _section_body(text, r'^#+ *Prerequisites?')
    if prereq_body is None:
        issues.append("Prerequisites section missing")
    else:
        items = [ln for ln in prereq_body.splitlines()
                 if re.match(r'\s*[-*]|\s*\d+\.', ln) and ln.strip()]
        if not [it for it in items if not _is_placeholder(it)]:
            issues.append("Prerequisites: no real items (empty or placeholder)")

    numbered = [s for s in re.findall(r'(?m)^\d+\.\s+(.+)', text)
                if s.strip() and not _is_placeholder(s)]
    if not numbered:
        issues.append("No numbered setup steps with real content")

    if not re.search(r'verif|confirm|check|test|validate', text, re.IGNORECASE):
        issues.append("Verification step not documented")

    return issues


def check_research(lines: list[str]) -> list[str]:
    """≥1 decision entry with non-placeholder Rationale; Decision field not blank."""
    issues: list[str] = []
    text = '\n'.join(lines)

    decisions = [v for v in re.findall(r'Decision\s*:\s*(.+)', text)
                 if v.strip() and not _is_placeholder(v)]
    rationales = [v for v in re.findall(r'Rationale\s*:\s*(.+)', text)
                  if v.strip() and not _is_placeholder(v)]

    if not decisions:
        issues.append("No real Decision entries (all blank or placeholder)")
    if not rationales:
        issues.append("No real Rationale entries (all blank or placeholder)")

    return issues


def check_test_plan(lines: list[str]) -> list[str]:
    """Testing Strategy ≥3 lines; ≥1 test level (unit/integration/e2e) with real scope."""
    issues: list[str] = []
    text = '\n'.join(lines)

    body = _section_body(text, r'^#+ *Testing Strategy')
    if body is None:
        issues.append("Testing Strategy section missing")
    else:
        if len(_non_blank(body.splitlines())) < 3:
            issues.append(f"Testing Strategy < 3 lines "
                          f"(found {len(_non_blank(body.splitlines()))})")

    if not re.search(r'\b(unit|integration|e2e|end.to.end|system)\b', text, re.IGNORECASE):
        issues.append("No test level defined (unit / integration / e2e)")

    return issues


# ---------------------------------------------------------------------------
# Web App + Microservices checkers
# ---------------------------------------------------------------------------

def check_api_contract(lines: list[str]) -> list[str]:
    """≥1 endpoint row with real Method + Path; not all placeholder."""
    issues: list[str] = []
    text = '\n'.join(lines)
    rows = re.findall(r'(?m)^\|\s*([A-Z]+)\s*\|\s*(/[^\|\n]*)', text)
    real = [(m, p) for m, p in rows
            if m not in ('Method', 'METHOD')
            and not re.match(r'^[-:]+$', m)
            and not _is_placeholder(m)
            and not _is_placeholder(p)]
    if not real:
        issues.append("No real endpoint rows found (Method + Path not filled)")
    return issues


def check_permissions(lines: list[str]) -> list[str]:
    """Role table ≥1 real role row; ≥1 permission described."""
    issues: list[str] = []
    text = '\n'.join(lines)

    role_rows = re.findall(r'(?m)^\|\s*([^\|\n]+?)\s*\|', text)
    real_roles = [r for r in role_rows
                  if r.strip()
                  and not re.match(r'^[-:]+$', r.strip())
                  and r.strip().lower() not in ('role', 'roles', 'name')
                  and not _is_placeholder(r)]
    if not real_roles:
        issues.append("Role table: no real role entries found")

    if not re.search(r'\b(can|may|read|write|create|update|delete|access|view|manage)\b',
                     text, re.IGNORECASE):
        issues.append("No permission entries documented")

    return issues


def check_data_model(lines: list[str]) -> list[str]:
    """≥1 entity/table defined; plantuml ER block non-empty."""
    issues: list[str] = []
    text = '\n'.join(lines)

    uml_m = re.search(r'@startuml(.+?)@enduml', text, re.DOTALL)
    if not uml_m:
        issues.append("plantuml ER block missing (@startuml / @enduml not found)")
    else:
        block = uml_m.group(1)
        entities = re.findall(r'entity\s+"([^"]+)"|entity\s+(\S+)|class\s+(\S+)', block)
        real = [e for triple in entities for e in triple if e and not _is_placeholder(e)]
        if not real:
            issues.append("plantuml ER block: no entity or table defined")

    return issues


def check_backend(lines: list[str]) -> list[str]:
    """Stack section ≥1 real technology entry."""
    issues: list[str] = []
    text = '\n'.join(lines)

    body = _section_body(text, r'^#+ *Stack')
    if body is None:
        issues.append("Stack section missing")
    else:
        real = [ln for ln in _non_blank(body.splitlines()) if not _is_placeholder(ln)]
        if not real:
            issues.append("Stack section empty or placeholder")

    return issues


# ---------------------------------------------------------------------------
# Data Pipeline + ML Pipeline checkers
# ---------------------------------------------------------------------------

def check_pipeline_contract(lines: list[str]) -> list[str]:
    """Cross-stage table ≥1 data row with non-placeholder Input + Output formats."""
    issues: list[str] = []
    text = '\n'.join(lines)

    rows = re.findall(
        r'(?m)^\|\s*([^\|\n]+?)\s*\|\s*([^\|\n]+?)\s*\|\s*([^\|\n]+?)\s*\|', text
    )
    real = [
        r for r in rows
        if not all(re.match(r'^[-:]+$', c.strip()) for c in r)
        and r[0].strip().lower() not in ('stage', 'name', 'module', 'document', 'step')
        and not _is_placeholder(r[0]) and r[0].strip()
        and not _is_placeholder(r[1]) and r[1].strip()
        and not _is_placeholder(r[2]) and r[2].strip()
    ]
    if not real:
        issues.append("Cross-stage table: no data rows with non-placeholder Input/Output formats")

    return issues


def check_pipeline_debug(lines: list[str]) -> list[str]:
    """≥1 debug scenario with non-placeholder Symptom and Root cause."""
    issues: list[str] = []
    text = '\n'.join(lines)

    symptoms = [v for v in re.findall(r'Symptom\s*:\s*(.+)', text)
                if v.strip() and not _is_placeholder(v)]
    causes = [v for v in re.findall(r'Root\s*[Cc]ause\s*:\s*(.+)', text)
              if v.strip() and not _is_placeholder(v)]

    if not symptoms:
        issues.append("No debug scenarios with real Symptom documented")
    if not causes:
        issues.append("No debug scenarios with real Root cause documented")

    return issues


# ---------------------------------------------------------------------------
# ML Pipeline checkers
# ---------------------------------------------------------------------------

def check_model_contract(lines: list[str]) -> list[str]:
    """Input schema ≥1 real field; Output format non-placeholder; ≥1 production threshold."""
    issues: list[str] = []
    text = '\n'.join(lines)

    input_body = _section_body(text, r'^#+ *(Input|Input\s+Schema)')
    if input_body is None:
        issues.append("Input schema section missing")
    else:
        fields = re.findall(r'(?m)^\|\s*(\S[^\|]+?)\s*\|', input_body)
        real_fields = [f for f in fields
                       if f.strip()
                       and not re.match(r'^[-:]+$', f.strip())
                       and f.strip().lower() not in ('field', 'name', 'feature', 'column')
                       and not _is_placeholder(f)]
        if not real_fields:
            issues.append("Input schema: no real field entries found")

    output_body = _section_body(text, r'^#+ *(Output|Output\s+Format)')
    if output_body is None:
        issues.append("Output format section missing")
    else:
        real = [ln for ln in _non_blank(output_body.splitlines()) if not _is_placeholder(ln)]
        if not real:
            issues.append("Output format section empty or placeholder")

    if not re.search(
        r'threshold|accuracy|f1|precision|recall|auc|score\s*[><=]', text, re.IGNORECASE
    ):
        issues.append("No production threshold defined")

    return issues


def check_experiment_log(lines: list[str]) -> list[str]:
    """≥1 experiment entry with non-placeholder Hypothesis and Result."""
    issues: list[str] = []
    text = '\n'.join(lines)

    hyps = [v for v in re.findall(r'Hypothesis\s*:\s*(.+)', text)
            if v.strip() and not _is_placeholder(v)]
    results = [v for v in re.findall(r'Result\s*:\s*(.+)', text)
               if v.strip() and not _is_placeholder(v)]

    if not hyps:
        issues.append("No experiment entries with real Hypothesis")
    if not results:
        issues.append("No experiment entries with real Result")

    return issues


# ---------------------------------------------------------------------------
# CLI Tool checkers
# ---------------------------------------------------------------------------

def check_cli_contract(lines: list[str]) -> list[str]:
    """≥1 subcommand with non-placeholder description; ≥1 flag or argument documented."""
    issues: list[str] = []
    text = '\n'.join(lines)

    _EXCLUDE_HEADERS = {
        'usage', 'options', 'flags', 'arguments', 'examples',
        'global', 'commands', 'subcommands', 'overview', 'description',
    }

    section_names = [s for s in re.findall(r'(?m)^#+ +(\w[\w -]*)$', text)
                     if s.lower().strip() not in _EXCLUDE_HEADERS
                     and not _is_placeholder(s)]

    if not section_names:
        # Try table format: | subcommand | description |
        rows = re.findall(r'(?m)^\|\s*(\w[\w-]*)\s*\|\s*([^\|\n]+)', text)
        real = [r for r in rows
                if r[0].lower() not in ('subcommand', 'command', 'name')
                and not _is_placeholder(r[0])
                and not _is_placeholder(r[1])
                and r[1].strip()]
        if not real:
            issues.append("No real subcommands defined")

    if not re.search(r'--\w+|-[a-zA-Z]\b|\[flags?\]|\[options?\]', text):
        issues.append("No flags or arguments documented")

    return issues


def check_release_guide(lines: list[str]) -> list[str]:
    """Versioning policy section non-empty; ≥1 publish step documented."""
    issues: list[str] = []
    text = '\n'.join(lines)

    body = _section_body(text, r'^#+ *(Versioning|Version\s+Policy)')
    if body is None:
        issues.append("Versioning policy section missing")
    else:
        real = [ln for ln in _non_blank(body.splitlines()) if not _is_placeholder(ln)]
        if not real:
            issues.append("Versioning policy section empty")

    if not re.search(
        r'\b(publish|release|deploy|npm publish|pip|upload|cargo publish|push tag|git tag)\b',
        text, re.IGNORECASE,
    ):
        issues.append("No publish steps documented")

    return issues


# ---------------------------------------------------------------------------
# Library / SDK checkers
# ---------------------------------------------------------------------------

def check_public_api(lines: list[str]) -> list[str]:
    """≥1 public function or class with real signature (not placeholder)."""
    issues: list[str] = []
    text = '\n'.join(lines)

    func_patterns = [
        r'def\s+([a-zA-Z_]\w*)\s*\(',
        r'function\s+([a-zA-Z_]\w*)\s*\(',
        r'(?m)^### `([a-zA-Z_]\w*)[\(`]',
        r'`([a-zA-Z_]\w*)\s*\(',
        r'class\s+([A-Z][a-zA-Z_]\w*)',
    ]
    real: list[str] = []
    for pat in func_patterns:
        real.extend(m for m in re.findall(pat, text) if not _is_placeholder(m))

    if not real:
        issues.append("No real public function or class signatures found (all placeholder or missing)")

    return issues


def check_compatibility_matrix(lines: list[str]) -> list[str]:
    """≥1 runtime version row with Support status."""
    issues: list[str] = []
    text = '\n'.join(lines)

    rows = re.findall(r'(?m)^\|\s*([^\|\n]+?)\s*\|\s*([^\|\n]+?)\s*\|', text)
    real = [
        r for r in rows
        if not all(re.match(r'^[-:]+$', c.strip()) for c in r)
        and r[0].strip().lower() not in ('version', 'runtime', 'environment', 'language',
                                          'platform', 'python', 'node')
        and not _is_placeholder(r[0]) and r[0].strip()
    ]
    if not real:
        issues.append("No runtime version rows with Support status found")

    return issues


# ---------------------------------------------------------------------------
# Microservices checkers
# ---------------------------------------------------------------------------

def check_service_catalog(lines: list[str]) -> list[str]:
    """≥1 service row with real name, port, and owner."""
    issues: list[str] = []
    text = '\n'.join(lines)

    rows = re.findall(
        r'(?m)^\|\s*([^\|\n]+?)\s*\|\s*([^\|\n]+?)\s*\|\s*([^\|\n]+?)\s*\|', text
    )
    real = [
        r for r in rows
        if not all(re.match(r'^[-:]+$', c.strip()) for c in r)
        and r[0].strip().lower() not in ('service', 'name')
        and not _is_placeholder(r[0]) and r[0].strip()
    ]
    if not real:
        issues.append("No service entries with real name, port, and owner found")

    return issues


def check_service_contract(lines: list[str]) -> list[str]:
    """≥1 inter-service endpoint or event documented."""
    issues: list[str] = []
    text = '\n'.join(lines)

    has_content = bool(
        re.search(r'(?m)^\|\s*[A-Z]+\s*\|\s*/', text)
        or re.search(r'\bevent\b|\btopic\b|\bqueue\b|\bmessage\b', text, re.IGNORECASE)
        or re.search(r'(?m)^#+ *[A-Z][a-zA-Z ]+\s*(→|->|calls?|invokes?|triggers?)', text)
    )
    if not has_content:
        issues.append("No inter-service endpoints or events documented")

    return issues


# ---------------------------------------------------------------------------
# AI / LLM App checkers
# ---------------------------------------------------------------------------

def check_llm_contract(lines: list[str]) -> list[str]:
    """Model name non-placeholder; System Prompt ≥1 real line; ≥1 parameter defined."""
    issues: list[str] = []
    text = '\n'.join(lines)

    model_m = re.search(r'Model\s*:\s*(.+)', text)
    if not model_m or not model_m.group(1).strip() or _is_placeholder(model_m.group(1)):
        issues.append("Model name empty or placeholder")

    sys_body = _section_body(text, r'^#+ *System\s+Prompt')
    if sys_body is None:
        issues.append("System Prompt section missing")
    else:
        real = [ln for ln in _non_blank(sys_body.splitlines()) if not _is_placeholder(ln)]
        if not real:
            issues.append("System Prompt section empty or placeholder")

    if not re.search(
        r'\b(temperature|max_tokens|top_p|frequency_penalty|presence_penalty|seed|top_k)\b',
        text, re.IGNORECASE,
    ):
        issues.append("No LLM parameters defined")

    return issues


def check_eval_spec(lines: list[str]) -> list[str]:
    """≥1 evaluation criterion with scoring rubric; ≥1 test case."""
    issues: list[str] = []
    text = '\n'.join(lines)

    crit_body = _section_body(text, r'^#+ *(Criteria|Evaluation\s+Criteria|Metrics)')
    if crit_body is None:
        issues.append("Evaluation criteria section missing")
    else:
        real = [ln for ln in _non_blank(crit_body.splitlines()) if not _is_placeholder(ln)]
        if not real:
            issues.append("Evaluation criteria section empty or placeholder")

    if not re.search(r'\b(test\s*case|scenario|example\s*input|sample\s*input)\b',
                     text, re.IGNORECASE):
        issues.append("No test cases documented")

    return issues


def check_prompt_library(lines: list[str]) -> list[str]:
    """≥1 prompt entry (name + file reference)."""
    issues: list[str] = []
    text = '\n'.join(lines)

    rows = re.findall(r'(?m)^\|\s*([^\|\n]+?)\s*\|\s*([^\|\n]+?)\s*\|', text)
    real = [
        r for r in rows
        if not all(re.match(r'^[-:]+$', c.strip()) for c in r)
        and r[0].strip().lower() not in ('name', 'prompt', 'id')
        and not _is_placeholder(r[0]) and r[0].strip()
    ]
    has_links = bool(re.search(r'\[.+\]\(.+-prompt\.md\)', text))

    if not real and not has_links:
        issues.append("No prompt entries documented (name + file reference)")

    return issues


# ---------------------------------------------------------------------------
# IaC / DevOps checkers
# ---------------------------------------------------------------------------

def check_topology(lines: list[str]) -> list[str]:
    """plantuml block non-empty; ≥1 real resource defined."""
    issues: list[str] = []
    text = '\n'.join(lines)

    uml_m = re.search(r'@startuml(.+?)@enduml', text, re.DOTALL)
    if not uml_m:
        issues.append("plantuml block missing (@startuml / @enduml not found)")
        return issues

    block = uml_m.group(1)
    resources = re.findall(
        r'(?:node|cloud|database|storage|server|component|package|rectangle|queue)\s+"([^"]+)"',
        block,
    )
    real = [r for r in resources if not _is_placeholder(r)]
    if not real:
        issues.append("plantuml block: no real resource defined")

    return issues


def check_runbook(lines: list[str]) -> list[str]:
    """≥1 runbook entry with Steps non-empty."""
    issues: list[str] = []
    text = '\n'.join(lines)

    ordered = [s for s in re.findall(r'(?m)^\d+\.\s+(.+)', text)
               if s.strip() and not _is_placeholder(s)]
    steps_vals = [v for v in re.findall(r'Steps?\s*:\s*(.+)', text)
                  if v.strip() and not _is_placeholder(v)]

    if not ordered and not steps_vals:
        issues.append("No runbook entries with real Steps documented")

    return issues


def check_drift_policy(lines: list[str]) -> list[str]:
    """Detection cadence non-placeholder; Remediation SLA defined."""
    issues: list[str] = []
    text = '\n'.join(lines)

    cadence_m = re.search(
        r'(?:Detection\s+Cadence|Cadence|Scan\s+Frequency)\s*:\s*(.+)', text, re.IGNORECASE
    )
    if not cadence_m or not cadence_m.group(1).strip() or _is_placeholder(cadence_m.group(1)):
        issues.append("Detection cadence not defined or placeholder")

    sla_m = re.search(
        r'(?:Remediation\s+SLA|SLA|Response\s+Time|Remediation\s+Time)\s*:\s*(.+)',
        text, re.IGNORECASE,
    )
    if not sla_m or not sla_m.group(1).strip() or _is_placeholder(sla_m.group(1)):
        issues.append("Remediation SLA not defined or placeholder")

    return issues


# ---------------------------------------------------------------------------
# Mobile App checkers
# ---------------------------------------------------------------------------

def check_mobile_contract(lines: list[str]) -> list[str]:
    """≥1 screen with non-placeholder title; Navigation structure described."""
    issues: list[str] = []
    text = '\n'.join(lines)

    _SKIP = {'overview', 'navigation', 'screens', 'introduction', 'summary',
              'permissions', 'platform', 'push notifications', 'deep linking',
              'mobile contract', 'contract'}

    section_names = [s.strip() for s in re.findall(r'(?m)^#+ *(.+)', text)
                     if s.strip().lower() not in _SKIP
                     and not _is_placeholder(s)
                     and len(s.strip()) > 2]

    if not section_names:
        rows = re.findall(r'(?m)^\|\s*([^\|\n]+?)\s*\|\s*([^\|\n]+?)\s*\|', text)
        screen_rows = [r for r in rows
                       if r[0].strip().lower() not in ('screen', 'name', 'page')
                       and not re.match(r'^[-:]+$', r[0].strip())
                       and not _is_placeholder(r[0]) and r[0].strip()]
        if not screen_rows:
            issues.append("No real screens defined")

    if not re.search(
        r'navigation|nav\s+flow|tab\s*bar|bottom\s*nav|drawer|stack\s*navigator|back\s*stack',
        text, re.IGNORECASE,
    ):
        issues.append("Navigation structure not described")

    return issues


# ---------------------------------------------------------------------------
# Architecture: Deployment, Database, Distribution, Frontend
# ---------------------------------------------------------------------------

def check_deployment(lines: list[str]) -> list[str]:
    """Services table ≥1 real row; Environment Variables ≥1 real entry."""
    issues: list[str] = []
    text = '\n'.join(lines)

    # Services table — look for non-header, non-placeholder rows
    rows = re.findall(
        r'(?m)^\|\s*([^\|\n]+?)\s*\|\s*([^\|\n]+?)\s*\|\s*([^\|\n]+?)\s*\|', text
    )
    real_services = [
        r for r in rows
        if not all(re.match(r'^[-:]+$', c.strip()) for c in r)
        and r[0].strip().lower() not in ('service', 'name')
        and not _is_placeholder(r[0]) and r[0].strip()
        and not r[0].strip().startswith('[')
    ]
    if not real_services:
        issues.append("Services table: no real service rows (all placeholder or missing)")

    # Environment Variables — look for ALL_CAPS var names or table rows
    env_body = _section_body(text, r'^## Environment Variables')
    if env_body is None:
        issues.append("Environment Variables section missing")
    else:
        env_vars = [v for v in re.findall(r'\b[A-Z][A-Z0-9_]{2,}\b', env_body)
                    if not _is_placeholder(v)]
        if not env_vars:
            issues.append("Environment Variables: no real env var entries")

    return issues


def check_database(lines: list[str]) -> list[str]:
    """Database Engine non-placeholder; Main Entities ≥2 real lines of content."""
    issues: list[str] = []
    text = '\n'.join(lines)

    engine_body = _section_body(text, r'^## Database Engine')
    if engine_body is None:
        issues.append("Database Engine section missing")
    else:
        real = [ln for ln in _non_blank(engine_body.splitlines()) if not _is_placeholder(ln)]
        if not real:
            issues.append("Database Engine section empty or placeholder")

    entities_body = _section_body(text, r'^## Main Entities')
    if entities_body is None:
        issues.append("Main Entities section missing")
    else:
        real = [ln for ln in _non_blank(entities_body.splitlines()) if not _is_placeholder(ln)]
        if len(real) < 2:
            issues.append(
                f"Main Entities: fewer than 2 real lines of content (found {len(real)})"
            )

    return issues


def check_distribution(lines: list[str]) -> list[str]:
    """Package name non-placeholder; publish command documented."""
    issues: list[str] = []
    text = '\n'.join(lines)

    pkg_m = re.search(r'Package name\s*\|\s*(.+)', text)
    if not pkg_m or not pkg_m.group(1).strip() or _is_placeholder(pkg_m.group(1)):
        issues.append("Package name empty or placeholder")

    if not re.search(
        r'\b(npm publish|pip|twine|cargo publish|gem push|pack|release)\b',
        text, re.IGNORECASE,
    ):
        issues.append("No publish command documented")

    return issues


def check_frontend(lines: list[str]) -> list[str]:
    """Stack section non-placeholder; Page / Screen Structure described."""
    issues: list[str] = []
    text = '\n'.join(lines)

    stack_body = _section_body(text, r'^## Stack')
    if stack_body is None:
        issues.append("Stack section missing")
    else:
        real = [ln for ln in _non_blank(stack_body.splitlines()) if not _is_placeholder(ln)]
        if not real:
            issues.append("Stack section empty or placeholder")

    page_body = _section_body(
        text, r'^## (?:Page\s*/\s*Screen Structure|Screen Structure|Pages?)'
    )
    if page_body is None:
        issues.append("Page / Screen Structure section missing")
    else:
        real = [ln for ln in _non_blank(page_body.splitlines()) if not _is_placeholder(ln)]
        if not real:
            issues.append("Page / Screen Structure section empty or placeholder")

    return issues


# ---------------------------------------------------------------------------
# Business: Rules, Process, Objects
# ---------------------------------------------------------------------------

def check_business_rules(lines: list[str]) -> list[str]:
    """≥1 BR-XXX rule with non-placeholder Description and Enforcement Layer."""
    issues: list[str] = []
    text = '\n'.join(lines)

    if not re.search(r'BR-\d+', text):
        issues.append("No business rule entries (BR-XXX format) found")
        return issues

    descriptions = [v for v in re.findall(r'\*\*Description\*\*\s*\|\s*(.+)', text)
                    if v.strip() and not _is_placeholder(v)]
    enforcement = [v for v in re.findall(r'\*\*Enforcement Layer\*\*\s*\|\s*(.+)', text)
                   if v.strip() and not _is_placeholder(v)]

    if not descriptions:
        issues.append("Business rules: Description field empty or placeholder in all rules")
    if not enforcement:
        issues.append("Business rules: Enforcement Layer field empty or placeholder in all rules")

    return issues


def check_business_process(lines: list[str]) -> list[str]:
    """Process Files table ≥1 real process row (non-placeholder)."""
    issues: list[str] = []
    text = '\n'.join(lines)

    # Rows in the Process Files table — real entries have a *-process.md link or real name
    rows = re.findall(r'(?m)^\|\s*([^\|\n]+?)\s*\|\s*([^\|\n]+?)\s*\|', text)
    real_rows = [
        r for r in rows
        if not all(re.match(r'^[-:]+$', c.strip()) for c in r)
        and r[0].strip().lower() not in ('process', 'name')
        and not re.match(r'^[-:]+$', r[0].strip())
        and not _is_placeholder(r[0]) and r[0].strip()
        and not r[0].strip().startswith('[')
    ]
    if not real_rows:
        issues.append("Process Files table: no real process entries found")

    return issues


def check_business_objects(lines: list[str]) -> list[str]:
    """Object Files table ≥1 real object entry (non-placeholder)."""
    issues: list[str] = []
    text = '\n'.join(lines)

    rows = re.findall(r'(?m)^\|\s*([^\|\n]+?)\s*\|\s*([^\|\n]+?)\s*\|', text)
    real_rows = [
        r for r in rows
        if not all(re.match(r'^[-:]+$', c.strip()) for c in r)
        and r[0].strip().lower() not in ('object', 'name', 'relates to')
        and not re.match(r'^[-:]+$', r[0].strip())
        and not _is_placeholder(r[0]) and r[0].strip()
        and not r[0].strip().startswith('[')
    ]
    if not real_rows:
        issues.append("Object Files table: no real business object entries found")

    return issues


# ---------------------------------------------------------------------------
# Checker registry
# ---------------------------------------------------------------------------

CHECKERS: dict[str, object] = {
    'architecture.md':          check_architecture,
    'quickstart.md':            check_quickstart,
    'research.md':              check_research,
    'test-plan.md':             check_test_plan,
    'api-contract.md':          check_api_contract,
    'permissions.md':           check_permissions,
    'data-model.md':            check_data_model,
    'backend.md':               check_backend,
    'pipeline-contract.md':     check_pipeline_contract,
    'pipeline-debug.md':        check_pipeline_debug,
    'model-contract.md':        check_model_contract,
    'experiment-log.md':        check_experiment_log,
    'cli-contract.md':          check_cli_contract,
    'release-guide.md':         check_release_guide,
    'public-api.md':            check_public_api,
    'compatibility-matrix.md':  check_compatibility_matrix,
    'service-catalog.md':       check_service_catalog,
    'service-contract.md':      check_service_contract,
    'llm-contract.md':          check_llm_contract,
    'eval-spec.md':             check_eval_spec,
    'prompt-library.md':        check_prompt_library,
    'topology.md':              check_topology,
    'runbook.md':               check_runbook,
    'drift-policy.md':          check_drift_policy,
    'mobile-contract.md':       check_mobile_contract,
    'deployment.md':            check_deployment,
    'database.md':              check_database,
    'distribution.md':          check_distribution,
    'frontend.md':              check_frontend,
    'business-rules.md':        check_business_rules,
    'business-process.md':      check_business_process,
    'business-objects.md':      check_business_objects,
}


# ---------------------------------------------------------------------------
# Module flow delegation
# ---------------------------------------------------------------------------

def _find_module_docs_script(script_dir: str) -> str | None:
    for candidate in (
        os.path.join(script_dir, 'verify_module_docs.py'),
        os.path.join(os.path.dirname(script_dir), 'script', 'verify_module_docs.py'),
    ):
        if os.path.isfile(candidate):
            return candidate
    return None


def run_module_docs(project_type: str, docs_dir: str, script_dir: str) -> list[dict]:
    """Delegate module flow checks to verify_module_docs.py; return module result list."""
    script = _find_module_docs_script(script_dir)
    if not script:
        return []
    try:
        result = subprocess.run(
            [sys.executable, script, '--project-type', project_type,
             '--docs', docs_dir, '--json'],
            capture_output=True, text=True, timeout=30,
        )
        data = json.loads(result.stdout)
        return data.get('modules', [])
    except (json.JSONDecodeError, subprocess.TimeoutExpired, OSError, ValueError):
        return []


# ---------------------------------------------------------------------------
# Core audit
# ---------------------------------------------------------------------------

def get_docs_for_types(project_types: list[str]) -> list[str]:
    seen: set[str] = set()
    docs: list[str] = []
    for d in UNIVERSAL_DOCS:
        if d not in seen:
            docs.append(d)
            seen.add(d)
    for t in project_types:
        for d in TYPE_DOCS.get(t, []):
            if d not in seen:
                docs.append(d)
                seen.add(d)
    return docs


def audit(
    project_types: list[str], docs_dir: str, script_dir: str,
) -> tuple[list[dict], list[dict]]:
    """Audit all Required documents and module flow files.

    Returns (doc_results, module_results).
    doc_results: [{name, path, present, quality, issues}]
    module_results: [{name, module_type, flow_file_present, quality, issues, ...}]
    """
    doc_results: list[dict] = []

    for doc_name in get_docs_for_types(project_types):
        rel = DOC_PATHS.get(doc_name, f'specs/{doc_name}')
        abs_path = os.path.join(docs_dir, rel)
        present = os.path.isfile(abs_path)

        if not present:
            doc_results.append({
                'name': doc_name,
                'path': abs_path,
                'present': False,
                'quality': None,
                'issues': [],
            })
            continue

        lines = _read_file(abs_path) or []
        checker = CHECKERS.get(doc_name)
        if checker:
            issues = checker(lines)  # type: ignore[call-arg]
            # Mobile-app extra rule for architecture.md: require ≥1 screen component
            if doc_name == 'architecture.md' and 'mobile-app' in project_types and not issues:
                text = '\n'.join(lines)
                uml_m = re.search(r'@startuml(.+?)@enduml', text, re.DOTALL)
                if uml_m:
                    block = uml_m.group(1)
                    screen_comps = re.findall(
                        r'\[(.*?(?:screen|view|page|activity|fragment).*?)\]',
                        block, re.IGNORECASE,
                    )
                    if not screen_comps:
                        issues.append(
                            "Mobile App: no screen/view component in architecture diagram"
                        )
            quality: str | None = 'pass' if not issues else 'fail'
        else:
            quality = 'unknown'
            issues = []

        doc_results.append({
            'name': doc_name,
            'path': abs_path,
            'present': True,
            'quality': quality,
            'issues': issues,
        })

    module_results = run_module_docs('+'.join(project_types), docs_dir, script_dir)
    return doc_results, module_results


# ---------------------------------------------------------------------------
# Output
# ---------------------------------------------------------------------------

def print_results(
    doc_results: list[dict], module_results: list[dict], project_type: str,
) -> None:
    SEP = '─' * 68
    print(f"\nDocument Content Quality — {project_type}")
    print(SEP)
    print(f"{'Document':<30} {'Required':<12} Quality")
    print(SEP)

    for r in doc_results:
        name = r['name'][:28]
        if not r['present']:
            present_col = '❌ Missing'
            quality_col = '—'
        else:
            present_col = '✅'
            if r['quality'] == 'pass':
                quality_col = '✅  Fully filled'
            elif r['quality'] == 'unknown':
                quality_col = '⚠️  No checker available'
            else:
                first = r['issues'][0] if r['issues'] else 'issues found'
                quality_col = f"⚠️  {first}"

        print(f"{name:<30} {present_col:<12} {quality_col}")

        for issue in (r['issues'][1:] if r.get('present') and r['quality'] == 'fail' else []):
            print(f"{'':30} {'':12} ⚠️  {issue}")

    if module_results:
        print()
        for m in module_results:
            mod_name = f"modules/{m['name']}"[:28]
            flow_present = m.get('flow_file_present', False)
            if not flow_present:
                present_col = '❌ Missing'
                quality_col = '—'
            else:
                present_col = '✅'
                type_lbl = m.get('module_type') or m.get('detected_type') or 'Unknown'
                q = m.get('quality')
                if q == 'pass':
                    quality_col = f"✅  Fully filled  ({type_lbl})"
                elif q == 'unknown':
                    quality_col = f"⚠️  Unknown module type"
                else:
                    first = m['issues'][0] if m.get('issues') else 'issues found'
                    quality_col = f"⚠️  {first}  ({type_lbl})"

            print(f"{mod_name:<30} {present_col:<12} {quality_col}")

            for issue in (m.get('issues', [])[1:] if flow_present and m.get('quality') == 'fail' else []):
                print(f"{'':30} {'':12} ⚠️  {issue}")

    print()

    total_docs = len(doc_results)
    present_docs = sum(1 for r in doc_results if r['present'])
    filled_docs = sum(1 for r in doc_results if r['present'] and r['quality'] == 'pass')

    print(f"Documents  : {present_docs} / {total_docs} present")
    print(f"Quality    : {filled_docs} / {present_docs} existing documents fully filled")

    if module_results:
        total_mods = len(module_results)
        present_mods = sum(1 for m in module_results if m.get('flow_file_present'))
        filled_mods = sum(
            1 for m in module_results
            if m.get('flow_file_present') and m.get('quality') == 'pass'
        )
        print(f"Modules    : {present_mods} / {total_mods} documented")
        if present_mods:
            print(f"Mod Quality: {filled_mods} / {present_mods} flow files fully filled")

    print()


def print_results_json(
    doc_results: list[dict], module_results: list[dict],
    project_type: str, docs_dir: str,
) -> None:
    present_docs = sum(1 for r in doc_results if r['present'])
    filled_docs = sum(1 for r in doc_results if r['present'] and r['quality'] == 'pass')
    present_mods = sum(1 for m in module_results if m.get('flow_file_present'))
    filled_mods = sum(
        1 for m in module_results if m.get('flow_file_present') and m.get('quality') == 'pass'
    )

    payload = {
        'project_type': project_type,
        'docs_dir': docs_dir,
        'documents': [
            {
                'name': r['name'],
                'path': r['path'],
                'present': r['present'],
                'quality': r['quality'],
                'issues': r['issues'],
            }
            for r in doc_results
        ],
        'modules': [
            {
                'name': m['name'],
                'module_type': m.get('module_type'),
                'flow_file_present': m.get('flow_file_present', False),
                'quality': m.get('quality'),
                'issues': m.get('issues', []),
            }
            for m in module_results
        ],
        'summary': {
            'total_documents': len(doc_results),
            'documents_present': present_docs,
            'documents_quality_pass': filled_docs,
            'total_modules': len(module_results),
            'modules_documented': present_mods,
            'modules_quality_pass': filled_mods,
        },
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def parse_types(raw: str) -> list[str]:
    parts = [p.strip() for p in raw.split('+')]
    for p in parts:
        if p not in VALID_TYPES:
            print(
                f"error: unknown project type '{p}'. Valid: {', '.join(VALID_TYPES)}",
                file=sys.stderr,
            )
            sys.exit(2)
    return parts


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Audit document content quality for project_starter_v4 projects.",
    )
    parser.add_argument(
        '--project-type', required=True, metavar='TYPE',
        help=f"Project type. Valid: {', '.join(VALID_TYPES)}. Hybrid: TYPE+TYPE",
    )
    parser.add_argument(
        '--docs', default='docs', metavar='PATH',
        help='Path to docs directory (default: docs)',
    )
    parser.add_argument(
        '--strict', action='store_true',
        help='Exit 1 if any document is missing or has a quality FAIL',
    )
    parser.add_argument(
        '--json', action='store_true', dest='json_output',
        help='Output results as JSON',
    )
    args = parser.parse_args()

    project_types = parse_types(args.project_type)
    docs_dir = args.docs

    if not os.path.isdir(docs_dir):
        print(f"error: docs directory not found: {docs_dir}", file=sys.stderr)
        sys.exit(2)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    doc_results, module_results = audit(project_types, docs_dir, script_dir)

    if args.json_output:
        print_results_json(doc_results, module_results, args.project_type, docs_dir)
    else:
        print_results(doc_results, module_results, args.project_type)

    if args.strict:
        has_failure = any(
            not r['present'] or r['quality'] == 'fail' for r in doc_results
        ) or any(
            not m.get('flow_file_present') or m.get('quality') == 'fail'
            for m in module_results
        )
        if has_failure:
            sys.exit(1)


if __name__ == '__main__':
    main()
