#!/usr/bin/env python3
"""
new_detector.py — Scaffolds a new framework Detector for verify_spec_code.py (Phase 52.5+).

Covers Situation A from docs/contributing-adapters.md: your framework fits an
existing capability adapter (web-api, cli, data-pipeline, library, llm-app,
iac, mobile) but isn't detected yet. This is the common case — almost every
"my tool isn't supported" request is Situation A, not a brand-new capability.

Generates:
  templates/script/validators/_spec_code_adapters/<name>.py
      A Detector stub (extract() + _parse_file() + a self-test skeleton).
  Registers <name> in the target capability's _DETECTORS dict, e.g.:
  templates/script/validators/_spec_code_adapters/_capability_web_api.py

Does NOT scaffold Situation B (an entirely new project type / capability
adapter) — that still needs the manual steps in
docs/contributing-adapters.md, since it requires a real decision about
whether an existing NormalizedForm fits or a new one is needed.

Usage:
  python3 templates/script/generators/new_detector.py --list-capabilities
  python3 templates/script/generators/new_detector.py --capability web-api --name django
  python3 templates/script/generators/new_detector.py --capability cli --name typer --ext .py
  python3 templates/script/generators/new_detector.py --capability web-api --name django --alias
  python3 templates/script/generators/new_detector.py --capability web-api --name django --dry-run
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_VALIDATORS_DIR = Path(__file__).resolve().parent.parent / "validators"
_ADAPTERS_DIR = _VALIDATORS_DIR / "_spec_code_adapters"
_VERIFY_SPEC_CODE = _VALIDATORS_DIR / "verify_spec_code.py"

# capability key -> capability file, its NormalizedForm, its FrameworkAdapter class,
# and a sensible default file extension for a first-cut detector.
_CAPABILITIES: dict[str, dict[str, str]] = {
    "web-api":       {"file": "_capability_web_api.py",  "normalized": "NormalizedEndpoint",      "adapter_class": "WebAPIAdapter",       "default_ext": ".py"},
    "cli":           {"file": "_capability_cli.py",      "normalized": "NormalizedCommand",       "adapter_class": "CLIAdapter",          "default_ext": ".py"},
    "data-pipeline": {"file": "_capability_pipeline.py", "normalized": "NormalizedStageContract", "adapter_class": "DataPipelineAdapter", "default_ext": ".py"},
    "library":       {"file": "_capability_library.py",  "normalized": "NormalizedFunction",      "adapter_class": "LibraryAdapter",      "default_ext": ".py"},
    "llm-app":       {"file": "_capability_llm.py",      "normalized": "NormalizedTool",          "adapter_class": "LLMAdapter",          "default_ext": ".py"},
    "iac":           {"file": "_capability_iac.py",      "normalized": "NormalizedResource",      "adapter_class": "IaCAdapter",          "default_ext": ".tf"},
    "mobile":        {"file": "_capability_mobile.py",   "normalized": "NormalizedScreen",        "adapter_class": "MobileAdapter",       "default_ext": ".tsx"},
    "logging":       {"file": "_capability_logging.py",  "normalized": "NormalizedLogPoint",      "adapter_class": "LoggingAdapter",      "default_ext": ".py"},
}

_DETECTORS_DICT_RE = re.compile(
    r"_DETECTORS: dict\[str, tuple\[str, str, tuple\[str, \.\.\.\]\]\] = \{\n(.*?)\n\}", re.S,
)
_ADAPTER_REGISTRY_RE = re.compile(
    r"ADAPTER_REGISTRY: dict\[str, tuple\[str, str, str \| None\]\] = \{\n(.*?)\n\}", re.S,
)


def _class_name(name: str) -> str:
    return "".join(part.capitalize() for part in re.split(r"[_\-]+", name) if part) + "Detector"


def _detector_template(name: str, class_name: str, normalized: str, capability: str, extensions: list[str]) -> str:
    ext_repr = ", ".join(repr(e) for e in extensions)
    return f'''"""
{name}.py — {class_name} for project_starter_v5.

Scaffolded by new_detector.py for the "{capability}" capability.
Receives pre-discovered files from the capability adapter and returns
{normalized} objects. Must not perform file discovery or spec parsing —
both are the capability adapter's job.

TODO: replace the parsing logic in _parse_file() with real detection for
{name}, then replace the self-test at the bottom with a real round-trip check.

