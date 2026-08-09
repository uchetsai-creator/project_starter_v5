"""Unit tests for detect_type.py."""
import os
import sys
import json
import subprocess
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
DETECT_SCRIPT = REPO_ROOT / "detect_type.py"

sys.path.insert(0, str(REPO_ROOT))
from detect_type import (
    _score_directory,
    _score_requirements,
    _merge,
    _recommend,
    _suggest_adapter,
    _suggest_spec_code,
    VALID_TYPES,
)


def _run(*args: str) -> subprocess.CompletedProcess:
    # PYTHONUTF8 forces detect_type.py's own stdout/stderr encoding to UTF-8, matching the
    # encoding="utf-8" this decodes with — without it, a non-ASCII character (e.g. the em
    # dash in the .project-starter.yml template) encodes using the OS locale codepage
    # (e.g. cp950 on Traditional Chinese Windows), which this decode would then reject.
    return subprocess.run(
        [sys.executable, str(DETECT_SCRIPT), *args],
        capture_output=True, text=True, encoding="utf-8",
        env={**os.environ, "PYTHONUTF8": "1"},
    )


# ---------------------------------------------------------------------------
# _score_requirements
# ---------------------------------------------------------------------------

def test_web_app_keywords():
    s = _score_requirements("I need a REST API web application with user auth")
    assert s["web-app"] > s["data-pipeline"]
    assert s["web-app"] > s["cli-tool"]


def test_llm_app_keywords():
    s = _score_requirements("LLM chatbot with RAG and vector database using langchain")
    assert s["llm-app"] > s["web-app"]
    assert s["llm-app"] > s["ml-pipeline"]


def test_data_pipeline_keywords():
    s = _score_requirements("ETL data pipeline with Airflow for batch processing")
    assert s["data-pipeline"] >= 50


def test_ml_pipeline_keywords():
    s = _score_requirements("machine learning model training with PyTorch and MLflow")
    assert s["ml-pipeline"] > s["data-pipeline"]
    assert s["ml-pipeline"] > s["llm-app"]


def test_iac_keywords():
    s = _score_requirements("infrastructure as code with Terraform on AWS")
    assert s["iac"] >= 40


def test_mobile_app_keywords():
    s = _score_requirements("mobile app for iOS and Android with React Native")
    assert s["mobile-app"] >= 40
    assert s["mobile-app"] > s["web-app"]


def test_cli_tool_keywords():
    s = _score_requirements("command line tool for data processing")
    assert s["cli-tool"] >= 20


def test_library_keywords():
    s = _score_requirements("Python library and SDK published to PyPI")
    assert s["library"] >= 20


def test_microservices_keywords():
    s = _score_requirements("microservices architecture with Kubernetes and Kafka")
    assert s["microservices"] >= 40


# ---------------------------------------------------------------------------
# _score_directory
# ---------------------------------------------------------------------------

def test_tf_files_detected(tmp_path):
    (tmp_path / "main.tf").touch()
    (tmp_path / "variables.tf").touch()
    s = _score_directory(tmp_path)
    assert s["iac"] >= 20


def test_dags_dir_detected(tmp_path):
    dags = tmp_path / "dags"
    dags.mkdir()
    (dags / "etl_dag.py").touch()
    s = _score_directory(tmp_path)
    assert s["data-pipeline"] >= 20


def test_dagster_adapter_file_does_not_pollute(tmp_path):
    # dagster.py in adapters should NOT trigger data-pipeline via glob
    adapters = tmp_path / "_adapters"
    adapters.mkdir()
    (adapters / "dagster.py").touch()
    s = _score_directory(tmp_path)
    assert s["data-pipeline"] == 0


def test_pubspec_yaml_detected(tmp_path):
    (tmp_path / "pubspec.yaml").touch()
    s = _score_directory(tmp_path)
    assert s["mobile-app"] >= 25


def test_notebooks_dir_detected(tmp_path):
    (tmp_path / "notebooks").mkdir()
    s = _score_directory(tmp_path)
    assert s["ml-pipeline"] >= 15


def test_k8s_dir_detected(tmp_path):
    (tmp_path / "k8s").mkdir()
    (tmp_path / "auth-service").mkdir()
    (tmp_path / "api-service").mkdir()
    s = _score_directory(tmp_path)
    assert s["microservices"] >= 35


def test_multiple_service_dirs_detected(tmp_path):
    (tmp_path / "auth-service").mkdir()
    (tmp_path / "payment-service").mkdir()
    (tmp_path / "notification-service").mkdir()
    s = _score_directory(tmp_path)
    assert s["microservices"] >= 40


