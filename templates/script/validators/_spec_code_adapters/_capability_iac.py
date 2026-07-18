"""
_capability_iac.py — IaCAdapter for project_starter_v5 (Phase 52.5).

Capability adapter for Infrastructure-as-Code (IaC / DevOps) projects.
Orchestrates: TerraformDetector, PulumiDetector.

Architecture:
  IaCAdapter (this file)
      │  extract_spec() — parses topology.md
      │  extract_code() — discovers .tf + .py files, delegates to detector(s)
      ├── TerraformDetector  (receives .tf files)
      └── PulumiDetector     (receives .py files)

Invariants:
  - No framework-specific parsing logic here.
  - Detector selection is the only framework-awareness in this adapter.
  - File discovery lives here, not in detectors.
  - extract_spec() / extract_code() never raise; return [] on any error.
"""
from __future__ import annotations

import os
import re

from _base import FrameworkAdapter, NormalizedResource

# Detector name → (module_name, class_name, accepted_extensions)
_DETECTORS: dict[str, tuple[str, str, tuple[str, ...]]] = {
    'terraform': ('terraform', 'TerraformDetector', ('.tf',)),
    'pulumi':    ('pulumi',    'PulumiDetector',    ('.py',)),
}


def _parse_config_table(section: str) -> list[str]:
    """Return config key names from a '#### Configuration' Markdown table."""
    h = re.search(r'^#### Configuration', section, re.MULTILINE)
    if not h:
        return []
    table_text = section[h.end():]
    next_h = re.search(r'^#{3,4} ', table_text, re.MULTILINE)
    if next_h:
        table_text = table_text[:next_h.start()]

    keys: list[str] = []
    for row in re.finditer(r'(?m)^\|(.+)\|$', table_text):
        cols = [c.strip().strip('`') for c in row.group(1).split('|')]
        key = cols[0] if cols else ''
        if not key or re.match(r'^[-:]+$', key) or key.lower() in (
            'key', 'name', 'attribute', 'property'
        ):
            continue
        keys.append(key)
    return keys


class IaCAdapter(FrameworkAdapter):
    """
    Capability adapter for IaC / DevOps projects (Phase 52.5).

    Recognized frameworks: terraform, pulumi.

    Args:
        framework: Optional framework hint (e.g. 'terraform'). When supplied,
                   only the matching detector is run. When None, all detectors
                   run and results are unioned.
    """

    def __init__(self, framework: str | None = None) -> None:
        self._framework = framework

    # ------------------------------------------------------------------ spec

    def extract_spec(self, spec_path: str) -> list[NormalizedResource]:
        """
        Parse a topology.md spec file.

        Both Terraform and Pulumi share the same spec format:
          ### web_server (aws_instance)
          #### Configuration
          | Key | Value | Description |
          |---|---|---|
          | instance_type | t3.micro | EC2 instance type |
        """
        try:
            with open(spec_path, encoding='utf-8') as f:
                text = f.read()
        except OSError:
            return []

        resources: list[NormalizedResource] = []
        section_matches = list(re.finditer(
            r'^### (`?)(\w+)\1(?:\s+\(([^)]+)\))?',
            text, re.MULTILINE,
        ))

        for idx, match in enumerate(section_matches):
            label = match.group(2)
            rtype = (match.group(3) or '').strip()
            section_start = match.end()
            section_end = (section_matches[idx + 1].start()
                           if idx + 1 < len(section_matches) else len(text))
            section = text[section_start:section_end]

            resources.append(NormalizedResource(
                name=label,
                resource_type=rtype,
                config_keys=_parse_config_table(section),
            ))

        return resources

    # ------------------------------------------------------------------ code

    def extract_code(self, src_path: str) -> list[NormalizedResource]:
        """
        Discover .tf and .py files and delegate to IaC detector(s).

        With framework hint: only the matching detector runs.
        Without hint: all detectors run and results are unioned.
        """
        active_detectors = (
            {self._framework: _DETECTORS[self._framework]}
            if self._framework and self._framework in _DETECTORS
            else _DETECTORS
        )

        # Collect the union of all extensions needed by active detectors
        needed_exts: set[str] = set()
        for _, _, exts in active_detectors.values():
            needed_exts.update(exts)

        all_files = (
            [src_path] if os.path.isfile(src_path)
            else [
                os.path.join(root, fname)
                for root, _, fnames in os.walk(src_path)
                for fname in fnames
                if any(fname.endswith(ext) for ext in needed_exts)
            ]
        )

        results: list[NormalizedResource] = []
        for detector_key, (module_name, class_name, _exts) in active_detectors.items():
            try:
                import importlib
                mod = importlib.import_module(module_name)
                cls = getattr(mod, class_name)
                results.extend(cls().extract(all_files))
            except Exception:  # noqa: BLE001
                pass

        return results