Before you call this done, check it against every item below — each one is a real bug
found by testing an existing detector against hand-written code, not a hypothetical:
  1. Type vocabulary — don't hand-roll a type comparison; verify_spec_code.py's compare()
     already normalizes spec-prose words (string/boolean/integer) against your language's
     native type names. Just don't bypass it with your own equality check.
  2. Output/return fields — if {normalized} has a response/output side, do not fabricate a
     single placeholder field. If your language is Python, use
     `_resolve_output_fields(tree, func_node)` from _utils.py (resolves class/dataclass
     fields, dict literals, constructor kwargs). Otherwise write the equivalent and return
     [] (not a fake field) when you truly can't resolve real names.
  3. Key/identifier syntax normalization — if there's more than one valid way to write the
     same identifier in your ecosystem, check whether it needs normalizing before
     comparison (see _normalize_path() in verify_spec_code.py for the pattern).
  4. Don't match by method/keyword name alone — verify the receiver/context is actually an
     instance of your framework's construct, not anything that happens to share a name
     (see express.py's _find_router_identifiers() for the pattern).
  5. Nested structure leakage — if your source format nests (blocks/maps/sub-objects), track
     depth/scope explicitly; a flat regex over the whole block will pick up keys that belong
     to a deeper level (see terraform.py's _top_level_keys() for the pattern).
  6. More than one idiomatic way to write the same construct — real code commonly has 2-3
     equally valid styles for the thing you're detecting. Check what idiomatic code in that
     ecosystem actually looks like, not just the first example you write.
  7. Scalar attributes outside the per-field list — if {normalized} has a single-value
     attribute that isn't part of its fields list, confirm compare() actually checks it.

Test against real code you write by hand, not only a fixture that already matches your
regex — every pitfall above was only found that way. Full write-up:
docs/contributing-adapters.md → "Common pitfalls".
"""
from __future__ import annotations

from _base import Detector, {normalized}, NormalizedField

_EXTENSIONS = ({ext_repr},)


class {class_name}(Detector):
    """
    Framework detector for {name} ({capability}).
    Receives pre-discovered files from its capability adapter. Must not perform file discovery.
    """

    def extract(self, files: list[str]) -> list[{normalized}]:
        items: list[{normalized}] = []
        for fpath in files:
            if fpath.endswith(_EXTENSIONS):
                items.extend(self._parse_file(fpath))
        return items

    def _parse_file(self, fpath: str) -> list[{normalized}]:
        try:
            with open(fpath, encoding='utf-8') as f:
                source = f.read()
        except OSError:
            return []
        # TODO: parse `source` (regex or a real parser) and return {normalized} objects.
        # See the module docstring's pitfall checklist before considering this done.
        _ = source
        return []


if __name__ == '__main__':
    # TODO: write a temp source file, call extract([temp_path]), assert the
    # expected {normalized} objects come back — see _example_adapter.py for the pattern.
    detector = {class_name}()
    assert detector.extract([]) == [], "extract([]) must return an empty list"
    print("[OK] {name}.py self-test passed")
'''


def _capability_file_path(capability: str) -> Path:
    return _ADAPTERS_DIR / _CAPABILITIES[capability]["file"]


def _insert_into_dict(text: str, pattern: re.Pattern, key: str, new_line: str, label: str, path: Path) -> str:
    m = pattern.search(text)
    if not m:
        print(f"error: could not find the expected dict in {path}", file=sys.stderr)
        sys.exit(1)
    body = m.group(1)
    if re.search(rf"^\s*'{re.escape(key)}':", body, re.M):
        print(f"error: '{key}' is already registered in {label} ({path.name}) — "
              f"pick a different --name, or edit {path.name} manually", file=sys.stderr)
        sys.exit(1)
    new_body = body.rstrip() + "\n" + new_line
    return text[:m.start(1)] + new_body + text[m.end(1):]


def _register_detector(capability_path: Path, key: str, class_name: str, extensions: list[str], dry_run: bool) -> str:
    text = capability_path.read_text(encoding="utf-8")
    ext_repr = ", ".join(repr(e) for e in extensions)
    m = _DETECTORS_DICT_RE.search(text)
    indent = "    "
    if m:
        indent_match = re.search(r"\n( +)'", m.group(1))
        if indent_match:
            indent = indent_match.group(1)
    new_line = f"{indent}'{key}': ('{key}', '{class_name}', ({ext_repr},)),"
    new_text = _insert_into_dict(text, _DETECTORS_DICT_RE, key, new_line, "_DETECTORS", capability_path)
    if not dry_run:
        capability_path.write_text(new_text, encoding="utf-8")
    return new_line


def _register_alias(key: str, capability: str, dry_run: bool) -> str:
    text = _VERIFY_SPEC_CODE.read_text(encoding="utf-8")
    module = _CAPABILITIES[capability]["file"][:-3]
    cls = _CAPABILITIES[capability]["adapter_class"]
    m = _ADAPTER_REGISTRY_RE.search(text)
    indent = "    "
    if m:
        indent_match = re.search(r"\n( +)'", m.group(1))
        if indent_match:
            indent = indent_match.group(1)
    new_line = f"{indent}'{key}': ('{module}', '{cls}', '{key}'),"
    new_text = _insert_into_dict(text, _ADAPTER_REGISTRY_RE, key, new_line, "ADAPTER_REGISTRY", _VERIFY_SPEC_CODE)
    if not dry_run:
        _VERIFY_SPEC_CODE.write_text(new_text, encoding="utf-8")
    return new_line


def main() -> None:
    # Force UTF-8 stdout/stderr — without this, a non-ASCII character (e.g. "→")
    # crashes print() with UnicodeEncodeError on a non-UTF-8-default Windows console
    # (confirmed in CI on windows-latest; see orchestrator.py's main() and CHANGELOG.md).
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")
        sys.stderr.reconfigure(encoding="utf-8")  # type: ignore[union-attr]  # guard above only narrows sys.stdout

    parser = argparse.ArgumentParser(
        description="Scaffold a new framework Detector for an existing capability adapter "
                    "(Situation A in docs/contributing-adapters.md).",
    )
    parser.add_argument("--capability", choices=sorted(_CAPABILITIES), help="Target capability adapter")
    parser.add_argument("--name", help="Framework key, e.g. 'django' — used as module filename and --framework value")
    parser.add_argument(
        "--ext", action="append", dest="extensions",
        help="File extension this detector handles (repeatable). Defaults to the capability's typical extension.",
    )
    parser.add_argument(
        "--alias", action="store_true",
        help="Also register a standalone --adapter <name> alias in verify_spec_code.py ADAPTER_REGISTRY",
    )
    parser.add_argument("--force", action="store_true", help="Overwrite the detector file if it already exists")
    parser.add_argument("--dry-run", action="store_true", help="Print what would be created/changed without writing files")
    parser.add_argument("--list-capabilities", action="store_true", help="List capabilities and their NormalizedForm, then exit")
    args = parser.parse_args()

    if args.list_capabilities:
        print("Capabilities (--capability <key>):\n")
        for key, info in _CAPABILITIES.items():
            print(f"  {key:<14} {info['normalized']:<24} ({info['file']})")
        return

    if not args.capability or not args.name:
        parser.error("--capability and --name are required (or pass --list-capabilities)")

    name = args.name.strip().lower()
    if not re.match(r"^[a-z][a-z0-9_]*$", name):
        parser.error("--name must be lowercase, start with a letter, and contain only letters/digits/underscore")

    extensions = args.extensions or [_CAPABILITIES[args.capability]["default_ext"]]
    class_name = _class_name(name)
    normalized = _CAPABILITIES[args.capability]["normalized"]

    detector_path = _ADAPTERS_DIR / f"{name}.py"
    if detector_path.exists() and not args.force:
        print(f"error: {detector_path} already exists — pass --force to overwrite", file=sys.stderr)
        sys.exit(1)

    capability_path = _capability_file_path(args.capability)
    if not capability_path.exists():
        print(f"error: capability file not found: {capability_path}", file=sys.stderr)
        sys.exit(1)

    content = _detector_template(name, class_name, normalized, args.capability, extensions)

    if args.dry_run:
        print(f"--- would write {detector_path} ---")
        print(content)
    else:
        detector_path.write_text(content, encoding="utf-8")
        print(f"[OK] Created {detector_path}")

    new_line = _register_detector(capability_path, name, class_name, extensions, args.dry_run)
    verb = "would add" if args.dry_run else "Added"
    print(f"[OK] {verb} to {capability_path.name} _DETECTORS:\n    {new_line.strip()}")

    if args.alias:
        alias_line = _register_alias(name, args.capability, args.dry_run)
        print(f"[OK] {verb} alias to verify_spec_code.py ADAPTER_REGISTRY:\n    {alias_line.strip()}")

    print()
    print("Next steps:")
    print(f"  1. Implement _parse_file() in {detector_path.name}")
    print(f"  2. Replace the self-test at the bottom of {detector_path.name} with a real round-trip check")
    print(f"  3. Run: python3 {detector_path}")
    if not args.alias:
        print(f"  4. (Optional) re-run with --alias to also register --adapter {name} in ADAPTER_REGISTRY")
    print("  5. (Optional) add a pre-commit trigger + spec_code_* config — "
          "see README.md -> Spec <-> Code Validator -> Wiring it into pre-commit")


if __name__ == "__main__":
    main()
