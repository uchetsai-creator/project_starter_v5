"""
typer.py — TyperDetector for project_starter_v5.

Extracts NormalizedCommand objects from Typer CLI code:
  - Code: functions decorated with @<app>.command(...) — same decorator shape
    as Click, but Typer's whole premise is that flags are *not* declared with
    explicit @click.option()/@click.argument() decorators. Instead, every
    function parameter becomes a CLI flag automatically, with its type coming
    from the annotation — unless a `typer.Option(...)`/`typer.Argument(...)`
    default value explicitly overrides the flag's name (e.g. `dry_run: bool =
    typer.Option(False, "--fast")` exposes `--fast`, not `--dry-run`). Reusing
    Click's detector here would find zero flags on every Typer command, since
    Click's flags live in decorators Typer code never has.
  - Spec: cli-contract.md — shared cli format, parsed by CLIAdapter, not here.
"""
from __future__ import annotations

import ast

from _base import Detector, NormalizedCommand, NormalizedField
from _utils import _annotation_str, _clean_flag_name

_SKIP_PARAMS = frozenset({'self', 'ctx'})


class TyperDetector(Detector):
    """
    Framework detector for Typer (cli).
    Receives pre-discovered .py files from CLIAdapter. Must not perform file discovery.
    """

    def extract(self, files: list[str]) -> list[NormalizedCommand]:
        commands: list[NormalizedCommand] = []
        for fpath in files:
            if fpath.endswith('.py'):
                commands.extend(self._parse_file(fpath))
        return commands

    def _parse_file(self, fpath: str) -> list[NormalizedCommand]:
        try:
            with open(fpath, encoding='utf-8') as f:
                source = f.read()
            tree = ast.parse(source, filename=fpath)
        except (OSError, SyntaxError):
            return []

        commands: list[NormalizedCommand] = []
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue

            cmd_name = self._command_name(node)
            if cmd_name is None:
                continue

            defaults = self._defaults_by_arg(node)
            flags: list[NormalizedField] = []
            for arg in node.args.args:
                if arg.arg in _SKIP_PARAMS:
                    continue
                flags.append(self._flag_from_param(arg, defaults.get(arg.arg)))

            commands.append(NormalizedCommand(name=cmd_name, flags=flags))

        return commands

    @staticmethod
    def _command_name(node) -> str | None:
        """A function is a Typer command if decorated with <name>.command(...)."""
        for dec in node.decorator_list:
            if not isinstance(dec, ast.Call):
                continue
            func = dec.func
            if not (isinstance(func, ast.Attribute) and func.attr == 'command'):
                continue
            name = node.name
            if dec.args and isinstance(dec.args[0], ast.Constant) and isinstance(dec.args[0].value, str):
                name = dec.args[0].value
            return name
        return None

    @staticmethod
    def _defaults_by_arg(node) -> dict:
        """Map each parameter name to its default-value AST node, if any
        (ast.arguments stores defaults right-aligned against the arg list)."""
        args = node.args.args
        defaults = node.args.defaults
        mapping = {}
        for arg, default in zip(args[len(args) - len(defaults):], defaults):
            mapping[arg.arg] = default
        return mapping

    @staticmethod
    def _flag_from_param(arg, default) -> NormalizedField:
        flag_name = arg.arg
        flag_type = _annotation_str(arg.annotation) or 'str'

        # typer.Option(...)/typer.Argument(...)'s first string argument, when it
        # starts with '-', explicitly overrides the flag name Typer would
        # otherwise derive from the parameter name.
        if isinstance(default, ast.Call):
            func = default.func
            call_name = func.attr if isinstance(func, ast.Attribute) else getattr(func, 'id', None)
            if call_name in ('Option', 'Argument'):
                for a in default.args:
                    if isinstance(a, ast.Constant) and isinstance(a.value, str) and a.value.startswith('-'):
                        flag_name = _clean_flag_name(a.value)
                        break

        return NormalizedField(name=flag_name, type=flag_type)


if __name__ == '__main__':
    import tempfile
    from pathlib import Path

    src = '''
import typer

app = typer.Typer()

@app.command()
def build(output: str = "dist", verbose: bool = False):
    pass

@app.command("deploy")
def deploy_cmd(target: str, dry_run: bool = typer.Option(False, "--fast")):
    pass

def helper(x: int):
    """Not a Typer command — no @app.command() decorator."""
    pass
'''

    with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False, encoding="utf-8") as f:
        f.write(src)
        path = f.name

    try:
        detector = TyperDetector()
        assert detector.extract([]) == [], "extract([]) must return an empty list"

        commands = detector.extract([path])
        by_name = {c.name: c for c in commands}

        assert "build" in by_name, commands
        assert "deploy" in by_name, commands
        assert {f.name for f in by_name["build"].flags} == {"output", "verbose"}
        build_types = {f.name: f.type for f in by_name["build"].flags}
        assert build_types["verbose"] == "bool"

        deploy_flags = {f.name for f in by_name["deploy"].flags}
        assert deploy_flags == {"target", "fast"}, deploy_flags  # typer.Option override
        assert len(commands) == 2, "helper() with no @app.command() must not be detected"
    finally:
        Path(path).unlink()

    print("[OK] typer.py self-test passed")
