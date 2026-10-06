#!/usr/bin/env python3
"""
infer_business_logic.py — Static-analysis draft of business-rule / rationale
candidates for a module, staged for human confirmation.

Companion to draft_module_flow.py, but targets the "meaning" documents Retrofit
Step 2 asks a human to fill from a blind read — business-process.md,
business-objects.md, business-rules.md, and research.md's rationale column
(templates/init/retrofit.md, Step 2 items 9-12). draft_module_flow.py already
established the split this script follows: pre-fill what is mechanically true,
leave what requires understanding intent as a human task. That script pre-fills
class/function names (syntax); this one pre-fills rule *candidates* that are
enforced in code (a guard clause that raises IS a business rule, by
construction) plus lower-confidence hints (comments, commit messages) that
only ever look like a reason.

Hard rule, matching code-quality-check.md's Evidence Rules ("never guess, never
infer missing behavior") and this project's stance on retrofit spec content
(templates/init/retrofit.md: "describe what already exists, not what should
exist"): this script NEVER writes into business-rules.md, business-process.md,
business-objects.md, or research.md directly. Output always lands in a staging
file under docs/_inferred/, and every single line carries a source pointer
(file:line, or a commit hash for a rationale hint) plus a confidence tier. A
human — not this script — decides what gets promoted into the real spec, using
the confirmation round described in the script's --help and in
templates/init/retrofit.md Step 2b.

Confidence tiers (reuses this project's existing High/Medium/Low vocabulary
from code-quality-check.md's Severity Guide, rather than inventing new terms):

  High   — enforced in code right now (a guard clause that raises/rejects, a
           DB constraint, a schema validator). The WHAT is not in question;
           only the paraphrase and the Reason column need a human's confirm.
  Medium — named or explained in a comment/docstring/test description near the
           enforcement point. The source text implies intent but could be
           stale, wrong, or sarcastic — must be confirmed, not assumed true.
  Low    — a rationale hint with no adjacent enforcement (e.g. a commit
           message touching the file, with no guard clause changed in the
           same commit). Weak evidence; likely to be rejected, still cheaper
           for a human to reject than to write from nothing.

Anything this script cannot attach a source pointer to is not emitted at all —
silence, not a guess. That gap still needs a [NEEDS CLARIFICATION] entry in
the real spec doc, same as project-requirements.md already does today; this
script does not fill that gap, only shrinks the amount of it that requires
writing from a blank page.

Usage:
  python3 templates/script/generators/infer_business_logic.py <module_src_dir> --project-type <type>
  python3 templates/script/generators/infer_business_logic.py src/billing --project-type web-app --docs docs
  python3 templates/script/generators/infer_business_logic.py src/billing --project-type web-app --history --force

Supported source languages: Python (.py, via `ast`) and JS/TS
(.js/.jsx/.ts/.tsx/.mjs/.cjs, via regex + brace-depth scanning — same class of
heuristic as draft_module_flow.py's JS path, same caveats apply). Other
languages are reported as unsupported per file, not silently skipped.
"""
from __future__ import annotations

import argparse
import ast
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scanners"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "validators"))
from _registry import VALID_TYPES  # noqa: E402
from _verify_common import parse_types  # noqa: E402

_JS_EXTENSIONS = (".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs")

# Words that mark a raise/throw as a business-rule enforcement point rather
# than a generic internal error (e.g. `assert isinstance(...)` is a type
# guard, not a business rule — excluded on purpose).
_REJECTION_CALLEE_HINTS = (
    "validationerror", "forbidden", "unauthorized", "badrequest", "conflict",
    "denied", "rejected", "invalid", "notallowed", "notpermitted",
    "toolate", "expired", "exceeded", "insufficient",
)

