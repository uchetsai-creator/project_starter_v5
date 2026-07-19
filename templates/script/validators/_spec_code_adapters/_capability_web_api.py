"""
_capability_web_api.py — WebAPIAdapter for project_starter_v5 (Phase 52.5).

Capability adapter for web / microservice API projects.
Orchestrates: FastAPIDetector, FlaskDetector, ExpressDetector.

Architecture:
  WebAPIAdapter (this file)
      │  extract_spec() — parses api-contract.md
      │  extract_code() — discovers .py + .js/.ts files, delegates to detector(s)
      ├── FastAPIDetector  (receives .py files)
      ├── FlaskDetector    (receives .py files)
      └── ExpressDetector  (receives .js/.ts files)

Invariants:
  - No framework-specific parsing logic here.
  - Detector selection is the only framework-awareness in this adapter.
  - File discovery lives here, not in detectors.
  - extract_spec() / extract_code() never raise; return [] on any error.
"""
from __future__ import annotations

import os
import re

from _base import FrameworkAdapter, NormalizedEndpoint
from _utils import _parse_field_table

# Detector name → (module_name, class_name, accepted_extensions)
_DETECTORS: dict[str, tuple[str, str, tuple[str, ...]]] = {
    'fastapi': ('fastapi', 'FastAPIDetector', ('.py',)),
    'flask':   ('flask',   'FlaskDetector',   ('.py',)),
    'express': ('express', 'ExpressDetector', ('.js', '.ts', '.mjs', '.cjs')),
}


class WebAPIAdapter(FrameworkAdapter):
    """
    Capability adapter for web API / microservices projects (Phase 52.5).

    Recognized frameworks: fastapi, flask, express.

    Args:
        framework: Optional framework hint (e.g. 'fastapi'). When supplied,
                   only the matching detector is run. When None, all detectors
                   run and results are unioned.
    """

    def __init__(self, framework: str | None = None) -> None:
        self._framework = framework

    # ------------------------------------------------------------------ spec

    def extract_spec(self, spec_path: str) -> list[NormalizedEndpoint]:
        """
        Parse an api-contract.md spec file.

        All web-API frameworks share the same spec format:
          ### POST /orders
          #### Request Body
          | Field | Type | Required | Description |
          | customer_id | int | Yes | ... |
          #### Response Body
          | Field | Type | Description |
          | order_id | int | ... |
        """
        try:
            with open(spec_path, encoding='utf-8') as f:
                text = f.read()
        except OSError:
            return []

        endpoints: list[NormalizedEndpoint] = []
        section_matches = list(re.finditer(
            r'^### (GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\s+(\S+)',
            text, re.MULTILINE | re.IGNORECASE,
        ))

        for idx, match in enumerate(section_matches):
            method = match.group(1).upper()
            path = match.group(2)
            section_start = match.end()
            section_end = (section_matches[idx + 1].start()
                           if idx + 1 < len(section_matches) else len(text))
            section = text[section_start:section_end]

            endpoints.append(NormalizedEndpoint(
                method=method,
                path=path,
                request_fields=_parse_field_table(section, 'Request Body'),
                response_fields=_parse_field_table(section, 'Response Body'),
            ))

        return endpoints

    # ------------------------------------------------------------------ code

    def extract_code(self, src_path: str) -> list[NormalizedEndpoint]:
        """
        Discover source files and delegate to web-API detector(s).

        Discovers .py files for Python frameworks and .js/.ts files for Express.
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

        return self._dispatch_detectors(active_detectors, all_files)
