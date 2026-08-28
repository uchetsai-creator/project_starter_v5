import sys
import tempfile
from pathlib import Path

_ADAPTERS_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "templates" / "script" / "validators" / "_spec_code_adapters"
)
sys.path.insert(0, str(_ADAPTERS_DIR))

from luigi import LuigiDetector  # noqa: E402

sys.path.remove(str(_ADAPTERS_DIR))  # don't leak onto sys.path — see test_ansible_detector.py


def _extract(source: str):
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False, encoding="utf-8") as f:
        f.write(source)
        path = f.name
    try:
        return LuigiDetector().extract([path])
    finally:
        Path(path).unlink()


def test_class_level_parameters_become_input_fields():
    src = """
import luigi

class ExtractTask(luigi.Task):
    run_date = luigi.DateParameter()
    row_limit = luigi.IntParameter()

    def output(self):
        return luigi.LocalTarget("out.csv")
"""
    contracts = _extract(src)
    assert len(contracts) == 1
    fields = {f.name: f.type for f in contracts[0].input_fields}
    assert fields == {"run_date": "date", "row_limit": "int"}


def test_output_fields_are_always_empty():
    src = """
import luigi

class T(luigi.Task):
    path = luigi.Parameter()

    def output(self):
        return luigi.LocalTarget(path=self.path, format=luigi.format.Gzip)
"""
    contracts = _extract(src)
    assert contracts[0].output_fields == []


def test_class_without_task_base_is_ignored():
    src = """
import luigi

class PlainHelper:
    value = luigi.Parameter()
"""
    assert _extract(src) == []


def test_external_task_subclass_is_detected():
    src = """
import luigi

class UpstreamData(luigi.ExternalTask):
    date = luigi.DateParameter()
"""
    contracts = _extract(src)
    assert contracts[0].stage_name == "UpstreamData"


def test_non_parameter_class_attribute_is_not_a_field():
    src = """
import luigi

class T(luigi.Task):
    date = luigi.DateParameter()
    priority = 50  # plain int, not a luigi Parameter

    def run(self):
        pass
"""
    contracts = _extract(src)
    assert {f.name for f in contracts[0].input_fields} == {"date"}
