#!/usr/bin/env python3
"""scan_codebase.py — Module inventory and documentation coverage check

Scans a source directory and compares it against docs/modules/ to find:
  - Which folders are already documented
  - Which folders are not yet documented
  - Which folders are uncertain (shared utility? infrastructure?)

Outputs:
  --tree      Print a tree view of the source directory with coverage annotations
  --coverage  Print a coverage summary table
  --update    Update the Project Structure and Coverage Summary sections in codebase-map.md
  --format    Output format: text (default) or json
  --scaffold  Generate stub module-data-flow.md files for undocumented modules

Usage:
  python3 docs/script/scanners/scan_codebase.py <src_dir>
  python3 docs/script/scanners/scan_codebase.py <src_dir> --project-type <type>
  python3 docs/script/scanners/scan_codebase.py <src_dir> --depth 2
  python3 docs/script/scanners/scan_codebase.py <src_dir> --format json
  python3 docs/script/scanners/scan_codebase.py <src_dir> --scaffold
  python3 docs/script/scanners/scan_codebase.py <src_dir> --tree
  python3 docs/script/scanners/scan_codebase.py <src_dir> --coverage
  python3 docs/script/scanners/scan_codebase.py <src_dir> --update docs/codebase-map.md

Project types (controls module boundary detection heuristic):
  web-app        Folders = Feature modules, Background Jobs, or Shared/Infrastructure (default)
  cli-tool       Folders = Commands or Shared/Infrastructure
  library        Folders = Namespaces or Shared/Infrastructure
  data-pipeline  Folders = Pipeline Stages or Shared/Infrastructure
  ml-pipeline    Folders = Pipeline Stages or Shared/Infrastructure
  microservices  Folders = Services or Shared/Infrastructure
  llm-app        Folders = Feature modules, Background Jobs, or Shared/Infrastructure
  iac            Folders = Resource Groups or Shared/Infrastructure (.terraform, modules)
  mobile-app     Folders = Screens or Shared/Infrastructure (navigation, components)

Examples:
  python3 docs/script/scanners/scan_codebase.py src
  python3 docs/script/scanners/scan_codebase.py src --project-type data-pipeline
  python3 docs/script/scanners/scan_codebase.py services --project-type microservices --depth 2
  python3 docs/script/scanners/scan_codebase.py stages --project-type ml-pipeline --update docs/codebase-map.md
  python3 docs/script/scanners/scan_codebase.py src --project-type cli-tool --coverage
  python3 docs/script/scanners/scan_codebase.py src --project-type web-app --scaffold
  python3 docs/script/scanners/scan_codebase.py src --format json
"""

import sys
import os
import argparse
import glob
import json
import re
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / 'validators'))
from _registry import VALID_TYPES

# ---------------------------------------------------------------------------
# Folders that are almost never feature modules — skip or mark as "—"
# ---------------------------------------------------------------------------
SHARED_PATTERNS = {
    "lib", "libs", "utils", "util", "helpers", "helper",
    "common", "shared", "core", "types", "interfaces",
    "config", "configs", "constants",
    "middleware", "middlewares",
    "scripts", "script",
    "migrations", "migration", "seeds", "seed",
    "test", "tests", "__tests__", "spec", "specs",
    "dist", "build", "node_modules", ".git", "__pycache__",
    "docs", "docs-zh", "logs",
}

JOB_PATTERNS = {
    "jobs", "job", "workers", "worker",
    "consumers", "consumer", "subscribers", "subscriber",
    "cron", "crons", "tasks", "task", "queues", "queue",
    "handlers", "events",
}

# Pipeline stage name patterns — folder names commonly used in Data/ML pipelines.
# Numbers are stripped before matching (e.g. "01_extract" → "extract").
PIPELINE_STAGE_PATTERNS = {
    # Data pipeline stages
    "extract", "ingest", "intake", "fetch", "collect",
    "validate", "validation", "quality", "check",
    "transform", "transformation", "process", "processing", "enrich",
    "load", "export", "output", "sink",
    "stage", "staging",
    "raw", "curated", "clean", "cleaned",
    # ML pipeline stages
    "data", "dataset",
    "preprocess", "preprocessing",
    "features", "feature_engineering", "featurize",
    "train", "training",
    "evaluate", "evaluation", "eval",
    "predict", "prediction", "inference", "score", "scoring",
    "serve", "serving",
    "deploy", "deployment",
    "monitor", "monitoring",
    "register", "registry",
}

