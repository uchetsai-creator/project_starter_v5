import sys
from pathlib import Path

sys.path.insert(
    0,
    str(Path(__file__).resolve().parent.parent.parent / "templates/script/validators"),
)
from verify_module_docs import (
    check_background_job,
    check_feature,
    check_pipeline_stage,
    check_quality,
    check_shared_utility,
    detect_module_type,
)


# ---------------------------------------------------------------------------
# detect_module_type
# ---------------------------------------------------------------------------

def test_detect_module_type_canonical_pipeline_stage():
    assert detect_module_type(["# My Module", "Module type: Pipeline Stage"]) == "Pipeline Stage"


def test_detect_module_type_bold_variant_feature():
    assert detect_module_type(["# My Module", "**Type:** Feature"]) == "Feature"


def test_detect_module_type_background_job():
    assert detect_module_type(["Module type: Background Job"]) == "Background Job"


def test_detect_module_type_shared_utility():
    assert detect_module_type(["Module type: Shared Utility"]) == "Shared Utility"


def test_detect_module_type_returns_none_when_missing():
    assert detect_module_type(["# My Module", "No type here"]) is None


# ---------------------------------------------------------------------------
# check_pipeline_stage
# ---------------------------------------------------------------------------

_VALID_PIPELINE = [
    "Module type: Pipeline Stage",
    "Input:",
    "  Source: S3 bucket",
    "  Format: CSV",
    "  Schema: source_schema",
    "↓",
    "Output:",
    "  Destination: PostgreSQL",
    "  Format: rows",
    "Error Handling:",
    "  transient: retry 3 times",
    "  missing_input: skip stage",
    "  default: log and alert",
]


def test_check_pipeline_stage_valid_no_issues():
    assert check_pipeline_stage(_VALID_PIPELINE) == []


def test_check_pipeline_stage_missing_input_block():
    lines = [
        "Output:",
        "  Destination: PostgreSQL",
        "  Format: rows",
        "Error Handling:",
        "  transient: retry",
        "  missing_input: skip",
        "  default: alert",
    ]
    issues = check_pipeline_stage(lines)
    assert any("Input" in i for i in issues)


def test_check_pipeline_stage_missing_output_block():
    lines = [
        "Input:",
        "  Source: S3",
        "  Format: CSV",
        "  Schema: s",
        "↓",
        "Error Handling:",
        "  transient: retry",
        "  missing_input: skip",
        "  default: alert",
    ]
    issues = check_pipeline_stage(lines)
    assert any("Output" in i for i in issues)


def test_check_pipeline_stage_missing_error_handling():
    lines = [
        "Input:",
        "  Source: S3",
        "  Format: CSV",
        "  Schema: s",
        "↓",
        "Output:",
        "  Destination: DB",
        "  Format: rows",
    ]
    issues = check_pipeline_stage(lines)
    assert any("Error Handling" in i for i in issues)


# ---------------------------------------------------------------------------
# check_feature
# ---------------------------------------------------------------------------

_VALID_FEATURE = [
    "Module type: Feature",
    "Function: create_order",
    "File: orders.py",
]


def test_check_feature_valid_no_issues():
    assert check_feature(_VALID_FEATURE) == []


def test_check_feature_no_function_values_reports_issue():
    issues = check_feature(["Module type: Feature"])
    assert any("Function" in i for i in issues)


def test_check_feature_not_supported_is_acceptable():
    issues = check_feature(["Module type: Feature", "Not Supported"])
    assert issues == []


# ---------------------------------------------------------------------------
# check_background_job
# ---------------------------------------------------------------------------

_VALID_BG_JOB = [
    "Module type: Background Job",
    "Trigger: cron 0 * * * *",
    "→ acknowledge message",
    "Error Handling:",
    "  transient: retry 3x",
    "  permanent: dead-letter queue",
    "  default: alert oncall",
]


def test_check_background_job_valid_no_issues():
    assert check_background_job(_VALID_BG_JOB) == []


def test_check_background_job_missing_trigger():
    lines = [l for l in _VALID_BG_JOB if not l.startswith("Trigger")]
    issues = check_background_job(lines)
    assert any("Trigger" in i for i in issues)


def test_check_background_job_missing_error_handling():
    lines = [
        "Trigger: cron 0 * * * *",
        "→ acknowledge message",
    ]
    issues = check_background_job(lines)
    assert any("Error Handling" in i for i in issues)


# ---------------------------------------------------------------------------
# check_shared_utility
# ---------------------------------------------------------------------------

_VALID_SHARED_UTIL = [
    "Module type: Shared Utility",
    "@startuml",
    "class Logger {",
    "  +log(msg: str)",
    "  +error(msg: str)",
    "}",
    "@enduml",
    "**Used by**",
    "| Module | Usage |",
    "| --- | --- |",
    "| auth | session logging |",
]


def test_check_shared_utility_valid_no_issues():
    assert check_shared_utility(_VALID_SHARED_UTIL) == []


def test_check_shared_utility_missing_plantuml_block():
    lines = [l for l in _VALID_SHARED_UTIL if "@" not in l and "class" not in l and "{" not in l and "}" not in l and "+" not in l]
    issues = check_shared_utility(lines)
    assert any("plantuml" in i for i in issues)


def test_check_shared_utility_missing_used_by_section():
    issues = check_shared_utility(_VALID_SHARED_UTIL[:7])  # plantuml block only
    assert any("Used by" in i for i in issues)


# ---------------------------------------------------------------------------
# check_quality — dispatch and status
# ---------------------------------------------------------------------------

def test_check_quality_pipeline_stage_pass():
    status, issues = check_quality(_VALID_PIPELINE, "Pipeline Stage")
    assert status == "pass"
    assert issues == []


def test_check_quality_feature_pass():
    status, issues = check_quality(_VALID_FEATURE, "Feature")
    assert status == "pass"
    assert issues == []


def test_check_quality_background_job_pass():
    status, issues = check_quality(_VALID_BG_JOB, "Background Job")
    assert status == "pass"
    assert issues == []


def test_check_quality_shared_utility_pass():
    status, issues = check_quality(_VALID_SHARED_UTIL, "Shared Utility")
    assert status == "pass"
    assert issues == []


def test_check_quality_unknown_type_returns_unknown():
    status, issues = check_quality([], "Nonexistent")
    assert status == "unknown"
    assert issues


def test_check_quality_fail_when_issues_present():
    status, issues = check_quality(["Module type: Pipeline Stage"], "Pipeline Stage")
    assert status == "fail"
    assert len(issues) > 0
