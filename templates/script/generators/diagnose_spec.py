#!/usr/bin/env python3
"""
diagnose_spec.py — classify spec quality problems as project-level or framework-level.

Accepts either verify_content.py --json output (preferred) or
verify_docs.py --content --json output. Format is auto-detected.

  verify_content.py format: {"documents": [...]}  — documents[].{name, present, quality, issues}
  verify_docs.py format:    {"results": [...]}     — results[].{doc, status, content}

For verify_docs.py format, each fill-quality gap is classified by checking whether
the framework template already contains guidance for that section:

  Project-level gap   → template has the section; the project didn't fill it in.
  Framework-level gap → template is missing the section; no guidance was provided.

For verify_content.py format, all quality issues are treated as project-level gaps
(checker-detected issues mean template sections exist but content is wrong or missing).

For framework-level gaps (verify_docs.py format only), calls `propose_framework_fix.py`
to open a PR on project_starter_v4 with a template placeholder (round 1).
Round 2 writes remaining framework gaps to logs/framework-gaps.md instead of
opening more PRs, enforcing the 2-round iteration limit.

Usage:
  # Pipe verify_content.py output directly (preferred):
  python3 docs/script/validators/verify_content.py --project-type web-app --json \\
    | python3 templates/script/generators/diagnose_spec.py --project-type web-app

  # Pipe verify_docs.py output directly:
  python3 docs/script/validators/verify_docs.py --project-type web-app --content --json \\
    | python3 templates/script/generators/diagnose_spec.py --project-type web-app

  # Or from a saved file:
  python3 templates/script/generators/diagnose_spec.py \\
      --project-type web-app --input verify-output.json

  # Round 2 (after merging round-1 PRs):
  python3 docs/script/validators/verify_docs.py --project-type web-app --content --json \\
    | python3 templates/script/generators/diagnose_spec.py --project-type web-app --round 2

  # Dry-run (no PRs opened, no files written):
  ... | python3 templates/script/generators/diagnose_spec.py --project-type web-app --dry-run

Required: set PROJECT_STARTER_FRAMEWORK_REPO to your fork before running:
  export PROJECT_STARTER_FRAMEWORK_REPO=your-org/your-repo
"""

import argparse
import json
import os
import subprocess
import sys
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
PROPOSE_SCRIPT = SCRIPT_DIR / "propose_framework_fix.py"

# Maximum self-improving rounds before remaining gaps are logged for manual triage.
MAX_ROUNDS = 2


# ── Template helpers ──────────────────────────────────────────────────────────

def find_template_content(doc_path: str, templates_dir: Path) -> str | None:
    """Return the text of the framework template for a given doc path, or None."""
    candidate = templates_dir / doc_path
    if candidate.exists():
        return candidate.read_text(encoding="utf-8")
    # Try without subdir prefix (e.g. "architecture.md" → architecture/architecture.md)
    stem = Path(doc_path).name
    for subdir in ("specs", "architecture", "business"):
        alt = templates_dir / subdir / stem
        if alt.exists():
            return alt.read_text(encoding="utf-8")
    return None


def section_in_template(section_name: str, template_content: str) -> bool:
    """Return True if the template contains a heading matching section_name."""
    needle = section_name.lstrip("#").strip().lower()
    for line in template_content.splitlines():
        if line.startswith("#"):
            heading = line.lstrip("#").strip().lower()
            if heading == needle or needle in heading:
                return True
    return False


def classify_gap(doc_path: str, section: str, templates_dir: Path) -> str:
    """Return 'framework' or 'project' for a fill-quality gap."""
    content = find_template_content(doc_path, templates_dir)
    if content is None:
        return "framework"  # Template file missing entirely
    if not section_in_template(section, content):
        return "framework"  # Template exists but lacks this section
    return "project"


# ── PR proposal ───────────────────────────────────────────────────────────────

