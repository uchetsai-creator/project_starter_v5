from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent

VALID_TYPES: list[str] = [
    "web-app", "cli-tool", "library",
    "data-pipeline", "ml-pipeline", "microservices", "llm-app", "iac", "mobile-app",
]


def setup_fixture(tmp_path: Path, type_name: str, content: str) -> Path:
    """Stub: create a minimal fixture directory for use in 65.3/65.4."""
    p = tmp_path / type_name
    p.mkdir(parents=True, exist_ok=True)
    return p
