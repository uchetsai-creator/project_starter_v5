#!/usr/bin/env python3
"""
verify_requirements_form.py — Checks that project-requirements.md is written in the form
readers can use to understand the system. Applies to every project type.

Checks:
  EARS          every functional requirement (FR-XXX bullet) states its trigger and response:
                WHEN / WHILE / IF / WHERE … THE SYSTEM SHALL …, or an unconditional
                THE SYSTEM SHALL … (ubiquitous). Bullets that are still template placeholders
                (text in square brackets only) are reported as unfilled, not as wrong form.
  Scenarios     every functional-requirement group has at least one scenario written as
                Given / When / Then. A group is a `### SL-n — …` slice when slices are used,
                otherwise each `###` heading under "## Functional Requirements" (or
                "## 功能需求").
  Journeys      a "## User Journeys" (or "## 使用者旅程") section exists with at least one
                sub-heading: what each role is trying to do, end to end.
  Glossary      optional. When specs/glossary.md exists it must be a table with at least one
                "term | meaning" row and both cells filled. When it is absent the check passes
                and prints a hint: create it only if the project uses domain terms or
                abbreviations that readers need explained.

Format rules are checked on the document text. Structure (headings) is matched in English or
Chinese so the same check works for projects written in either language.

Usage:
  python3 docs/script/validators/verify_requirements_form.py --docs docs
  python3 docs/script/validators/verify_requirements_form.py --docs docs --json

Exit status: 0 when every check passes, 1 when any check fails.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import sys

EARS_PREFIX = re.compile(r"^\s*(?:WHEN|WHILE|IF|WHERE)\b", re.IGNORECASE)
EARS_UNCONDITIONAL = re.compile(r"THE SYSTEM SHALL\b")
FR_BULLET = re.compile(r"^\s*[-*]\s+\*\*(FR-[A-Z0-9]+)\*\*\s*[:：]?\s*(.*)$")
SLICE_HEADING = re.compile(r"^###\s+SL-\d+\b.*$")
FR_SECTION = re.compile(r"^##\s+(?:Functional Requirements|功能需求)\b")
JOURNEY_SECTION = re.compile(r"^##\s+(?:User Journeys|使用者旅程)\b")
GROUP_HEADING = re.compile(r"^###\s+(.+)$")
H2 = re.compile(r"^##\s+")
SCENARIO_WORDS = ("Given", "When", "Then")


def _strip_html_comments(text: str) -> str:
    return re.sub(r"<!--.*?-->", "", text, flags=re.DOTALL)


def _is_placeholder(text: str) -> bool:
    """Template bullets keep their bracketed slots, e.g. `WHEN [trigger/event occurs], THE SYSTEM SHALL [...]`."""
    return bool(re.search(r"\[[^\]]*\]", text))


def check_ears(lines):
    """Return (violations, unfilled) for FR bullets."""
    violations, unfilled = [], []
    for lineno, line in enumerate(lines, 1):
        m = FR_BULLET.match(line)
        if not m:
            continue
        fr_id, body = m.group(1), m.group(2).strip()
        if _is_placeholder(body):
            unfilled.append((lineno, fr_id))
            continue
        if EARS_PREFIX.match(body) or EARS_UNCONDITIONAL.search(body):
            continue
        violations.append((lineno, fr_id, body[:100]))
    return violations, unfilled


def _groups(lines):
    """Return ({group_name: [line_numbers]}, has_slices) for the functional-requirement groups."""
    has_slices = any(SLICE_HEADING.match(l) for l in lines)
    groups: dict[str, list[int]] = {}
    in_fr = False
    current = None
    for i, line in enumerate(lines, 1):
        if FR_SECTION.match(line):
            in_fr, current = True, None
            continue
        if H2.match(line):
            in_fr, current = False, None
            continue
        if not in_fr:
            continue
        if has_slices:
            if SLICE_HEADING.match(line):
                current = re.sub(r"^###\s+", "", line.strip())
                groups[current] = []
                continue
            if GROUP_HEADING.match(line):
                current = None  # a plain ### inside slice mode is not a slice
                continue
        else:
            m = GROUP_HEADING.match(line)
            if m:
                current = m.group(1).strip()
                groups[current] = []
                continue
        if current is not None:
            groups[current].append(i)
    return groups, has_slices


def check_scenarios(lines):
    """Return (groups_without_scenario, all_groups)."""
    groups, _ = _groups(lines)
    missing = []
    for name, line_numbers in groups.items():
        # template placeholder lines do not count as a written scenario
        body = "\n".join(lines[n - 1] for n in line_numbers if not _is_placeholder(lines[n - 1]))
        if not all(re.search(rf"\b{w}\b", body) for w in SCENARIO_WORDS):
            missing.append(name)
    return missing, list(groups)


def check_journeys(lines):
    in_section = False
    has_subheading = False
    found = False
    for line in lines:
        if JOURNEY_SECTION.match(line):
            found, in_section = True, True
            continue
        if in_section and H2.match(line):
            break
        if in_section and GROUP_HEADING.match(line):
            has_subheading = True
    return found, has_subheading


GLOSSARY_ROW = re.compile(r"^\s*\|(.+)\|\s*$")


def check_glossary(path: str) -> dict:
    """Optional file: absent passes; present must have at least one filled term | meaning row."""
    if not os.path.exists(path):
        return {"ok": True, "present": False, "path": path, "bad_rows": []}
    rows, bad = 0, []
    for lineno, line in enumerate(open(path, encoding="utf-8"), 1):
        m = GLOSSARY_ROW.match(line)
        if not m:
            continue
        cells = [c.strip() for c in m.group(1).split("|")]
        if all(set(c) <= set("-: ") for c in cells):
            continue  # separator row
        if len(cells) < 2:
            bad.append({"line": lineno, "text": line.strip()[:80]})
            continue
        if cells[0].lower() in ("term", "詞", "術語"):
            continue  # header row
        if not cells[0] or not cells[1]:
            bad.append({"line": lineno, "text": line.strip()[:80]})
            continue
        rows += 1
    ok = rows >= 1 and not bad
    return {"ok": ok, "present": True, "path": path, "rows": rows, "bad_rows": bad}


def run(docs_dir: str) -> dict:
    req_path = os.path.join(docs_dir, "project-requirements.md")
    result = {"file": req_path, "checks": {}, "passed": True}
    if not os.path.exists(req_path):
        result["checks"]["file"] = {"ok": False, "detail": "project-requirements.md not found"}
        result["passed"] = False
        return result

    lines = _strip_html_comments(open(req_path, encoding="utf-8").read()).splitlines()

    violations, unfilled = check_ears(lines)
    result["checks"]["ears"] = {
        "ok": not violations,
        "violations": [{"line": n, "id": i, "text": t} for n, i, t in violations],
        "unfilled": [{"line": n, "id": i} for n, i in unfilled],
    }

    missing, groups = check_scenarios(lines)
    result["checks"]["scenarios"] = {
        "ok": bool(groups) and not missing,
        "groups": len(groups),
        "missing": missing,
    }

    found, has_sub = check_journeys(lines)
    result["checks"]["journeys"] = {
        "ok": found and has_sub,
        "section_found": found,
        "has_subsection": has_sub,
    }

    result["checks"]["glossary"] = check_glossary(os.path.join(docs_dir, "specs", "glossary.md"))

    result["passed"] = all(c["ok"] for c in result["checks"].values())
    return result


def _print(result: dict) -> None:
    c = result["checks"]
    if "file" in c:
        print(f"FAIL  {c['file']['detail']}")
        return
    e = c["ears"]
    print(f"{'PASS' if e['ok'] else 'FAIL'}  EARS: {len(e['violations'])} requirement(s) not in WHEN/WHILE/IF/WHERE … SHALL form")
    for v in e["violations"]:
        print(f"        line {v['line']}  {v['id']}: {v['text']}")
    if e["unfilled"]:
        print(f"        ({len(e['unfilled'])} template placeholder(s) still unfilled)")
    s = c["scenarios"]
    print(f"{'PASS' if s['ok'] else 'FAIL'}  Scenarios: {len(s['missing'])} of {s['groups']} group(s) lack Given/When/Then")
    for name in s["missing"]:
        print(f"        {name}")
    j = c["journeys"]
    print(f"{'PASS' if j['ok'] else 'FAIL'}  Journeys: section {'found' if j['section_found'] else 'missing'}, "
          f"sub-section {'found' if j['has_subsection'] else 'missing'}")
    g = c["glossary"]
    if not g["present"]:
        print("PASS  Glossary: not present (optional). Create specs/glossary.md if the project uses domain terms or abbreviations.")
    else:
        print(f"{'PASS' if g['ok'] else 'FAIL'}  Glossary: {g['rows']} term row(s) in {g['path']}")
        for b in g["bad_rows"]:
            print(f"        line {b['line']}: needs a term and a meaning: {b['text']}")


def main() -> int:
    parser = argparse.ArgumentParser(description="Check project-requirements.md form (EARS, scenarios, journeys, glossary).")
    parser.add_argument("--docs", default="docs", help="docs directory (default: docs)")
    parser.add_argument("--json", action="store_true", help="print the result as JSON")
    args = parser.parse_args()

    result = run(args.docs)
    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        _print(result)
    return 0 if result["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())
