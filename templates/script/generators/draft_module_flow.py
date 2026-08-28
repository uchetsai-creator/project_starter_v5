#!/usr/bin/env python3
"""
draft_module_flow.py — Static-analysis draft for a module's flow doc.

Scout-style helper for the "no docs/modules entry yet" case in Checkpoint A
(guidance/learning-checkpoints/common.md) and Retrofit Step 3
(templates/init/retrofit.md). `scan_codebase.py --scaffold` already generates a
stub for an undocumented module, but that stub is a blank template — every
class/function name in it is a placeholder the human has to fill in from
scratch. This script instead parses the module's actual source files and
pre-fills the parts that are mechanically true: which classes exist, which
methods/functions they have, and which function names look like entry points
by name pattern.

What this does NOT do — and must not pretend to do — is reconstruct the real
call sequence (who calls whom, in what order, with what data). That requires
understanding intent, not just syntax, and a wrong auto-generated sequence
diagram would be worse than an empty one (see code-quality-check.md's Evidence
Rules: never guess, never infer missing behavior). So the Flow Format section
is left as a fill-in template, annotated with the detected entry-point
candidates as hints to verify — not asserted as fact.

Usage:
  python3 templates/script/generators/draft_module_flow.py <module_src_dir> --project-type <type>
  python3 templates/script/generators/draft_module_flow.py src/order --project-type web-app --docs docs
  python3 templates/script/generators/draft_module_flow.py src/order --project-type web-app --force

Supported source languages: Python (.py, via `ast`) and JS/TS/React
(.js/.jsx/.ts/.tsx/.mjs/.cjs, via regex + brace-depth scanning — same class of
heuristic as _spec_code_adapters/javascript_logging.py). Other languages are
listed in the draft with a note that structure could not be auto-detected.
"""
from __future__ import annotations

import argparse
import ast
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scanners"))
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "validators"))
from _module_types import MODULE_TYPE_REGISTRY  # noqa: E402
from _registry import VALID_TYPES  # noqa: E402
from _verify_common import parse_types  # noqa: E402
from scan_codebase import base_type, guess_type  # noqa: E402

_JS_EXTENSIONS = (".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs")

_ENTRY_NAME_HINTS = (
    "handle", "run", "main", "execute", "process", "consume", "subscribe",
    "on_", "create", "get", "list", "update", "delete", "post", "put",
    "patch", "route", "resolve", "command", "cmd", "index",
)

_CONTROL_KEYWORDS = frozenset({
    "if", "for", "while", "switch", "catch", "else", "do", "try", "finally",
    "function", "return", "constructor",
})


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------

@dataclass
class DetectedClass:
    name: str
    methods: list[str] = field(default_factory=list)


@dataclass
class DetectedFunction:
    name: str


@dataclass
class FileStructure:
    rel_path: str
    classes: list[DetectedClass] = field(default_factory=list)
    functions: list[DetectedFunction] = field(default_factory=list)
    unsupported: bool = False


def is_entry_candidate(name: str) -> bool:
    lower = name.lower()
    return any(hint in lower for hint in _ENTRY_NAME_HINTS)


# ---------------------------------------------------------------------------
# Python structure extraction (ast)
# ---------------------------------------------------------------------------

def _python_structure(path: Path, rel_path: str) -> FileStructure | None:
    try:
        source = path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(path))
    except (OSError, SyntaxError, UnicodeDecodeError):
        return None

    classes: list[DetectedClass] = []
    functions: list[DetectedFunction] = []

    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            methods = [
                n.name for n in node.body
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
                and not (n.name.startswith("__") and n.name.endswith("__"))
            ]
            classes.append(DetectedClass(name=node.name, methods=methods))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            functions.append(DetectedFunction(name=node.name))

    return FileStructure(rel_path=rel_path, classes=classes, functions=functions)


# ---------------------------------------------------------------------------
# JS/TS structure extraction (regex + brace-depth, no nested-function attempt —
# consistent with this being a best-effort draft, not a real parser)
# ---------------------------------------------------------------------------