# Directories skipped at every level during recursive scan
SKIP_DIRS = {
    ".git", ".github", "node_modules", "__pycache__",
    ".venv", "venv", "dist", "build", ".next", ".nuxt",
    "coverage", ".pdf_build_cache",
}

# ---------------------------------------------------------------------------
# Per-type vocabulary: what to call a non-shared folder
# ---------------------------------------------------------------------------

# Maps project-type → (singular label, plural label for summary line)
MODULE_VOCAB: dict[str, tuple[str, str]] = {
    "web-app":       ("Feature",        "feature modules"),
    "cli-tool":      ("Command",        "commands"),
    "library":       ("Namespace",      "namespaces"),
    "data-pipeline": ("Pipeline Stage", "pipeline stages"),
    "ml-pipeline":   ("Pipeline Stage", "pipeline stages"),
    "microservices": ("Service",        "services"),
    "llm-app":       ("Feature",        "feature modules"),
    "iac":           ("Resource Group", "resource groups"),
    "mobile-app":    ("Screen",         "screens"),
}


# ---------------------------------------------------------------------------
# Scaffold stub template
# ---------------------------------------------------------------------------

_SCAFFOLD_STUB = """\
# {title} Data Flow

**Module type:** {module_type}

<!-- Scaffold stub — generated by scan_codebase.py --scaffold. Fill in content using the format defined in docs/modules/module-data-flow.md. -->

## Overview

[Description of what this module does]

---

[Add sequence or class diagram here following the {module_type} format in docs/modules/module-data-flow.md]
"""


# ---------------------------------------------------------------------------
# Classification helpers
# ---------------------------------------------------------------------------

def is_shared(name: str) -> bool:
    return name.lower() in SHARED_PATTERNS


def is_job_folder(name: str) -> bool:
    lower = name.lower()
    if lower in JOB_PATTERNS:
        return True
    # Match compound names like "order-consumer", "cron-inventory", "email-worker"
    parts = re.split(r"[-_]", lower)
    return any(p in JOB_PATTERNS for p in parts)


def is_pipeline_stage(name: str) -> bool:
    """Return True if the folder name matches a known pipeline stage pattern."""
    lower = name.lower()
    if lower in PIPELINE_STAGE_PATTERNS:
        return True
    # Strip leading numeric prefix: "01_extract" → "extract", "02-validate" → "validate"
    stripped = re.sub(r"^\d+[_\-]", "", lower)
    return stripped in PIPELINE_STAGE_PATTERNS


def is_pipeline_stage_detected(path: str) -> bool:
    """Return True if directory contains files indicative of a concrete pipeline stage."""
    try:
        files = os.listdir(path)
    except (PermissionError, FileNotFoundError):
        return False
    for f in files:
        if (f.endswith("_stage.py") or
                (f.startswith("step_") and f.endswith(".py")) or
                (f.startswith("run_") and f.endswith(".py"))):
            return True
    return False


def base_type(type_str: str) -> str:
    """Strip confidence qualifier: 'Pipeline Stage (detected)' → 'Pipeline Stage'."""
    return type_str.split(" (")[0] if " (" in type_str else type_str


