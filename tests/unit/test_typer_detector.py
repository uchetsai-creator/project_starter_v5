import sys
import tempfile
from pathlib import Path

_ADAPTERS_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "templates" / "script" / "validators" / "_spec_code_adapters"
)
sys.path.insert(0, str(_ADAPTERS_DIR))

from typer import TyperDetector  # noqa: E402

sys.path.remove(str(_ADAPTERS_DIR))  # don't leak onto sys.path — see test_ansible_detector.py


def _extract(source: str):
    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False, encoding="utf-8") as f:
        f.write(source)
        path = f.name
    try:
        return TyperDetector().extract([path])
    finally:
        Path(path).unlink()


def test_flags_are_derived_from_parameters_without_option_decorators():
    src = """
import typer

app = typer.Typer()

@app.command()
def build(output: str = "dist", verbose: bool = False):
    pass
"""
    commands = _extract(src)
    assert len(commands) == 1
    flags = {f.name: f.type for f in commands[0].flags}
    assert flags == {"output": "str", "verbose": "bool"}


def test_named_command_overrides_function_name():
    src = """
import typer

app = typer.Typer()

@app.command("deploy")
def deploy_cmd(target: str):
    pass
"""
    commands = _extract(src)
    assert commands[0].name == "deploy"


def test_typer_option_string_overrides_derived_flag_name():
    src = """
import typer

app = typer.Typer()

@app.command()
def sync(dry_run: bool = typer.Option(False, "--fast")):
    pass
"""
    commands = _extract(src)
    assert {f.name for f in commands[0].flags} == {"fast"}


def test_function_without_command_decorator_is_ignored():
    src = """
def helper(x: int):
    pass
"""
    assert _extract(src) == []


def test_positional_argument_without_default_is_still_a_flag():
    src = """
import typer

app = typer.Typer()

@app.command()
def greet(name: str):
    pass
"""
    commands = _extract(src)
    assert {f.name for f in commands[0].flags} == {"name"}