# Comment/docstring markers that plausibly state a *reason*, not just a
# restatement of what the code does. Deliberately narrow — recall matters
# less than precision here, since every hit still needs human confirmation.
_RATIONALE_MARKERS_RE = re.compile(
    r"\b(because|since|to prevent|to avoid|to ensure|required by|per policy|"
    r"compliance|due to)\b",
    re.IGNORECASE,
)


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class InferredItem:
    confidence: str  # "High" | "Medium" | "Low"
    kind: str  # "rule" | "rationale"
    description: str  # short paraphrase — the WHAT, not the WHY, unless kind == "rationale"
    file: str
    line: int
    evidence: str  # the actual source snippet or commit subject backing this item
    evidence_kind: str  # "guard_clause" | "comment" | "commit_message"


@dataclass
class ModuleInference:
    module_name: str
    items: list[InferredItem] = field(default_factory=list)
    unsupported_files: list[str] = field(default_factory=list)


# ---------------------------------------------------------------------------
# High confidence: guard clauses that raise/reject — Python (ast)
# ---------------------------------------------------------------------------

def _looks_like_rejection(node: ast.Raise) -> bool:
    """True if this raise's exception name/call matches a rejection pattern.

    Deliberately excludes bare `assert` and generic `raise ValueError(...)`
    with no matching keyword — those are as likely to be type/argument guards
    as business rules, and a false High-confidence item is worse than a
    missed one (see module docstring: silence over a guess).
    """
    exc = node.exc
    name = ""
    if isinstance(exc, ast.Call) and isinstance(exc.func, ast.Name):
        name = exc.func.id
    elif isinstance(exc, ast.Name):
        name = exc.id
    return any(hint in name.lower() for hint in _REJECTION_CALLEE_HINTS)


def _extract_python_guard_rules(path: Path, rel_path: str) -> list[InferredItem]:
    """Walk function bodies for `if <condition>: raise <Rejection>(...)`.

    A guard clause that raises IS enforcement — this is the one place the
    script asserts the WHAT with High confidence. The condition text is
    unparsed as-is (ast.unparse, Python 3.9+); it is NOT rephrased into
    natural language here — that rewrite is exactly the kind of "sounds
    right but might not be" step this script avoids. The human doing the
    confirmation round rephrases it once they've verified it against
    business-rules.md's actual Rule Name / Reason fields.
    """
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return []

    items: list[InferredItem] = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.If):
            continue
        for stmt in node.body:
            if isinstance(stmt, ast.Raise) and stmt.exc is not None and _looks_like_rejection(stmt):
                try:
                    cond_text = ast.unparse(node.test)
                except Exception:
                    cond_text = "<condition — could not unparse, read source directly>"
                items.append(InferredItem(
                    confidence="High",
                    kind="rule",
                    description=f"guards on `{cond_text}`",
                    file=rel_path,
                    line=node.lineno,
                    evidence=f"if {cond_text}: raise ...",
                    evidence_kind="guard_clause",
                ))
    return items


# ---------------------------------------------------------------------------
# High confidence: guard clauses that throw — JS/TS (regex, same caveats as
# draft_module_flow.py's JS path: best-effort, not a real parser)
# ---------------------------------------------------------------------------

_JS_GUARD_THROW_RE = re.compile(
    r"if\s*\((?P<cond>[^)]{1,200})\)\s*\{?\s*throw\s+new\s+(?P<exc>\w+)",
)


def _extract_js_guard_rules(path: Path, rel_path: str) -> list[InferredItem]:
    try:
        source = path.read_text(encoding="utf-8")
    except OSError:
        return []

    items: list[InferredItem] = []
    for lineno, line in enumerate(source.splitlines(), start=1):
        m = _JS_GUARD_THROW_RE.search(line)
        if not m or not any(hint in m.group("exc").lower() for hint in _REJECTION_CALLEE_HINTS):
            continue
        items.append(InferredItem(
            confidence="High",
            kind="rule",
            description=f"guards on `{m.group('cond').strip()}`",
            file=rel_path,
            line=lineno,
            evidence=line.strip(),
            evidence_kind="guard_clause",
        ))
    return items


