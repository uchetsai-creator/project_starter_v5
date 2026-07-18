"""
airflow.py — AirflowDetector (+ legacy AirflowAdapter) for project_starter_v5.

Phase 52.5: AirflowDetector is the primary class — it receives pre-discovered
files from DataPipelineAdapter and returns NormalizedStageContract objects.
AirflowAdapter is kept as a backward-compatible shim.

Extracts NormalizedStageContract objects from:
  - Spec: pipeline-contract.md (### Stage sections with #### Input/Output Contract tables)
  - Code: Python files — @task-decorated functions and type-annotated callables

No comparison logic here. All comparison lives in verify_spec_code.py.
"""
from __future__ import annotations

import ast
import os
import re

from _base import Detector, FrameworkAdapter, NormalizedField, NormalizedStageContract

# Placeholder stage names to skip when parsing the spec template
_PLACEHOLDER_NAMES = frozenset({'stage name', '[stage name]', 'stage', ''})


def _annotation_str(node) -> str:
    if node is None:
        return ''
    try:
        return ast.unparse(node)
    except AttributeError:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Constant):
            return str(node.value)
        if isinstance(node, ast.Attribute):
            return f"{_annotation_str(node.value)}.{node.attr}"
        return ''


def _parse_schema_value(value: str) -> list[NormalizedField]:
    """Parse 'field: type, field2: type2' or 'field (type)' patterns."""
    fields = []
    for part in re.split(r'[,\n;]', value):
        part = part.strip().strip('`')
        m = re.match(r'([a-zA-Z_]\w*)\s*[:(]\s*(\w[\w\[\], ]*)', part)
        if m:
            fields.append(NormalizedField(name=m.group(1).strip(),
                                          type=m.group(2).strip()))
    return fields


class AirflowDetector(Detector):
    """
    Framework detector for Apache Airflow (Phase 52.5).

    Receives pre-discovered .py files from DataPipelineAdapter.
    Returns NormalizedStageContract for each @task-decorated function.
    Must not perform file discovery.
    """

    def extract(self, files: list[str]) -> list[NormalizedStageContract]:
        contracts: list[NormalizedStageContract] = []
        for fpath in files:
            if fpath.endswith('.py'):
                contracts.extend(self._parse_file(fpath))
        return contracts

    def _parse_file(self, fpath: str) -> list[NormalizedStageContract]:
        try:
            with open(fpath, encoding='utf-8') as f:
                source = f.read()
            tree = ast.parse(source, filename=fpath)
        except (OSError, SyntaxError):
            return []

        contracts: list[NormalizedStageContract] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue

            is_task = any(
                (isinstance(d, ast.Name) and d.id == 'task') or
                (isinstance(d, ast.Attribute) and d.attr == 'task')
                for d in node.decorator_list
            )
            has_annotations = any(
                a.annotation is not None for a in node.args.args
            )
            if not is_task and not has_annotations:
                continue

            input_fields = [
                NormalizedField(name=a.arg, type=_annotation_str(a.annotation))
                for a in node.args.args
                if a.arg not in ('self', 'context', 'kwargs', 'args')
            ]
            output_fields = []
            if node.returns:
                ret = _annotation_str(node.returns)
                if ret and ret.lower() not in ('none', 'any'):
                    output_fields.append(NormalizedField(name='return', type=ret))

            if input_fields or output_fields:
                contracts.append(NormalizedStageContract(
                    stage_name=node.name,
                    input_fields=input_fields,
                    output_fields=output_fields,
                ))

        return contracts


class AirflowAdapter(FrameworkAdapter):
    """
    Adapter for Apache Airflow (Python) Data Pipeline projects.

    Spec format (pipeline-contract.md):
      ### StageName
      #### Input Contract
      | Schema | field: type, field2: type2 |
      #### Output Contract
      | Schema | out_field: type |

    Code format (Python):
      @task
      def stage_name(field: type, field2: type2) -> OutputType:
          ...
    """

    # ------------------------------------------------------------------ spec

    def extract_spec(self, spec_path: str) -> list[NormalizedStageContract]:
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
        files = (
            [src_path] if os.path.isfile(src_path)
            else [
                os.path.join(root, fname)
                for root, _, fnames in os.walk(src_path)
                for fname in fnames
                if fname.endswith('.py')
            ]
        )
        contracts: list[NormalizedStageContract] = []
        for fpath in files:
            contracts.extend(self._parse_file(fpath))
        return contracts

    def _parse_file(self, fpath: str) -> list[NormalizedStageContract]:
        try:
            with open(fpath, encoding='utf-8') as f:
                source = f.read()
            tree = ast.parse(source, filename=fpath)
        except (OSError, SyntaxError):
            return []

        contracts: list[NormalizedStageContract] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue

            is_task = any(
                (isinstance(d, ast.Name) and d.id == 'task') or
                (isinstance(d, ast.Attribute) and d.attr == 'task')
                for d in node.decorator_list
            )
            has_annotations = any(
                a.annotation is not None for a in node.args.args
            )
            if not is_task and not has_annotations:
                continue

            input_fields = [
                NormalizedField(name=a.arg, type=_annotation_str(a.annotation))
                for a in node.args.args
                if a.arg not in ('self', 'context', 'kwargs', 'args')
            ]
            output_fields = []
            if node.returns:
                ret = _annotation_str(node.returns)
                if ret and ret.lower() not in ('none', 'any'):
                    output_fields.append(NormalizedField(name='return', type=ret))

            if input_fields or output_fields:
                contracts.append(NormalizedStageContract(
                    stage_name=node.name,
                    input_fields=input_fields,
                    output_fields=output_fields,
                ))

        return contracts
