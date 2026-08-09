"""
luigi.py — LuigiDetector for project_starter_v5.

Extracts NormalizedStageContract objects from Luigi pipeline code:
  - Code: `class SomeTask(luigi.Task):` subclasses. Luigi is class-based, unlike
    Airflow/Dagster/Prefect's decorated-function stages — a stage's inputs are
    declared as class-level `luigi.Parameter()` (and subclasses: IntParameter,
    DateParameter, ...) attribute assignments, not function parameters.
  - Output: intentionally always []. Luigi's `output()` method returns a
    Target (e.g. `luigi.LocalTarget(...)`) describing *where* the task writes
    (a file/path), not a typed schema of *what* it writes — there is no
    per-field output contract to resolve here, so this returns [] rather than
    fabricating fields from Target constructor arguments that describe
    storage location, not produced data. Only a stage's inputs are
    comparable for Luigi; a pipeline-contract.md Output Contract for a Luigi
    stage will always show as missing and should be checked manually.
  - Spec: pipeline-contract.md — shared pipeline format, parsed by
    DataPipelineAdapter, not here.
"""
from __future__ import annotations

import ast

from _base import Detector, NormalizedField, NormalizedStageContract

_PARAM_TYPES = {
    'Parameter': 'str',
    'IntParameter': 'int',
    'FloatParameter': 'float',
    'BoolParameter': 'bool',
    'BooleanParameter': 'bool',
    'DateParameter': 'date',
    'DateHourParameter': 'datetime',
    'DateMinuteParameter': 'datetime',
    'DateSecondParameter': 'datetime',
    'DateIntervalParameter': 'str',
    'ListParameter': 'list',
    'DictParameter': 'dict',
    'TupleParameter': 'tuple',
    'PathParameter': 'str',
}


class LuigiDetector(Detector):
    """
    Framework detector for Luigi (data-pipeline).
    Receives pre-discovered .py files from DataPipelineAdapter. Must not perform file discovery.
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
            if not (isinstance(node, ast.ClassDef) and self._is_luigi_task(node)):
                continue

            input_fields = [
                field for stmt in node.body
                if (field := self._param_field(stmt)) is not None
            ]

            contracts.append(NormalizedStageContract(
                stage_name=node.name,
                input_fields=input_fields,
                output_fields=[],
            ))

        return contracts

    @staticmethod
    def _is_luigi_task(node: ast.ClassDef) -> bool:
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id in ('Task', 'ExternalTask'):
                return True
            if isinstance(base, ast.Attribute) and base.attr in ('Task', 'ExternalTask'):
                return True
        return False

    @staticmethod
    def _param_field(stmt) -> NormalizedField | None:
        """A class body statement like `date = luigi.DateParameter()` -> a
        NormalizedField named 'date' typed from the Parameter subclass used."""
        if not (isinstance(stmt, ast.Assign) and len(stmt.targets) == 1
                and isinstance(stmt.targets[0], ast.Name)):
            return None
        value = stmt.value
        if not isinstance(value, ast.Call):
            return None
        func = value.func
        param_cls = func.attr if isinstance(func, ast.Attribute) else getattr(func, 'id', None)
        if not param_cls or not param_cls.endswith('Parameter'):
            return None
        return NormalizedField(name=stmt.targets[0].id, type=_PARAM_TYPES.get(param_cls, 'str'))


if __name__ == '__main__':
    import tempfile
    from pathlib import Path

    src = '''
import luigi

class ExtractTask(luigi.Task):
    run_date = luigi.DateParameter()
    source_path = luigi.Parameter()

    def output(self):
        return luigi.LocalTarget(f"extract_{self.run_date}.csv")

    def run(self):
        pass


class TransformTask(luigi.Task):
    run_date = luigi.DateParameter()
    row_limit = luigi.IntParameter()

    def requires(self):
        return ExtractTask(run_date=self.run_date)

    def output(self):
        return luigi.LocalTarget(f"transform_{self.run_date}.csv")

    def run(self):
        pass


class NotATask:
    """No luigi.Task base — must not be detected as a stage."""
    value = luigi.Parameter()
'''

    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False, encoding="utf-8") as f:
        f.write(src)
        path = f.name

    try:
        detector = LuigiDetector()
        assert detector.extract([]) == [], "extract([]) must return an empty list"

        contracts = detector.extract([path])
        by_name = {c.stage_name: c for c in contracts}

        assert "ExtractTask" in by_name, contracts
        assert "TransformTask" in by_name, contracts
        assert "NotATask" not in by_name, "class without a luigi.Task base must be skipped"

        extract_inputs = {f.name: f.type for f in by_name["ExtractTask"].input_fields}
        assert extract_inputs == {"run_date": "date", "source_path": "str"}

        transform_inputs = {f.name: f.type for f in by_name["TransformTask"].input_fields}
        assert transform_inputs == {"run_date": "date", "row_limit": "int"}

        assert all(c.output_fields == [] for c in contracts), \
            "output_fields must stay [] — Luigi targets don't declare a data schema"
        assert len(contracts) == 2
    finally:
        Path(path).unlink()

    print("[OK] luigi.py self-test passed")