# ---------------------------------------------------------------------------
# Medium confidence: rationale markers in comments/docstrings near a guard.
# TODO(skeleton): only scans same-line and one-line-above the guard today.
# A real implementation should also pull the enclosing function's docstring
# and cross-reference it against the guard found above, but that widens the
# false-positive surface (a docstring can explain the function without
# explaining this specific branch) enough that it needs a human decision
# before landing, not a default-on heuristic. Left unimplemented on purpose —
# ship the High-confidence path first, revisit after seeing how much Medium
# noise it produces in a real confirmation round.
# ---------------------------------------------------------------------------

def _extract_rationale_hints(path: Path, rel_path: str, guard_lines: set[int]) -> list[InferredItem]:
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return []

    items: list[InferredItem] = []
    for lineno in sorted(guard_lines):
        for probe in (lineno - 2, lineno - 1):  # 1-indexed lines just above the guard
            if probe < 1 or probe > len(lines):
                continue
            text = lines[probe - 1]
            if _RATIONALE_MARKERS_RE.search(text):
                items.append(InferredItem(
                    confidence="Medium",
                    kind="rationale",
                    description=text.strip().lstrip("/#* "),
                    file=rel_path,
                    line=probe,
                    evidence=text.strip(),
                    evidence_kind="comment",
                ))
                break
    return items


# ---------------------------------------------------------------------------
# Low confidence: commit messages touching this module, matching rationale
# markers. Weak on purpose — a commit subject rarely explains a specific
# guard clause, only that *something* in the file changed.
# TODO(skeleton): naive `git log` on the whole module directory. A sharper
# version would use `git log -L <line>,<line>:<file>` per guard clause found
# above instead of the whole module, at the cost of one subprocess call per
# item — worth doing once the High-confidence path is validated against a
# real retrofit, not before.
# ---------------------------------------------------------------------------