def propose_fix(
    project_type: str,
    doc_path: str,
    gap_description: str,
    framework_repo: str,
    dry_run: bool,
) -> str:
    """Call propose_framework_fix.py and return its stdout output."""
    cmd = [
        sys.executable, str(PROPOSE_SCRIPT),
        "--type", project_type,
        "--document", doc_path,
        "--gap-description", gap_description,
        "--framework-repo", framework_repo,
    ]
    if dry_run:
        cmd.append("--dry-run")
    result = subprocess.run(cmd, capture_output=True, text=True)
    out = result.stdout.strip()
    if result.returncode != 0:
        err = result.stderr.strip()
        return f"[error] {err}" if err else "[error] propose_framework_fix.py failed"
    return out


# ── Gap log ───────────────────────────────────────────────────────────────────

def write_gaps_log(gaps: list[dict], logs_dir: Path, dry_run: bool) -> Path:
    """Append remaining framework gaps to logs/framework-gaps.md."""
    log_path = logs_dir / "framework-gaps.md"
    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    rows = "\n".join(
        f"| `{g['doc']}` | `{g['section']}` | {g['type']} | {now} | Open |"
        for g in gaps
    )
    header = (
        "# Framework Gaps — Manual Triage\n\n"
        "Gaps remaining after the 2-round auto-fix limit.\n"
        "Review each row and fix the template manually, then delete the row.\n\n"
        "| Document | Section | Project type | Logged | Status |\n"
        "|---|---|---|---|---|\n"
    )
    if dry_run:
        print(f"  [dry-run] would write {len(gaps)} gap(s) to {log_path}")
        return log_path
    logs_dir.mkdir(parents=True, exist_ok=True)
    if log_path.exists():
        existing = log_path.read_text(encoding="utf-8").rstrip()
        log_path.write_text(existing + f"\n{rows}\n", encoding="utf-8")
    else:
        log_path.write_text(header + rows + "\n", encoding="utf-8")
    return log_path