def test_requirements_txt_deps(tmp_path):
    (tmp_path / "requirements.txt").write_text("fastapi\nuvicorn\nhttpx\n")
    s = _score_directory(tmp_path)
    assert s["web-app"] >= 20


def test_package_json_react_native(tmp_path):
    pkg = {
        "dependencies": {
            "react-native": "0.73.0",
            "expo": "^50.0.0",
        }
    }
    (tmp_path / "package.json").write_text(json.dumps(pkg))
    s = _score_directory(tmp_path)
    assert s["mobile-app"] >= 40


def test_package_json_express(tmp_path):
    pkg = {"dependencies": {"express": "^4.18.0"}}
    (tmp_path / "package.json").write_text(json.dumps(pkg))
    s = _score_directory(tmp_path)
    assert s["web-app"] >= 20


# ---------------------------------------------------------------------------
# _recommend
# ---------------------------------------------------------------------------

def test_recommend_single_winner():
    scores = {t: 0 for t in VALID_TYPES}
    scores["web-app"] = 50
    scores["cli-tool"] = 5
    rec, ranked = _recommend(scores)
    assert rec == "web-app"


def test_recommend_hybrid_when_two_strong_signals():
    scores = {t: 0 for t in VALID_TYPES}
    scores["web-app"] = 50
    scores["llm-app"] = 40
    rec, ranked = _recommend(scores)
    assert "web-app" in rec
    assert "llm-app" in rec
    assert "+" in rec


def test_recommend_no_hybrid_when_second_too_weak():
    scores = {t: 0 for t in VALID_TYPES}
    scores["web-app"] = 50
    scores["cli-tool"] = 5  # 5 < 50 * 0.40 = 20 → no hybrid
    rec, _ = _recommend(scores)
    assert "+" not in rec
    assert rec == "web-app"


def test_recommend_fallback_when_all_zero():
    scores = {t: 0 for t in VALID_TYPES}
    rec, ranked = _recommend(scores)
    assert rec == "web-app"
    assert ranked == []


def test_recommend_below_primary_threshold_still_returns_top():
    scores = {t: 0 for t in VALID_TYPES}
    scores["cli-tool"] = 5  # below PRIMARY_THRESHOLD=20
    rec, ranked = _recommend(scores)
    assert rec == "cli-tool"
    assert "+" not in rec


# ---------------------------------------------------------------------------
# CLI integration
# ---------------------------------------------------------------------------

def test_cli_requirements_only_no_scan(tmp_path):
    result = _run("--requirements", "terraform IaC provisioning", "--no-scan")
    assert result.returncode == 0
    assert "iac" in result.stdout


def test_cli_json_output():
    result = _run("--requirements", "LLM chatbot with RAG", "--no-scan", "--json")
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert "recommendation" in data
    assert "scores" in data
    assert data["scores"]["llm-app"] > 0


def test_cli_directory_scan(tmp_path):
    (tmp_path / "main.tf").touch()
    result = _run(str(tmp_path))
    assert result.returncode == 0
    assert "iac" in result.stdout


def test_cli_apply_writes_yml(tmp_path):
    (tmp_path / "main.tf").touch()
    result = _run(str(tmp_path), "--apply")
    assert result.returncode == 0
    yml = tmp_path / ".project-starter.yml"
    assert yml.exists()
    assert "iac" in yml.read_text(encoding="utf-8")


def test_cli_apply_updates_existing_yml(tmp_path):
    yml = tmp_path / ".project-starter.yml"
    yml.write_text("project_type: [your-project-type]\ndocs_path: docs/\n")
    (tmp_path / "main.tf").touch()
    result = _run(str(tmp_path), "--apply")
    assert result.returncode == 0
    assert "iac" in yml.read_text(encoding="utf-8")
    assert "[your-project-type]" not in yml.read_text(encoding="utf-8")


def test_cli_invalid_path_exits_nonzero():
    result = _run("/nonexistent/path/that/does/not/exist")
    assert result.returncode != 0


def test_cli_no_args_does_not_crash():
    # Running with no args defaults to current dir — should not crash
    result = _run("--no-scan")
    assert result.returncode == 0


# ---------------------------------------------------------------------------
# spec_code_* suggestion
# ---------------------------------------------------------------------------

def test_suggest_adapter_matches_python_dep(tmp_path):
    (tmp_path / "requirements.txt").write_text("fastapi\nuvicorn\n", encoding="utf-8")
    assert _suggest_adapter(tmp_path, "web-app") == "fastapi"