def guess_type(name: str, project_type: str | None = None, path: str | None = None) -> str:
    """Classify a source folder based on its name and the declared project type.

    Project type controls which module boundary heuristic applies:
    - data-pipeline / ml-pipeline: all non-shared folders are Pipeline Stages;
      content peek upgrades label to '(detected)' or '(inferred)'
    - cli-tool: all non-shared folders are Commands
    - library: all non-shared folders are Namespaces
    - microservices: all non-shared folders are Services
    - web-app / llm-app / None: Feature or Background Job (existing behaviour)
    """
    if is_shared(name):
        return "Shared / Infrastructure"

    if project_type in ("data-pipeline", "ml-pipeline"):
        if path and is_pipeline_stage_detected(path):
            return "Pipeline Stage (detected)"
        if is_pipeline_stage(name):
            return "Pipeline Stage"
        return "Pipeline Stage (inferred)"

    if project_type == "cli-tool":
        return "Command"

    if project_type == "library":
        return "Namespace"

    if project_type == "microservices":
        return "Service"

    if project_type == "iac":
        if name.lower() in {"modules", ".terraform", ".terragrunt-cache"}:
            return "Shared / Infrastructure"
        return "Resource Group"

    if project_type == "mobile-app":
        if name.lower() in {"navigation", "navigators", "components", "widgets",
                             "hooks", "store", "stores", "services", "native",
                             "android", "ios", "assets", "theme", "themes"}:
            return "Shared / Infrastructure"
        return "Screen"

    # web-app, llm-app, and unspecified (default)
    if is_job_folder(name):
        return "Background Job"
    return "Feature"


# ---------------------------------------------------------------------------
# Discovery
# ---------------------------------------------------------------------------

def find_source_folders(src_dir: str, project_type: str | None = None, depth: int = 1) -> list[dict]:
    """Return subdirectories of src_dir up to `depth` levels deep."""
    src_path = Path(src_dir)
    if not src_path.exists():
        print(f"Error: directory not found: {src_dir}")
        sys.exit(1)

    folders: list[dict] = []
    _collect(src_path, src_path, src_path.parent, project_type, depth, 1, folders)
    return folders


def _collect(
    src_root: Path, current: Path, project_root: Path,
    project_type: str | None, max_depth: int, cur_depth: int,
    results: list[dict],
) -> None:
    try:
        entries = sorted(current.iterdir())
    except PermissionError:
        return
    for entry in entries:
        if not entry.is_dir() or entry.name.startswith(".") or entry.name in SKIP_DIRS:
            continue
        rel_to_src = entry.relative_to(src_root)
        results.append({
            "name": entry.name,
            "display_name": str(rel_to_src),
            "path": str(entry),
            "rel": str(entry.relative_to(project_root)),
            "type": guess_type(entry.name, project_type, str(entry)),
            "depth": cur_depth,
        })
        if cur_depth < max_depth:
            _collect(src_root, entry, project_root, project_type, max_depth, cur_depth + 1, results)


def find_documented_modules(docs_dir: str = "docs") -> dict[str, str]:
    """Return {module_name: flow_file_path} for all existing module flow files."""
    pattern = os.path.join(docs_dir, "modules", "**", "*-module-data-flow.md")
    result = {}
    for path in glob.glob(pattern, recursive=True):
        # Derive module name from the parent folder name
        module_name = Path(path).parent.name
        result[module_name] = path
    return result


def match_folder_to_module(folder_name: str, documented: dict[str, str]) -> str | None:
    """Try to find a matching documented module for a source folder (by basename)."""
    return documented.get(folder_name)


def annotate_folders(folders: list[dict], documented: dict[str, str]) -> list[dict]:
    for f in folders:
        match = match_folder_to_module(f["name"], documented)
        if f["type"] == "Shared / Infrastructure":
            f["status"] = "—"
            f["status_icon"] = "—"
            f["flow_file"] = "— Not required"
        elif match:
            f["status"] = "Documented"
            f["status_icon"] = "✅"
            f["flow_file"] = match
        else:
            f["status"] = "Not documented"
            f["status_icon"] = "❌"
            f["flow_file"] = "—"
    return folders


# ---------------------------------------------------------------------------
# Output: Tree view
# ---------------------------------------------------------------------------

def _arrow(label: str, width: int = 36) -> str:
    """Right-pad name to `width` chars then append ← label."""
    return f"{label:<{width}}← "


