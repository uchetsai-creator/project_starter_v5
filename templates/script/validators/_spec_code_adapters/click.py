"""
click.py — ClickDetector (+ legacy ClickAdapter) for project_starter_v5.

Phase 52.5: ClickDetector is the primary class — it receives pre-discovered
files from CLIAdapter and returns NormalizedCommand objects.
ClickAdapter is kept as a backward-compatible shim.

Extracts NormalizedCommand objects from:
  - Spec: cli-contract.md (### `tool subcommand` sections with #### Flags tables)
  - Code: Python files — @click.command() / @cli.command() decorated functions
           with @click.option() / @click.argument() decorators

No comparison logic here. All comparison lives in verify_spec_code.py.
"""
from __future__ import annotations

import ast
import os
import re

from _base import Detector, FrameworkAdapter, NormalizedCommand, NormalizedField

_PLACEHOLDER_CMD_NAMES = frozenset({'subcommand', '[subcommand]', 'tool-name', ''})


def _clean_flag_name(raw: str) -> str:
    """Strip backticks, leading dashes, and angle brackets."""
    return re.sub(r'[`<>]', '', raw).strip().lstrip('-').replace('-', '_')


class ClickDetector(Detector):
    """
    Framework detector for Click (Phase 52.5).

    Receives pre-discovered .py files from CLIAdapter.
    Returns NormalizedCommand for each @cli.command() decorated function.
    Must not perform file discovery.
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
            if not isinstance(node, ast.FunctionDef):
                continue

            cmd_name = None
            for dec in node.decorator_list:
                if not isinstance(dec, ast.Call):
                    continue
                func = dec.func
                if not (hasattr(func, 'attr') and func.attr == 'command'):
                    continue
                cmd_name = node.name
                if dec.args and isinstance(dec.args[0], ast.Constant):
                    cmd_name = str(dec.args[0].value)
                break

            if cmd_name is None:
                continue

            flags: list[NormalizedField] = []
            for dec in node.decorator_list:
                if not isinstance(dec, ast.Call):
                    continue
                func = dec.func
                if not (hasattr(func, 'attr') and func.attr in ('option', 'argument')):
                    continue

                flag_name = ''
                flag_type = 'str'
                for arg in dec.args:
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        if arg.value.startswith('--'):
                            flag_name = _clean_flag_name(arg.value)
                        elif arg.value.startswith('-') and len(arg.value) == 2:
                            pass
                        elif not arg.value.startswith('-'):
                            flag_name = _clean_flag_name(arg.value)
                for kw in dec.keywords:
                    if kw.arg == 'type':
                        if isinstance(kw.value, ast.Name):
                            flag_type = kw.value.id
                        elif isinstance(kw.value, ast.Attribute):
                            flag_type = kw.value.attr
                    elif kw.arg == 'is_flag':
                        if isinstance(kw.value, ast.Constant) and kw.value.value:
                            flag_type = 'bool'

                if flag_name:
                    flags.append(NormalizedField(name=flag_name, type=flag_type))

            commands.append(NormalizedCommand(name=cmd_name, flags=flags))

        return commands


class ClickAdapter(FrameworkAdapter):
    """
    Adapter for Click (Python) CLI Tool projects.

    Spec format (cli-contract.md):
      ### `tool-name subcommand`
      #### Flags
      | Flag | Short | Type | Default | Description |
      | `--output` | `-o` | string | stdout | ... |

    Code format (Python):
      @cli.command('subcommand')
      @click.option('--output', '-o', type=str)
      def subcommand(output):
          ...
    """

    # ------------------------------------------------------------------ spec

    def extract_spec(self, spec_path: str) -> list[NormalizedCommand]:
        try:
            with open(spec_path, encoding='utf-8') as f:
                text = f.read()
        except OSError:
            return []

        commands: list[NormalizedCommand] = []
        section_matches = list(re.finditer(
            r'^### `([^`]+)`|^### ([^\n`]+)', text, re.MULTILINE
        ))

        for idx, match in enumerate(section_matches):
            raw = (match.group(1) or match.group(2) or '').strip()
            # Last word is the subcommand name
            parts = raw.split()
            cmd_name = parts[-1].strip('[]') if parts else ''
            if cmd_name.lower() in _PLACEHOLDER_CMD_NAMES:
                continue

            section_start = match.end()
            section_end = (section_matches[idx + 1].start()
                           if idx + 1 < len(section_matches) else len(text))
            section = text[section_start:section_end]

            flags = self._parse_flags(section)
            commands.append(NormalizedCommand(name=cmd_name, flags=flags))

        return commands

    def _parse_flags(self, section: str) -> list[NormalizedField]:
        flags_m = re.search(r'^#### Flags', section, re.MULTILINE)
        if not flags_m:
            return []
        table_text = section[flags_m.end():]
        next_sec = re.search(r'^#{3,4} ', table_text, re.MULTILINE)
        if next_sec:
            table_text = table_text[:next_sec.start()]

        flags: list[NormalizedField] = []
        for row in re.finditer(
            r'(?m)^\|\s*(`[^`]+`|[^\|]+?)\s*\|\s*[^\|]*\|\s*([^\|]+?)\s*\|',
            table_text,
        ):
            flag_col = row.group(1).strip()
            type_col = row.group(2).strip()
            if re.match(r'^[-:]+$', flag_col.replace('`', '')):
                continue
            if flag_col.lower().replace('`', '') in ('flag', 'name', 'option'):
                continue
            flag_name = _clean_flag_name(flag_col)
            type_str = re.sub(r'[`|\\]', '', type_col).split()[0]
            if flag_name and not re.match(r'^[-:]+$', flag_name):
                flags.append(NormalizedField(name=flag_name, type=type_str))

        return flags

    # ------------------------------------------------------------------ code

    def extract_code(self, src_path: str) -> list[NormalizedCommand]:
        files = (
            [src_path] if os.path.isfile(src_path)
            else [
                os.path.join(root, fname)
                for root, _, fnames in os.walk(src_path)
                for fname in fnames
                if fname.endswith('.py')
            ]
        )
        commands: list[NormalizedCommand] = []
        for fpath in files:
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
            if not isinstance(node, ast.FunctionDef):
                continue

            cmd_name = None
            for dec in node.decorator_list:
                if not isinstance(dec, ast.Call):
                    continue
                func = dec.func
                if not (hasattr(func, 'attr') and func.attr == 'command'):
                    continue
                # Explicit name as first positional arg
                cmd_name = node.name
                if dec.args and isinstance(dec.args[0], ast.Constant):
                    cmd_name = str(dec.args[0].value)
                break

            if cmd_name is None:
                continue

            flags: list[NormalizedField] = []
            for dec in node.decorator_list:
                if not isinstance(dec, ast.Call):
                    continue
                func = dec.func
                if not (hasattr(func, 'attr') and func.attr in ('option', 'argument')):
                    continue

                flag_name = ''
                flag_type = 'str'
                for arg in dec.args:
                    if isinstance(arg, ast.Constant) and isinstance(arg.value, str):
                        if arg.value.startswith('--'):
                            flag_name = _clean_flag_name(arg.value)
                        elif arg.value.startswith('-') and len(arg.value) == 2:
                            pass  # short flag only; use long flag when available
                        elif not arg.value.startswith('-'):
                            flag_name = _clean_flag_name(arg.value)
                for kw in dec.keywords:
                    if kw.arg == 'type':
                        if isinstance(kw.value, ast.Name):
                            flag_type = kw.value.id
                        elif isinstance(kw.value, ast.Attribute):
                            flag_type = kw.value.attr
                    elif kw.arg == 'is_flag':
                        if isinstance(kw.value, ast.Constant) and kw.value.value:
                            flag_type = 'bool'

                if flag_name:
                    flags.append(NormalizedField(name=flag_name, type=flag_type))

            commands.append(NormalizedCommand(name=cmd_name, flags=flags))

        return commands