_JS_CLASS_RE = re.compile(r"\bclass\s+(\w+)")
_JS_FUNC_DECL_RE = re.compile(r"\bfunction\s+(\w+)\s*\(")
_JS_ARROW_ASSIGN_RE = re.compile(
    r"\b(?:export\s+)?(?:const|let|var)\s+(\w+)\s*(?::[^=]+?)?=\s*(?:async\s*)?"
    r"(?:\([^)]*\)|\w+)\s*(?::[^=>{]+?)?=>"
)
_JS_METHOD_RE = re.compile(
    r"(?<![\w.])(?:(?:public|private|protected|static|async)\s+)*"
    r"([A-Za-z_$][\w$]*)\s*\([^()]*\)\s*(?::\s*[\w<>\[\].,\s]+?)?\s*\{"
)


def _find_matching_brace(source: str, open_idx: int) -> int:
    """Return the index of the '}' matching the '{' at open_idx, string-aware."""
    depth = 0
    i = open_idx
    n = len(source)
    quote: str | None = None
    while i < n:
        ch = source[i]
        if quote:
            if ch == "\\":
                i += 2
                continue
            if ch == quote:
                quote = None
            i += 1
            continue
        if ch in ("'", '"', "`"):
            quote = ch
            i += 1
            continue
        if ch == "{":
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return n  # unbalanced — treat rest of file as inside


def _js_structure(path: Path, rel_path: str) -> FileStructure | None:
    try:
        source = path.read_text(encoding="utf-8")
    except OSError:
        return None

    class_regions: list[tuple[int, int, str]] = []
    for m in _JS_CLASS_RE.finditer(source):
        brace_idx = source.find("{", m.end())
        if brace_idx == -1:
            continue
        end_idx = _find_matching_brace(source, brace_idx)
        class_regions.append((brace_idx, end_idx, m.group(1)))

    def _owning_class(pos: int) -> str | None:
        for start, end, name in class_regions:
            if start < pos < end:
                return name
        return None

    functions: list[DetectedFunction] = []
    for regex in (_JS_FUNC_DECL_RE, _JS_ARROW_ASSIGN_RE):
        for m in regex.finditer(source):
            if _owning_class(m.start()) is not None:
                continue  # counted as a method below instead
            functions.append(DetectedFunction(name=m.group(1)))

    classes: list[DetectedClass] = []
    for start, end, cls_name in class_regions:
        region = source[start:end]
        seen: list[str] = []
        for m in _JS_METHOD_RE.finditer(region):
            name = m.group(1)
            if name in _CONTROL_KEYWORDS or name in seen:
                continue
            seen.append(name)
        classes.append(DetectedClass(name=cls_name, methods=seen))

    return FileStructure(rel_path=rel_path, classes=classes, functions=functions)


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

def discover_structure(module_dir: Path) -> list[FileStructure]:
    results: list[FileStructure] = []
    for path in sorted(module_dir.rglob("*")):
        if not path.is_file():
            continue
        rel_path = str(path.relative_to(module_dir))
        if path.suffix == ".py":
            fs = _python_structure(path, rel_path)
        elif path.suffix in _JS_EXTENSIONS:
            fs = _js_structure(path, rel_path)
        else:
            continue
        if fs is not None and (fs.classes or fs.functions):
            results.append(fs)
    return results


def entry_candidates(structures: list[FileStructure]) -> list[str]:
    candidates: list[str] = []
    for fs in structures:
        for fn in fs.functions:
            if is_entry_candidate(fn.name):
                candidates.append(f"{fn.name}() — {fs.rel_path}")
        for cls in fs.classes:
            for method in cls.methods:
                if is_entry_candidate(method):
                    candidates.append(f"{cls.name}.{method}() — {fs.rel_path}")
    return candidates