def print_tree(src_dir: str, folders: list[dict], docs_dir: str = "docs") -> str:
    """
    Build a full project-root tree starting one level above src_dir.
    Annotates every folder with ← description and module status icons.
    Tree always shows depth=1 of src_dir regardless of --depth value.
    """
    src_path = Path(src_dir).resolve()
    project_root = src_path.parent
    # Only use depth=1 folders for tree annotation
    depth1_folders = [f for f in folders if f["depth"] == 1]
    folder_names = {f["name"] for f in depth1_folders}

    lines = []
    lines.append(f"{project_root.name}/")

    # Collect top-level entries of the project root
    try:
        root_entries = sorted(project_root.iterdir(), key=lambda x: (x.is_file(), x.name))
    except PermissionError:
        root_entries = []

    visible = [e for e in root_entries if e.name not in SKIP_DIRS]

    for i, entry in enumerate(visible):
        is_last = (i == len(visible) - 1)
        prefix = "└── " if is_last else "├── "
        child_prefix = "    " if is_last else "│   "

        if entry == src_path:
            # This is the source folder — expand its modules
            lines.append(f"{prefix}{_arrow(entry.name + '/', 28)}application source code")
            try:
                src_children = sorted(src_path.iterdir(), key=lambda x: (x.is_file(), x.name))
            except PermissionError:
                src_children = []
            src_visible = [e for e in src_children if e.name not in SKIP_DIRS]
            for j, sub in enumerate(src_visible):
                sub_last = (j == len(src_visible) - 1)
                sub_prefix = child_prefix + ("└── " if sub_last else "├── ")
                if sub.is_dir() and sub.name in folder_names:
                    folder = next(f for f in depth1_folders if f["name"] == sub.name)
                    icon = folder["status_icon"]
                    desc = folder.get("desc", base_type(folder["type"]))
                    name_col = f"{sub.name}/"
                    lines.append(f"{sub_prefix}{icon}  {name_col:<24}← {desc}")
                elif sub.is_dir():
                    lines.append(f"{sub_prefix}{sub.name}/")
                else:
                    lines.append(f"{sub_prefix}{sub.name}")

        elif entry.is_dir():
            known = {
                "docs":        "planning, specs, architecture, module flow docs",
                "doc":         "planning, specs, architecture, module flow docs",
                "prisma":      "database schema and migrations",
                "migrations":  "database migrations",
                "migration":   "database migrations",
                "test":        "tests",
                "tests":       "tests",
                "__tests__":   "tests",
                "scripts":     "utility scripts",
                "script":      "utility scripts",
                "infra":       "infrastructure / IaC",
                "k8s":         "Kubernetes manifests",
                "deploy":      "deployment configs",
                "config":      "configuration files",
                "public":      "static assets",
                "assets":      "static assets",
            }
            desc = known.get(entry.name.lower(), "")
            if desc:
                lines.append(f"{prefix}{_arrow(entry.name + '/', 28)}{desc}")
            else:
                lines.append(f"{prefix}{entry.name}/")

        else:
            known_files = {
                "package.json":        "Node.js dependency manifest",
                "go.mod":              "Go module definition",
                "requirements.txt":    "Python dependencies",
                "pyproject.toml":      "Python project config",
                "Cargo.toml":          "Rust package manifest",
                "pom.xml":             "Maven project config",
                "build.gradle":        "Gradle build config",
                "docker-compose.yml":  "local infrastructure services",
                "docker-compose.yaml": "local infrastructure services",
                "Dockerfile":          "container build definition",
                ".env.example":        "environment variable template",
                "Makefile":            "build / dev task runner",
                "README.md":           "project overview",
            }
            desc = known_files.get(entry.name, "")
            if desc:
                lines.append(f"{prefix}{_arrow(entry.name, 28)}{desc}")
            else:
                lines.append(f"{prefix}{entry.name}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Output: Coverage table
# ---------------------------------------------------------------------------

def print_coverage(folders: list[dict], project_type: str | None = None) -> str:
    _, plural_label = MODULE_VOCAB.get(project_type, ("Feature", "feature modules"))

    lines = []
    lines.append(f"=== {plural_label.title()} Coverage Report ===\n")

    documented = [f for f in folders if f["status"] == "Documented"]
    undocumented = [f for f in folders if f["status"] == "Not documented"]
    shared = [f for f in folders if f["status"] == "—"]

    if documented:
        lines.append("✅  Documented:")
        for f in documented:
            lines.append(f"    {f['rel']:<40}  →  {f['flow_file']}")
        lines.append("")

    if undocumented:
        lines.append("❌  Not yet documented:")
        for f in undocumented:
            lines.append(f"    {f['rel']:<40}  →  needs module-data-flow.md  [{f['type']}]")
        lines.append("")

    if shared:
        lines.append("—   Shared / Infrastructure (no flow file needed):")
        for f in shared:
            lines.append(f"    {f['rel']}")
        lines.append("")

    total = len(documented) + len(undocumented)
    pct = int(len(documented) / total * 100) if total else 100
    lines.append(f"Coverage: {len(documented)}/{total} {plural_label} documented ({pct}%)")

    if undocumented:
        lines.append("")
        lines.append("Next steps:")
        for f in undocumented:
            slug = f["name"]
            lines.append(
                f"  - Create docs/modules/{slug}/{slug}-module-data-flow.md  [{base_type(f['type'])}]"
            )
        lines.append("  (run with --scaffold to generate stubs automatically)")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Output: JSON
# ---------------------------------------------------------------------------

def format_json(
    folders: list[dict], src_dir: str, project_type: str | None, depth: int, docs_dir: str
) -> str:
    documented = [f for f in folders if f["status"] == "Documented"]
    undocumented = [f for f in folders if f["status"] == "Not documented"]
    shared = [f for f in folders if f["status"] == "—"]
    total = len(documented) + len(undocumented)
    pct = int(len(documented) / total * 100) if total else 100

    modules = []
    for f in folders:
        modules.append({
            "name": f["name"],
            "display_name": f["display_name"],
            "path": f["rel"],
            "type": f["type"],
            "status": f["status"],
            "flow_file": f["flow_file"] if f["flow_file"] != "—" else None,
            "depth": f["depth"],
        })

    payload = {
        "project_type": project_type,
        "src_dir": src_dir,
        "depth": depth,
        "docs_dir": docs_dir,
        "modules": modules,
        "summary": {
            "documented": len(documented),
            "undocumented": len(undocumented),
            "shared": len(shared),
            "total_non_shared": total,
            "coverage_pct": pct,
        },
    }
    return json.dumps(payload, ensure_ascii=False, indent=2)


# ---------------------------------------------------------------------------
# Output: Scaffold stubs
# ---------------------------------------------------------------------------

def scaffold_stubs(folders: list[dict], docs_dir: str) -> None:
    undocumented = [f for f in folders if f["status"] == "Not documented"]
    if not undocumented:
        print("All modules are already documented — nothing to scaffold.")
        return

    created = []
    skipped = []

    for f in undocumented:
        slug = f["name"]
        module_type = base_type(f["type"])
        title = slug.replace("-", " ").replace("_", " ").title()
        stub_dir = os.path.join(docs_dir, "modules", slug)
        stub_path = os.path.join(stub_dir, f"{slug}-module-data-flow.md")

        if os.path.exists(stub_path):
            skipped.append(stub_path)
            continue

        os.makedirs(stub_dir, exist_ok=True)
        content = _SCAFFOLD_STUB.format(title=title, module_type=module_type)
        with open(stub_path, "w", encoding="utf-8") as fh:
            fh.write(content)
        created.append(stub_path)

    if created:
        print(f"Scaffolded {len(created)} stub(s):")
        for p in created:
            print(f"  ✅  {p}")
    if skipped:
        print(f"Skipped {len(skipped)} (already exist):")
        for p in skipped:
            print(f"  —   {p}")


# ---------------------------------------------------------------------------
# Output: Update codebase-map.md
# ---------------------------------------------------------------------------

def build_tree_block(src_dir: str, folders: list[dict], docs_dir: str = "docs") -> str:
    tree = print_tree(src_dir, folders, docs_dir)
    lines = ["```"]
    lines.append(tree)
    lines.append("```")
    return "\n".join(lines)


def build_coverage_table(folders: list[dict]) -> str:
    lines = []
    lines.append("| Module / Folder | Type | Status | Flow file |")
    lines.append("|---|---|---|---|")
    for f in folders:
        icon = f["status_icon"]
        status_text = f"{icon} {f['status']}" if f["status_icon"] != "—" else "— Not required"
        flow = f["flow_file"] if f["flow_file"] != "—" else "—"
        lines.append(f"| `{f['rel']}` | {f['type']} | {status_text} | {flow} |")
    return "\n".join(lines)


def update_codebase_map(map_path: str, src_dir: str, folders: list[dict], docs_dir: str = "docs"):
    if not os.path.exists(map_path):
        print(f"Error: codebase-map.md not found at {map_path}")
        sys.exit(1)

    with open(map_path, "r", encoding="utf-8") as f:
        content = f.read()

    tree_block = build_tree_block(src_dir, folders, docs_dir)
    coverage_table = build_coverage_table(folders)

    # Replace Project Structure section
    content = re.sub(
        r"(## Project Structure\n<!--.*?-->\n\n)```[\s\S]*?```",
        r"\g<1>" + tree_block,
        content,
        flags=re.DOTALL,
    )

    # Replace Coverage Summary table
    content = re.sub(
        r"(## Coverage Summary\n<!--.*?-->\n\n)\|[\s\S]*?\n\n",
        r"\g<1>" + coverage_table + "\n\n",
        content,
        flags=re.DOTALL,
    )

    with open(map_path, "w", encoding="utf-8") as f:
        f.write(content)

    print(f"Updated: {map_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        description="Scan source directory and check documentation coverage."
    )
    parser.add_argument("src_dir", help="Source directory to scan (e.g. src, app, stages)")
    parser.add_argument(
        "--project-type",
        metavar="TYPE",
        choices=VALID_TYPES,
        help=(
            f"Project type — controls module boundary detection heuristic. "
            f"Valid values: {', '.join(VALID_TYPES)}"
        ),
    )
    parser.add_argument(
        "--depth",
        metavar="N",
        type=int,
        default=1,
        help="Number of directory levels to scan for coverage/JSON output (default: 1). Use 2+ for monorepos. Does not affect the printed file tree depth.",
    )
    parser.add_argument(
        "--format",
        metavar="FORMAT",
        choices=["text", "json"],
        default="text",
        dest="output_format",
        help="Output format: text (default) or json",
    )
    parser.add_argument("--tree", action="store_true", help="Print tree view with coverage icons")
    parser.add_argument("--coverage", action="store_true", help="Print coverage summary")
    parser.add_argument("--update", metavar="CODEBASE_MAP", help="Update codebase-map.md in place")
    parser.add_argument(
        "--scaffold",
        action="store_true",
        help="Generate stub module-data-flow.md files for undocumented modules (skips existing files)",
    )
    parser.add_argument("--docs", default="docs", help="Path to docs directory (default: docs)")
    args = parser.parse_args()

    if args.depth < 1:
        print("error: --depth must be at least 1", file=sys.stderr)
        sys.exit(2)

    project_type = args.project_type  # None if not supplied — falls back to web-app behaviour

    folders = find_source_folders(args.src_dir, project_type, args.depth)
    documented = find_documented_modules(args.docs)
    folders = annotate_folders(folders, documented)

    # JSON mode — output and exit
    if args.output_format == "json":
        print(format_json(folders, args.src_dir, project_type, args.depth, args.docs))
        return

    # Default: show both tree and coverage if no specific output flag given
    show_all = not args.tree and not args.coverage and not args.update and not args.scaffold

    if args.tree or show_all:
        print(print_tree(args.src_dir, folders, args.docs))
        print()

    if args.coverage or show_all:
        print(print_coverage(folders, project_type))

    if args.update:
        update_codebase_map(args.update, args.src_dir, folders, args.docs)

    if args.scaffold:
        scaffold_stubs(folders, args.docs)


if __name__ == "__main__":
    main()