# ── Main ──────────────────────────────────────────────────────────────────────

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Classify spec quality gaps and open framework fix PRs (max 2 rounds)."
    )
    parser.add_argument("--project-type", required=True, help="Project type (e.g. web-app)")
    parser.add_argument(
        "--input", help="Path to verify_docs.py --json output file (default: read from stdin)"
    )
    parser.add_argument(
        "--round", type=int, choices=[1, 2], default=1, dest="round_num",
        help="Iteration round (1 = open PRs; 2 = log remaining gaps, no more PRs)"
    )
    parser.add_argument(
        "--templates-dir",
        help="Path to the templates directory to check for sections "
             "(default: templates/ if present, else docs/)"
    )
    parser.add_argument(
        "--framework-repo", default=os.environ.get("PROJECT_STARTER_FRAMEWORK_REPO"),
        help="GitHub repo to open PRs on (owner/repo). "
             "Defaults to $PROJECT_STARTER_FRAMEWORK_REPO."
    )
    parser.add_argument(
        "--logs-dir", default="logs",
        help="Directory for logs/framework-gaps.md (default: logs/)"
    )
    parser.add_argument(
        "--dry-run", action="store_true",
        help="Show what would happen without creating PRs or writing files"
    )
    args = parser.parse_args()

    if not args.framework_repo:
        print(
            "❌ PROJECT_STARTER_FRAMEWORK_REPO is not set.\n"
            "   Export it before running:\n"
            "     export PROJECT_STARTER_FRAMEWORK_REPO=your-org/your-repo",
            file=sys.stderr,
        )
        return 1

    # Load verify_docs.py JSON output
    try:
        if args.input:
            data = json.loads(Path(args.input).read_text(encoding="utf-8"))
        else:
            data = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError) as exc:
        print(f"❌ Could not read input: {exc}", file=sys.stderr)
        return 1

    # Resolve templates directory
    if args.templates_dir:
        templates_dir = Path(args.templates_dir)
    else:
        cwd = Path.cwd()
        if (cwd / "templates").exists():
            templates_dir = cwd / "templates"          # framework repo (new structure)
        elif (cwd / "docs" / "templates").exists():
            templates_dir = cwd / "docs" / "templates"  # legacy
        elif (cwd / "docs").exists():
            templates_dir = cwd / "docs"               # user project
        else:
            templates_dir = cwd

    project_type = args.project_type

    framework_gaps: list[dict] = []
    project_gaps: list[dict] = []
    missing_docs: list[str] = []

    # Auto-detect input format: verify_content.py emits "documents"; verify_docs.py emits "results".
    if "documents" in data:
        # verify_content.py --json format: documents[].{name, present, quality, issues}
        for r in data.get("documents", []):
            doc = r.get("name", "")
            if not r.get("present"):
                missing_docs.append(doc)
            elif r.get("quality") == "fail":
                for issue in r.get("issues", []):
                    project_gaps.append({"doc": doc, "section": issue, "type": project_type})
    else:
        # verify_docs.py --content --json format: results[].{doc, status, content}
        for r in data.get("results", []):
            doc = r.get("doc", "")
            status = r.get("status", "")
            content_info = r.get("content") or {}

            if status == "missing_required":
                missing_docs.append(doc)
                continue

            if status != "present" or not content_info:
                continue

            content_status = content_info.get("status", "full")
            unfilled = content_info.get("unfilled_sections") or []

            if content_status in ("partial", "poor") and unfilled:
                for section in unfilled:
                    cls = classify_gap(doc, section, templates_dir)
                    entry = {"doc": doc, "section": section, "type": project_type}
                    if cls == "framework":
                        framework_gaps.append(entry)
                    else:
                        project_gaps.append(entry)

    # ── Report ────────────────────────────────────────────────────────────────
    dry_tag = " [dry-run]" if args.dry_run else ""
    print(f"\n📊 Spec diagnosis — {project_type} · round {args.round_num}{dry_tag}\n")
    print(f"  Missing required docs : {len(missing_docs)}")
    print(f"  Framework-level gaps  : {len(framework_gaps)}")
    print(f"  Project-level gaps    : {len(project_gaps)}")

    if missing_docs:
        print("\n📋 Missing required documents (create these in your project):")
        for doc in missing_docs:
            print(f"  - {doc}")

    if project_gaps:
        print("\n📋 Project-level gaps (template has the section — fill it in):")
        for g in project_gaps:
            print(f"  - {g['doc']}: {g['section']}")

    if not framework_gaps:
        if not project_gaps and not missing_docs:
            print("\n✅ No spec quality issues found.")
        return 0

    if args.round_num >= MAX_ROUNDS:
        # Round 2: log remaining gaps, do not open more PRs
        print(f"\n📋 Framework-level gaps — logging to logs/framework-gaps.md (round {MAX_ROUNDS} limit reached):")
        for g in framework_gaps:
            print(f"  - {g['doc']}: {g['section']}")
        log_path = write_gaps_log(framework_gaps, Path(args.logs_dir), args.dry_run)
        if not args.dry_run:
            print(f"\n  Written to: {log_path}")
        print(f"\n⏹  Round {MAX_ROUNDS} complete — iteration limit reached.")
        print("   Review logs/framework-gaps.md and address remaining gaps manually.")
    else:
        # Round 1: open a PR for each framework-level gap
        print(f"\n🔧 Opening framework fix PRs (round 1){dry_tag}:")
        for g in framework_gaps:
            gap_desc = g["section"].lstrip("#").strip()
            print(f"\n  → {g['doc']}: {gap_desc}")
            output = propose_fix(project_type, g["doc"], gap_desc, args.framework_repo, args.dry_run)
            print(f"    {output}")
        print(
            f"\n✅ Round 1 complete. Merge or skip the PRs above, "
            f"then re-run with --round 2."
        )

    return 0


if __name__ == "__main__":
    sys.exit(main())