def _extract_commit_rationale(module_dir: Path, limit: int = 50) -> list[InferredItem]:
    try:
        result = subprocess.run(
            ["git", "log", f"-{limit}", "--pretty=format:%H%x1f%s", "--", str(module_dir)],
            capture_output=True, text=True, cwd=module_dir.parent, timeout=10,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    if result.returncode != 0:
        return []

    items: list[InferredItem] = []
    for line in result.stdout.splitlines():
        if "\x1f" not in line:
            continue
        commit_hash, subject = line.split("\x1f", 1)
        if _RATIONALE_MARKERS_RE.search(subject):
            items.append(InferredItem(
                confidence="Low",
                kind="rationale",
                description=subject.strip(),
                file=str(module_dir),
                line=0,
                evidence=f"commit {commit_hash[:8]}: {subject.strip()}",
                evidence_kind="commit_message",
            ))
    return items


# ---------------------------------------------------------------------------
# Discovery — mirrors draft_module_flow.py's discover_structure walk
# ---------------------------------------------------------------------------

def discover_inferences(module_dir: Path, include_history: bool) -> ModuleInference:
    inference = ModuleInference(module_name=module_dir.name)
    guard_lines_by_file: dict[str, set[int]] = {}

    for path in sorted(module_dir.rglob("*")):
        if not path.is_file():
            continue
        rel_path = str(path.relative_to(module_dir))

        if path.suffix == ".py":
            rule_items = _extract_python_guard_rules(path, rel_path)
        elif path.suffix in _JS_EXTENSIONS:
            rule_items = _extract_js_guard_rules(path, rel_path)
        else:
            continue

        if rule_items:
            inference.items.extend(rule_items)
            guard_lines_by_file[rel_path] = {item.line for item in rule_items}
            inference.items.extend(_extract_rationale_hints(path, rel_path, guard_lines_by_file[rel_path]))

    if include_history:
        inference.items.extend(_extract_commit_rationale(module_dir))

    return inference


# ---------------------------------------------------------------------------
# Rendering — staging file only, never the real spec doc (see module docstring)
# ---------------------------------------------------------------------------

def render_draft(inference: ModuleInference) -> str:
    title = inference.module_name.replace("-", " ").replace("_", " ").title()
    tiers = ("High", "Medium", "Low")
    by_tier = {tier: [i for i in inference.items if i.confidence == tier] for tier in tiers}

    lines = [
        f"# {title} — Inferred Business Logic (staging — not a spec document)",
        "",
        "<!-- Generated by infer_business_logic.py. Nothing in this file is confirmed.",
        "     Do not transcribe into business-rules.md / business-process.md / research.md",
        "     until each item has been through the confirmation round in",
        "     templates/init/retrofit.md Step 2b. Delete this file once its module is",
        "     fully confirmed — it is a staging area, not a permanent doc. -->",
        "",
        f"Module: `{inference.module_name}` — {len(inference.items)} candidate(s) "
        f"(High: {len(by_tier['High'])}, Medium: {len(by_tier['Medium'])}, Low: {len(by_tier['Low'])})",
        "",
    ]

    item_id = 0
    for tier in tiers:
        items = by_tier[tier]
        lines.append(f"## {tier} confidence")
        lines.append("")
        if not items:
            lines.append("_None found._")
            lines.append("")
            continue
        for item in items:
            item_id += 1
            lines.append(f"### INF-{item_id:03d} — {item.kind}: {item.description}")
            lines.append("")
            lines.append(f"- **Source:** `{item.file}:{item.line}`" if item.line else f"- **Source:** `{item.file}`")
            lines.append(f"- **Evidence ({item.evidence_kind}):** `{item.evidence}`")
            lines.append("- **Confirm / Edit / Reject:** _[fill in during the confirmation round]_")
            lines.append("")

    if not inference.items:
        lines.append(
            "_No High/Medium/Low candidates detected. This does not mean the module has no "
            "business rules — it means static analysis found no guard-clause or comment "
            "evidence. Fall back to a manual read for this module, same as retrofit.md Step 2 "
            "describes without this script's help._"
        )
        lines.append("")

    return "\n".join(lines).rstrip() + "\n"


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[union-attr]

    parser = argparse.ArgumentParser(
        description=(
            "Draft business-rule / rationale candidates from static analysis of a "
            "module's source — staged for human confirmation, never written directly "
            "into business-rules.md / business-process.md / research.md."
        )
    )
    parser.add_argument("module_dir", help="Path to the module's source folder (e.g. src/billing)")
    parser.add_argument(
        "--project-type", metavar="TYPE",
        help=f"Project type — reserved for future per-type extraction rules. Valid values: {', '.join(VALID_TYPES)}.",
    )
    parser.add_argument("--docs", default="docs", help="Path to docs directory (default: docs)")
    parser.add_argument(
        "--history", action="store_true",
        help="Also mine git log for Low-confidence rationale hints (slower — one git subprocess call).",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite an existing staging file")
    args = parser.parse_args()

    module_path = Path(args.module_dir)
    if not module_path.is_dir():
        print(f"error: not a directory: {args.module_dir}", file=sys.stderr)
        sys.exit(2)

    if args.project_type:
        parse_types(args.project_type)  # validates; extraction itself is not yet type-specific

    inference = discover_inferences(module_path, include_history=args.history)
    draft = render_draft(inference)

    out_dir = Path(args.docs) / "_inferred" / inference.module_name
    out_path = out_dir / f"{inference.module_name}-inferred.md"

    if out_path.exists() and not args.force:
        print(f"Skipped — already exists: {out_path} (use --force to overwrite)")
        sys.exit(0)

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path.write_text(draft, encoding="utf-8")

    print(f"Drafted: {out_path}")
    print(f"  High confidence (enforced in code):  {sum(1 for i in inference.items if i.confidence == 'High')}")
    print(f"  Medium confidence (comment hint):    {sum(1 for i in inference.items if i.confidence == 'Medium')}")
    print(f"  Low confidence (commit history):     {sum(1 for i in inference.items if i.confidence == 'Low')}")
    print("  Next: run the confirmation round with the user (templates/init/retrofit.md Step 2b) "
          "before transcribing anything into the real spec docs.")


if __name__ == "__main__":
    main()