# ---------------------------------------------------------------------------
# Format mapping — module-data-flow.md defines 4 canonical formats;
# scan_codebase.py's per-project-type vocabulary (Command, Namespace, Service,
# Screen, Resource Group, ...) maps down onto them via _module_types.py's
# MODULE_TYPE_REGISTRY (single source of truth, shared with verify_module_docs.py).
# ---------------------------------------------------------------------------


def resolve_format(module_type_label: str) -> str:
    label = base_type(module_type_label)  # strips "Pipeline Stage (detected)" -> "Pipeline Stage"
    draft_format = MODULE_TYPE_REGISTRY.get(label, {}).get("draft_format")
    # e.g. Resource Group — module-data-flow.md has no matching format (documented,
    # tested gap — see tests/unit/test_draft_module_flow.py's
    # test_unmapped_module_type_falls_back_honestly_instead_of_guessing)
    return draft_format or "UNKNOWN"


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------

def _render_detected_structure(structures: list[FileStructure]) -> str:
    if not structures:
        return (
            "_No classes or functions detected — either this module has no "
            "supported source files (Python / JS / TS), or the file(s) contain "
            "only top-level statements. Fill in the structure below manually._"
        )
    lines = ["## Detected Structure (auto-generated from source — verify before relying on it)", ""]
    for fs in structures:
        lines.append(f"### `{fs.rel_path}`")
        for cls in fs.classes:
            method_list = ", ".join(f"{m}()" for m in cls.methods) or "(no public methods detected)"
            lines.append(f"- class **{cls.name}** — methods: {method_list}")
        for fn in fs.functions:
            lines.append(f"- function **{fn.name}()**")
        lines.append("")
    return "\n".join(lines).rstrip()


def _render_entry_hint(candidates: list[str]) -> str:
    if not candidates:
        return "[Entry point — no name-pattern match found; identify manually]"
    joined = "; ".join(candidates)
    return f"[Entry point — candidates detected by name, confirm which applies: {joined}]"


def _render_class_block(title: str, structures: list[FileStructure]) -> str:
    classes = [cls for fs in structures for cls in fs.classes]
    if not classes:
        return (
            f"```plantuml\n@startuml\ntitle {title} Structure\n\n"
            f"' No classes detected — this module may be function-based.\n"
            f"' List the real functions as a class block manually if needed.\n"
            f"@enduml\n```"
        )
    lines = ["```plantuml", "@startuml", f"title {title} Structure", ""]
    for cls in classes:
        lines.append(f"class {cls.name} {{")
        for method in cls.methods:
            visibility = "-" if method.startswith("_") else "+"
            lines.append(f"  {visibility}{method}(): TODO_return_type")
        if not cls.methods:
            lines.append("  ' no public methods detected")
        lines.append("}")
        lines.append("")
    if len(classes) > 1:
        lines.append("' TODO: relationships between classes above are not inferred —")
        lines.append("' static analysis cannot tell who calls whom; add the real edges.")
    lines.append("@enduml")
    lines.append("```")
    return "\n".join(lines)