def test_suggest_adapter_matches_file_glob(tmp_path):
    (tmp_path / "main.tf").touch()
    assert _suggest_adapter(tmp_path, "iac") == "terraform"


def test_suggest_adapter_ignores_wrong_project_type(tmp_path):
    (tmp_path / "requirements.txt").write_text("fastapi\n", encoding="utf-8")
    # fastapi is a web-app signal — must not fire for an unrelated type
    assert _suggest_adapter(tmp_path, "cli-tool") is None


def test_suggest_adapter_no_signal_returns_none(tmp_path):
    assert _suggest_adapter(tmp_path, "web-app") is None


def test_suggest_spec_code_returns_full_triple(tmp_path):
    (tmp_path / "requirements.txt").write_text("click\n", encoding="utf-8")
    (tmp_path / "src").mkdir()
    suggestion = _suggest_spec_code(tmp_path, "cli-tool")
    assert suggestion == {
        "adapter": "click",
        "spec": "docs/specs/cli-contract.md",
        "src": "src/",
    }


def test_suggest_spec_code_skips_hybrid_recommendation(tmp_path):
    (tmp_path / "requirements.txt").write_text("fastapi\nlangchain\n", encoding="utf-8")
    assert _suggest_spec_code(tmp_path, "web-app+llm-app") is None


def test_cli_json_includes_spec_code_suggestion(tmp_path):
    (tmp_path / "main.tf").touch()
    result = _run(str(tmp_path), "--json")
    assert result.returncode == 0
    data = json.loads(result.stdout)
    assert data["spec_code_suggestion"] == {
        "adapter": "terraform",
        "spec": "docs/architecture/topology.md",
        "src": "src/",
    }


def test_cli_apply_prefills_spec_code_on_fresh_yml(tmp_path):
    (tmp_path / "main.tf").touch()
    result = _run(str(tmp_path), "--apply")
    assert result.returncode == 0
    text = (tmp_path / ".project-starter.yml").read_text(encoding="utf-8")
    assert "spec_code_adapter: terraform" in text
    assert "spec_code_spec: docs/architecture/topology.md" in text
    assert "spec_code_src: src/" in text


def test_cli_apply_refuses_on_low_confidence(tmp_path):
    result = _run(str(tmp_path), "--requirements", "I don't know, help me build something",
                   "--no-scan", "--apply")
    assert result.returncode == 1
    assert "confidence is low" in (result.stdout + result.stderr)
    assert not (tmp_path / ".project-starter.yml").exists()


def test_cli_apply_force_overrides_low_confidence_refusal(tmp_path):
    result = _run(str(tmp_path), "--requirements", "I don't know, help me build something",
                   "--no-scan", "--apply", "--force")
    assert result.returncode == 0
    yml = tmp_path / ".project-starter.yml"
    assert yml.exists()
    assert "project_type: web-app" in yml.read_text(encoding="utf-8")


def test_json_output_includes_authoritative_flag(tmp_path):
    result = _run("--requirements", "I don't know, help me build something",
                   "--no-scan", "--json")
    data = json.loads(result.stdout)
    assert data["authoritative"] is False

    result_high = _run("--requirements", "terraform IaC provisioning", "--no-scan", "--json")
    data_high = json.loads(result_high.stdout)
    assert data_high["authoritative"] is True


def test_cli_apply_still_works_on_high_confidence_without_force(tmp_path):
    (tmp_path / "main.tf").touch()
    result = _run(str(tmp_path), "--apply")
    assert result.returncode == 0
    assert "iac" in (tmp_path / ".project-starter.yml").read_text(encoding="utf-8")


def test_cli_apply_does_not_overwrite_existing_spec_code_config(tmp_path):
    (tmp_path / "main.tf").touch()
    yml = tmp_path / ".project-starter.yml"
    yml.write_text(
        "project_type: [your-project-type]\n"
        "docs_path: docs/\n"
        "spec_code_adapter: pulumi\n"
        "spec_code_spec: docs/architecture/topology.md\n"
        "spec_code_src: infra/\n",
        encoding="utf-8",
    )
    result = _run(str(tmp_path), "--apply")
    assert result.returncode == 0
    text = yml.read_text(encoding="utf-8")
    # Existing user config must survive untouched — only project_type is rewritten.
    assert "spec_code_adapter: pulumi" in text
    assert "spec_code_src: infra/" in text
