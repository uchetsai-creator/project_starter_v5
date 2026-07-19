"""
_capability_pipeline.py — DataPipelineAdapter for project_starter_v5 (Phase 52.5).

Capability adapter for data / ML pipelines.
Orchestrates: AirflowDetector, DagsterDetector, PrefectDetector.

Architecture:
  DataPipelineAdapter (this file)
      │  extract_spec() — parses pipeline-contract.md
      │  extract_code() — discovers .py files, delegates to detector(s)
      ├── AirflowDetector
      ├── DagsterDetector
      └── PrefectDetector

Invariants:
  - No framework-specific parsing logic here.
  - Detector selection is the only framework-awareness in this adapter.
  - File discovery lives here, not in detectors.
  - extract_spec() / extract_code() never raise; return [] on any error.
"""
from __future__ import annotations

import os
import re

from _base import FrameworkAdapter, NormalizedField, NormalizedStageContract
from _utils import _PLACEHOLDER_NAMES, _parse_schema_value

_DETECTORS: dict[str, tuple[str, str, tuple[str, ...]]] = {
    'airflow': ('airflow', 'AirflowDetector', ('.py',)),
    'dagster': ('dagster', 'DagsterDetector', ('.py',)),
    'prefect': ('prefect', 'PrefectDetector', ('.py',)),
}



class DataPipelineAdapter(FrameworkAdapter):
    """
    Capability adapter for data / ML pipeline projects (Phase 52.5).

    Recognized frameworks: airflow, dagster, prefect.

    Args:
        framework: Optional framework hint (e.g. 'airflow'). When supplied,
                   only the matching detector is run. When None, all detectors
                   run and results are unioned.
    """

    def __init__(self, framework: str | None = None) -> None:
        self._framework = framework

    # ------------------------------------------------------------------ spec

    def extract_spec(self, spec_path: str) -> list[NormalizedStageContract]:
        """
        Parse a pipeline-contract.md spec file.

        All pipeline frameworks share the same spec format:
          ### StageName
          #### Input Contract
          | Schema | field: type, field2: type2 |
          #### Output Contract
          | Schema | out_field: type |
        """
        try:
            with open(spec_path, encoding='utf-8') as f:
                text = f.read()
        except OSError:
            return []

        contracts: list[NormalizedStageContract] = []
        stage_matches = list(re.finditer(r'^### (.+?)$', text, re.MULTILINE))

        for idx, match in enumerate(stage_matches):
            raw_name = match.group(1).strip().strip('`[]')
            if raw_name.lower() in _PLACEHOLDER_NAMES:
                continue

            section_start = match.end()
            section_end = (stage_matches[idx + 1].start()
                           if idx + 1 < len(stage_matches) else len(text))
            section = text[section_start:section_end]

            contracts.append(NormalizedStageContract(
                stage_name=raw_name,
                input_fields=self._contract_fields(section, 'Input'),
                output_fields=self._contract_fields(section, 'Output'),
            ))

        return contracts

    def _contract_fields(self, section: str, kind: str) -> list[NormalizedField]:
        header = re.search(rf'^#### {kind} Contract', section, re.MULTILINE)
        if not header:
            return []
        subsection = section[header.end():]
        next_header = re.search(r'^#{3,4} ', subsection, re.MULTILINE)
        if next_header:
            subsection = subsection[:next_header.start()]
        schema_m = re.search(r'\|\s*Schema\s*\|\s*(.+?)\s*\|', subsection)
        if not schema_m:
            return []
        return _parse_schema_value(schema_m.group(1))

    # ------------------------------------------------------------------ code

    def extract_code(self, src_path: str) -> list[NormalizedStageContract]:
        """
        Discover .py files and delegate to pipeline detector(s).

        With framework hint: only the matching detector runs.
        Without hint: all detectors run and results are unioned.
        """
        active_detectors = (
            {self._framework: _DETECTORS[self._framework]}
            if self._framework and self._framework in _DETECTORS
            else _DETECTORS
        )

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
