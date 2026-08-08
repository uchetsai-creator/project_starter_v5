"""Golden drift-detection coverage for the data-pipeline adapters: airflow, dagster,
prefect, luigi. See tests/unit/test_adapter_drift_detection.py for the full rationale.
"""
import os
import subprocess
import sys
from pathlib import Path

_VALIDATORS_DIR = Path(__file__).resolve().parent.parent.parent / "templates/script/validators"
SCRIPT = _VALIDATORS_DIR / "verify_spec_code.py"


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env={**os.environ, "PYTHONUTF8": "1"},
    )


_PIPELINE_SPEC = """\
### ExtractData
#### Input Contract
| Schema | source_path: str |
#### Output Contract
| Schema | row_count: int |
"""


# ---------------------------------------------------------------------------
# Airflow
# ---------------------------------------------------------------------------

_AIRFLOW_CODE_CLEAN = """\
from airflow.decorators import task


class ExtractOutput:
    row_count: int


@task
def ExtractData(source_path: str) -> ExtractOutput:
    ...
"""


def test_airflow_clean_spec_and_code_report_no_mismatches(tmp_path):
    spec = tmp_path / "pipeline-contract.md"
    spec.write_text(_PIPELINE_SPEC, encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    (src / "stages.py").write_text(_AIRFLOW_CODE_CLEAN, encoding="utf-8")

    result = _run("--adapter", "airflow", "--spec", str(spec), "--src", str(src), "--strict")
    assert "No mismatches" in result.stdout, result.stdout
    assert result.returncode == 0


def test_airflow_missing_input_field_is_caught(tmp_path):
    spec = tmp_path / "pipeline-contract.md"
    spec.write_text(_PIPELINE_SPEC, encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    code = _AIRFLOW_CODE_CLEAN.replace("source_path: str", "")
    (src / "stages.py").write_text(code, encoding="utf-8")

    result = _run("--adapter", "airflow", "--spec", str(spec), "--src", str(src), "--strict")
    assert "[FAIL]" in result.stdout, result.stdout
    assert "source_path" in result.stdout, result.stdout
    assert result.returncode == 1


def test_airflow_output_field_type_change_is_caught(tmp_path):
    spec = tmp_path / "pipeline-contract.md"
    spec.write_text(_PIPELINE_SPEC, encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    code = _AIRFLOW_CODE_CLEAN.replace("row_count: int", "row_count: str")
    (src / "stages.py").write_text(code, encoding="utf-8")

    result = _run("--adapter", "airflow", "--spec", str(spec), "--src", str(src), "--strict")
    assert "[FAIL]" in result.stdout, result.stdout
    assert "row_count" in result.stdout, result.stdout
    assert result.returncode == 1


# ---------------------------------------------------------------------------
# Dagster
# ---------------------------------------------------------------------------

_DAGSTER_CODE_CLEAN = """\
from dagster import op


class ExtractOutput:
    row_count: int


@op
def ExtractData(context, source_path: str) -> ExtractOutput:
    ...
"""


def test_dagster_clean_spec_and_code_report_no_mismatches(tmp_path):
    spec = tmp_path / "pipeline-contract.md"
    spec.write_text(_PIPELINE_SPEC, encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    (src / "stages.py").write_text(_DAGSTER_CODE_CLEAN, encoding="utf-8")

    result = _run("--adapter", "dagster", "--spec", str(spec), "--src", str(src), "--strict")
    assert "No mismatches" in result.stdout, result.stdout
    assert result.returncode == 0


def test_dagster_missing_input_field_is_caught(tmp_path):
    spec = tmp_path / "pipeline-contract.md"
    spec.write_text(_PIPELINE_SPEC, encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    code = _DAGSTER_CODE_CLEAN.replace(", source_path: str", "")
    (src / "stages.py").write_text(code, encoding="utf-8")

    result = _run("--adapter", "dagster", "--spec", str(spec), "--src", str(src), "--strict")
    assert "[FAIL]" in result.stdout, result.stdout
    assert "source_path" in result.stdout, result.stdout
    assert result.returncode == 1


# ---------------------------------------------------------------------------
# Prefect
# ---------------------------------------------------------------------------

_PREFECT_CODE_CLEAN = """\
from prefect import task


class ExtractOutput:
    row_count: int


@task
def ExtractData(source_path: str) -> ExtractOutput:
    ...
"""


def test_prefect_clean_spec_and_code_report_no_mismatches(tmp_path):
    spec = tmp_path / "pipeline-contract.md"
    spec.write_text(_PIPELINE_SPEC, encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    (src / "stages.py").write_text(_PREFECT_CODE_CLEAN, encoding="utf-8")

    result = _run("--adapter", "prefect", "--spec", str(spec), "--src", str(src), "--strict")
    assert "No mismatches" in result.stdout, result.stdout
    assert result.returncode == 0


def test_prefect_extra_output_field_is_caught(tmp_path):
    spec = tmp_path / "pipeline-contract.md"
    spec.write_text(_PIPELINE_SPEC, encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    # Drift: code's output class grew an extra field never declared in the spec.
    # A field-level "added_in_code" mismatch is reported as [FAIL] (unlike a whole
    # extra item, which is [WARN] — see verify_spec_code.py's print_report()).
    code = _PREFECT_CODE_CLEAN.replace(
        "class ExtractOutput:\n    row_count: int\n",
        "class ExtractOutput:\n    row_count: int\n    warnings: list\n",
    )
    (src / "stages.py").write_text(code, encoding="utf-8")

    result = _run("--adapter", "prefect", "--spec", str(spec), "--src", str(src), "--strict")
    assert "[FAIL]" in result.stdout, result.stdout
    assert "warnings" in result.stdout, result.stdout
    assert result.returncode == 1


# ---------------------------------------------------------------------------
# Luigi — class-based, input only; output_fields is always [] by design (see
# luigi.py's module docstring), so a spec's Output Contract always reports missing
# for a Luigi stage. Covered explicitly below rather than treated as a false positive.
# ---------------------------------------------------------------------------

_LUIGI_SPEC_INPUT_ONLY = """\
### ExtractTask
#### Input Contract
| Schema | run_date: date, source_path: str |
"""

_LUIGI_CODE_CLEAN = """\
import luigi


class ExtractTask(luigi.Task):
    run_date = luigi.DateParameter()
    source_path = luigi.Parameter()

    def output(self):
        return luigi.LocalTarget(f"extract_{self.run_date}.csv")

    def run(self):
        pass
"""


def test_luigi_clean_spec_and_code_report_no_mismatches(tmp_path):
    spec = tmp_path / "pipeline-contract.md"
    spec.write_text(_LUIGI_SPEC_INPUT_ONLY, encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    (src / "tasks.py").write_text(_LUIGI_CODE_CLEAN, encoding="utf-8")

    result = _run("--adapter", "luigi", "--spec", str(spec), "--src", str(src), "--strict")
    assert "No mismatches" in result.stdout, result.stdout
    assert result.returncode == 0


def test_luigi_missing_parameter_is_caught(tmp_path):
    spec = tmp_path / "pipeline-contract.md"
    spec.write_text(_LUIGI_SPEC_INPUT_ONLY, encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    code = _LUIGI_CODE_CLEAN.replace("    source_path = luigi.Parameter()\n", "")
    (src / "tasks.py").write_text(code, encoding="utf-8")

    result = _run("--adapter", "luigi", "--spec", str(spec), "--src", str(src), "--strict")
    assert "[FAIL]" in result.stdout, result.stdout
    assert "source_path" in result.stdout, result.stdout
    assert result.returncode == 1


def test_luigi_output_contract_in_spec_always_reports_missing():
    """Documents the known, by-design limitation: LuigiDetector never resolves
    output_fields (see luigi.py docstring), so any Output Contract in the spec is
    unverifiable for Luigi and must be checked manually."""
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)
        spec = tmp_path / "pipeline-contract.md"
        spec.write_text(_PIPELINE_SPEC, encoding="utf-8")  # includes an Output Contract
        src = tmp_path / "src"
        src.mkdir()
        (src / "tasks.py").write_text(
            "import luigi\n\n\nclass ExtractData(luigi.Task):\n"
            "    source_path = luigi.Parameter()\n\n"
            "    def output(self):\n        return luigi.LocalTarget('out.csv')\n",
            encoding="utf-8",
        )

        result = _run("--adapter", "luigi", "--spec", str(spec), "--src", str(src), "--strict")
        assert "[FAIL]" in result.stdout, result.stdout
        assert "row_count" in result.stdout, result.stdout
        assert result.returncode == 1