def render_draft(
    module_name: str,
    module_type_label: str,
    structures: list[FileStructure],
    candidates: list[str],
) -> str:
    title = module_name.replace("-", " ").replace("_", " ").title()
    fmt = resolve_format(module_type_label)
    canonical_type = {
        "A": "Feature", "B": "Background Job", "D": "Pipeline Stage", "C": "Shared Utility",
    }.get(fmt, base_type(module_type_label))

    header = (
        f"# {title} Data Flow\n\n"
        f"**Module type:** {canonical_type} "
        f"(scan_codebase.py classified this folder as: {module_type_label})\n\n"
        f"<!-- DRAFT — generated by draft_module_flow.py from static analysis of "
        f"{module_name}/. Detected Structure below is factual (real names from the "
        f"source); everything else is a template for you to fill in. Do not treat "
        f"this file as final documentation until the Flow Format and Overview "
        f"sections are written by a human. -->\n\n"
        f"## Overview\n\n[Description of what this module does — not auto-derivable, fill in]\n\n"
        f"---\n\n"
        f"{_render_detected_structure(structures)}\n\n---\n\n"
    )

    if fmt == "C":
        body = (
            "## Shared Utility — Class Block\n\n"
            f"{_render_class_block(title, structures)}\n\n"
            "**Used by:**\n\n| Module | Purpose |\n|---|---|\n| [module name] | [what it uses from this utility] |\n"
        )
    elif fmt == "UNKNOWN":
        body = (
            f"<!-- No module-data-flow.md format matches classification "
            f"'{module_type_label}' — module-data-flow.md's 4 formats are "
            f"Feature / Background Job / Pipeline Stage / Shared Utility. Confirm "
            f"with the user which one actually applies, or whether this module type "
            f"needs its own documentation approach (e.g. IaC resource groups are "
            f"usually described in topology.md instead of a per-module flow file). -->\n\n"
            f"{_render_class_block(title, structures)}\n"
        )
    else:
        flow_label = {"A": "Operation Name", "B": "Flow Name", "D": "Stage Name"}[fmt]
        body = (
            f"## {'Process' if fmt == 'A' else 'Flow'}: [{flow_label} — fill in]\n\n"
            f"### Flow Format\n\n"
            f"```\n"
            f"{_render_entry_hint(candidates)}\n"
            f"↓\n"
            f"[Next step — see templates/flows/module-data-flow.md Format {fmt} for the full step list]\n"
            f"↓\n"
            f"[Result — response / return value / emitted event / side effect]\n"
            f"```\n\n"
            f"### Class Block\n\n"
            f"{_render_class_block(title, structures)}\n"
        )

    return header + body


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    # Force UTF-8 stdout/stderr — without this, a non-ASCII character (e.g. "→")
    # crashes print() with UnicodeEncodeError on a non-UTF-8-default Windows console
    # (confirmed in CI on windows-latest; see orchestrator.py's main() and CHANGELOG.md).
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[union-attr]  # guard above only narrows sys.stdout

    parser = argparse.ArgumentParser(
        description=(
            "Draft a module-data-flow.md from static analysis of a module's source "
            "files — pre-fills real class/function names instead of a blank stub."
        )
    )
    parser.add_argument("module_dir", help="Path to the module's source folder (e.g. src/order)")
    parser.add_argument(
        "--project-type",
        metavar="TYPE",
        help=f"Project type — controls module classification. Valid values: {', '.join(VALID_TYPES)}. "
             f"Hybrid types use + (e.g. data-pipeline+web-app).",
    )
    parser.add_argument("--docs", default="docs", help="Path to docs directory (default: docs)")
    parser.add_argument("--force", action="store_true", help="Overwrite an existing draft file")
    args = parser.parse_args()

    module_path = Path(args.module_dir)
    if not module_path.is_dir():
        print(f"error: not a directory: {args.module_dir}", file=sys.stderr)
        sys.exit(2)

    classify_type = parse_types(args.project_type)[0] if args.project_type else None
    module_name = module_path.name
    module_type_label = guess_type(module_name, classify_type, str(module_path))

    structures = discover_structure(module_path)
    candidates = entry_candidates(structures)
    draft = render_draft(module_name, module_type_label, structures, candidates)

    out_dir = Path(args.docs) / "modules" / module_name
    out_path = out_dir / f"{module_name}-module-data-flow.md"

    if out_path.exists() and not args.force:
        print(f"Skipped — already exists: {out_path} (use --force to overwrite)")
        sys.exit(0)

    out_dir.mkdir(parents=True, exist_ok=True)
    out_path.write_text(draft, encoding="utf-8")
    print(f"Drafted: {out_path}")
    print(f"  Classified as: {module_type_label}")
    print(f"  Files scanned: {len(structures)}")
    print(f"  Entry-point candidates: {len(candidates)}")
    if not structures:
        print("  [WARN] No Python or JS/TS structure detected — draft is a bare template.")


if __name__ == "__main__":
    main()
