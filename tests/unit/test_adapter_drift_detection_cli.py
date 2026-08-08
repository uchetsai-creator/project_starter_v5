"""Golden drift-detection coverage for the typer adapter (click is covered in
tests/unit/test_adapter_drift_detection.py). See that file for the full rationale.
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


_TYPER_SPEC = """\
### `mytool build`
#### Flags
| Flag | Short | Type | Default | Description |
|---|---|---|---|---|
| `--output` | | string | dist | Output path |
| `--verbose` | | bool | false | Verbose output |
"""

_TYPER_CODE_CLEAN = """\
import typer

app = typer.Typer()


@app.command()
def build(output: str = "dist", verbose: bool = False):
    pass
"""


def test_typer_clean_spec_and_code_report_no_mismatches(tmp_path):
    spec = tmp_path / "cli-contract.md"
    spec.write_text(_TYPER_SPEC, encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    (src / "cli.py").write_text(_TYPER_CODE_CLEAN, encoding="utf-8")

    result = _run("--adapter", "typer", "--spec", str(spec), "--src", str(src), "--strict")
    assert "No mismatches" in result.stdout, result.stdout
    assert result.returncode == 0


def test_typer_missing_flag_is_caught(tmp_path):
    spec = tmp_path / "cli-contract.md"
    spec.write_text(_TYPER_SPEC, encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    code = _TYPER_CODE_CLEAN.replace(', verbose: bool = False', '')
    (src / "cli.py").write_text(code, encoding="utf-8")

    result = _run("--adapter", "typer", "--spec", str(spec), "--src", str(src), "--strict")
    assert "[FAIL]" in result.stdout, result.stdout
    assert "verbose" in result.stdout, result.stdout
    assert result.returncode == 1


def test_typer_flag_type_change_is_caught(tmp_path):
    spec = tmp_path / "cli-contract.md"
    spec.write_text(_TYPER_SPEC, encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    # Drift: output changed from str to int, contradicting the spec's "string".
    code = _TYPER_CODE_CLEAN.replace('output: str = "dist"', 'output: int = 0')
    (src / "cli.py").write_text(code, encoding="utf-8")

    result = _run("--adapter", "typer", "--spec", str(spec), "--src", str(src), "--strict")
    assert "[FAIL]" in result.stdout, result.stdout
    assert "output" in result.stdout, result.stdout
    assert result.returncode == 1


def test_typer_option_name_override_matches_spec_flag(tmp_path):
    """typer.Option(..., "--fast") overrides the derived flag name — the spec must
    declare --fast (not --dry-run) for this to report clean, proving the override
    is actually honored rather than silently falling back to the param name."""
    spec = tmp_path / "cli-contract.md"
    spec.write_text(
        "### `mytool deploy`\n"
        "#### Flags\n"
        "| Flag | Short | Type | Default | Description |\n"
        "|---|---|---|---|---|\n"
        "| `--target` | | string | | Deploy target |\n"
        "| `--fast` | | bool | false | Skip slow checks |\n",
        encoding="utf-8",
    )
    src = tmp_path / "src"
    src.mkdir()
    (src / "cli.py").write_text(
        "import typer\n\n"
        "app = typer.Typer()\n\n\n"
        "@app.command(\"deploy\")\n"
        "def deploy_cmd(target: str, dry_run: bool = typer.Option(False, \"--fast\")):\n"
        "    pass\n",
        encoding="utf-8",
    )

    result = _run("--adapter", "typer", "--spec", str(spec), "--src", str(src), "--strict")
    assert "No mismatches" in result.stdout, result.stdout
    assert result.returncode == 0
