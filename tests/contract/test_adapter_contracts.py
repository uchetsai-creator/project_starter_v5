import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_ADAPTERS_DIR = _REPO_ROOT / "templates/script/validators/_spec_code_adapters"
sys.path.insert(0, str(_ADAPTERS_DIR))

from _base import (
    NormalizedCommand,
    NormalizedEndpoint,
    NormalizedFunction,
    NormalizedResource,
    NormalizedScreen,
    NormalizedStageContract,
    NormalizedTool,
)
from _capability_cli import CLIAdapter
from _capability_iac import IaCAdapter
from _capability_library import LibraryAdapter
from _capability_llm import LLMAdapter
from _capability_mobile import MobileAdapter
from _capability_pipeline import DataPipelineAdapter
from _capability_web_api import WebAPIAdapter

ALL_ADAPTER_CLASSES = [
    DataPipelineAdapter,
    WebAPIAdapter,
    CLIAdapter,
    LibraryAdapter,
    LLMAdapter,
    IaCAdapter,
    MobileAdapter,
]


# ---------------------------------------------------------------------------
# Contract 1 — extract_spec() and extract_code() never raise
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("adapter_class", ALL_ADAPTER_CLASSES, ids=[c.__name__ for c in ALL_ADAPTER_CLASSES])
def test_extract_spec_returns_empty_on_missing_file(adapter_class):
    adapter = adapter_class()
    assert adapter.extract_spec("/nonexistent/path.md") == []


@pytest.mark.parametrize("adapter_class", ALL_ADAPTER_CLASSES, ids=[c.__name__ for c in ALL_ADAPTER_CLASSES])
def test_extract_code_returns_empty_on_missing_dir(adapter_class):
    adapter = adapter_class()
    assert adapter.extract_code("/nonexistent/src/") == []


# ---------------------------------------------------------------------------
# Contract 3 — capability adapters return correct NormalizedForm types
# ---------------------------------------------------------------------------

@pytest.fixture
def fixture_pipeline_spec(tmp_path):
    spec = tmp_path / "pipeline-contract.md"
    spec.write_text(
        "### LoadData\n"
        "#### Input Contract\n"
        "| Schema | source: str, date: str |\n"
        "#### Output Contract\n"
        "| Schema | rows: int |\n",
        encoding="utf-8",
    )
    return str(spec)


@pytest.fixture
def fixture_api_spec(tmp_path):
    spec = tmp_path / "api-contract.md"
    spec.write_text(
        "### POST /orders\n"
        "#### Request Body\n"
        "| Field | Type | Required | Description |\n"
        "| --- | --- | --- | --- |\n"
        "| customer_id | int | Yes | Customer identifier |\n"
        "#### Response Body\n"
        "| Field | Type | Description |\n"
        "| --- | --- | --- |\n"
        "| order_id | int | Created order ID |\n",
        encoding="utf-8",
    )
    return str(spec)


@pytest.fixture
def fixture_cli_spec(tmp_path):
    spec = tmp_path / "cli-contract.md"
    spec.write_text(
        "### `mytool build`\n"
        "#### Flags\n"
        "| Flag | Short | Type | Default | Description |\n"
        "| --- | --- | --- | --- | --- |\n"
        "| `--output` | `-o` | string | stdout | Output path |\n",
        encoding="utf-8",
    )
    return str(spec)


@pytest.fixture
def fixture_library_spec(tmp_path):
    spec = tmp_path / "public-api.md"
    spec.write_text(
        "### create_client\n"
        "#### Parameters\n"
        "| Name | Type | Description |\n"
        "|---|---|---|\n"
        "| api_key | str | API key |\n"
        "#### Returns\n"
        "| Type | Description |\n"
        "|---|---|\n"
        "| Client | Authenticated client |\n",
        encoding="utf-8",
    )
    return str(spec)


@pytest.fixture
def fixture_llm_spec(tmp_path):
    spec = tmp_path / "llm-contract.md"
    spec.write_text(
        "### get_weather\n"
        "#### Parameters\n"
        "| Name | Type | Required | Description |\n"
        "|---|---|---|---|\n"
        "| location | string | Yes | City name |\n",
        encoding="utf-8",
    )
    return str(spec)


@pytest.fixture
def fixture_iac_spec(tmp_path):
    spec = tmp_path / "topology.md"
    spec.write_text(
        "### web_server (aws_instance)\n"
        "#### Configuration\n"
        "| Key | Value | Description |\n"
        "|---|---|---|\n"
        "| instance_type | t3.micro | EC2 instance type |\n",
        encoding="utf-8",
    )
    return str(spec)


@pytest.fixture
def fixture_mobile_spec(tmp_path):
    spec = tmp_path / "mobile-contract.md"
    spec.write_text(
        "### HomeScreen\n"
        "#### Props\n"
        "| Name | Type | Required | Description |\n"
        "|---|---|---|---|\n"
        "| userId | string | Yes | Current user ID |\n",
        encoding="utf-8",
    )
    return str(spec)


def test_pipeline_adapter_returns_stage_contracts(fixture_pipeline_spec):
    results = DataPipelineAdapter().extract_spec(fixture_pipeline_spec)
    assert len(results) > 0, "DataPipelineAdapter parsed no stages from fixture"
    assert all(isinstance(r, NormalizedStageContract) for r in results)


def test_web_api_adapter_returns_endpoints(fixture_api_spec):
    results = WebAPIAdapter().extract_spec(fixture_api_spec)
    assert len(results) > 0, "WebAPIAdapter parsed no endpoints from fixture"
    assert all(isinstance(r, NormalizedEndpoint) for r in results)


def test_cli_adapter_returns_commands(fixture_cli_spec):
    results = CLIAdapter().extract_spec(fixture_cli_spec)
    assert len(results) > 0, "CLIAdapter parsed no commands from fixture"
    assert all(isinstance(r, NormalizedCommand) for r in results)


def test_library_adapter_returns_functions(fixture_library_spec):
    results = LibraryAdapter().extract_spec(fixture_library_spec)
    assert len(results) > 0, "LibraryAdapter parsed no functions from fixture"
    assert all(isinstance(r, NormalizedFunction) for r in results)


def test_llm_adapter_returns_tools(fixture_llm_spec):
    results = LLMAdapter().extract_spec(fixture_llm_spec)
    assert len(results) > 0, "LLMAdapter parsed no tools from fixture"
    assert all(isinstance(r, NormalizedTool) for r in results)


def test_iac_adapter_returns_resources(fixture_iac_spec):
    results = IaCAdapter().extract_spec(fixture_iac_spec)
    assert len(results) > 0, "IaCAdapter parsed no resources from fixture"
    assert all(isinstance(r, NormalizedResource) for r in results)


def test_mobile_adapter_returns_screens(fixture_mobile_spec):
    results = MobileAdapter().extract_spec(fixture_mobile_spec)
    assert len(results) > 0, "MobileAdapter parsed no screens from fixture"
    assert all(isinstance(r, NormalizedScreen) for r in results)
