"""
_capability_cli.py — CLIAdapter for project_starter_v5 (Phase 52.5).

Capability adapter for CLI tool projects.
Orchestrates: ClickDetector.

Architecture:
  CLIAdapter (this file)
      │  extract_spec() — parses cli-contract.md
      │  extract_code() — discovers .py files, delegates to detector(s)
      └── ClickDetector

Invariants:
  - No framework-specific parsing logic here.
  - Detector selection is the only framework-awareness in this adapter.
  - File discovery lives here, not in detectors.
  - extract_spec() / extract_code() never raise; return [] on any error.
"""
from __future__ import annotations

import os
import re

from _base import FrameworkAdapter, NormalizedCommand, NormalizedField
from _utils import _clean_flag_name, _PLACEHOLDER_CMD_NAMES

_DETECTORS: dict[str, tuple[str, str]] = {
    'click': ('click', 'ClickDetector'),
}


class CLIAdapter(FrameworkAdapter):
    """
    Capability adapter for CLI tool projects (Phase 52.5).

    Recognized frameworks: click.

    Args:
        framework: Optional framework hint (e.g. 'click'). When supplied,
                   only the matching detector is run. When None, all detectors
                   run and results are unioned.
    """

    def __init__(self, framework: str | None = None) -> None:
        self._framework = framework

    # ------------------------------------------------------------------ spec

    def extract_spec(self, spec_path: str) -> list[NormalizedCommand]:
        """
        Parse a cli-contract.md spec file.

        Spec format:
          ### `tool-name subcommand`
          #### Flags
          | Flag | Short | Type | Default | Description |
          | `--output` | `-o` | string | stdout | ... |
        """
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
        """
        Discover .py files and delegate to CLI detector(s).

        With framework hint: only the matching detector runs.
        Without hint: all detectors run and results are unioned.
        """
        files = (
            [src_path] if os.path.isfile(src_path)
            else [
                os.path.join(root, fname)
                for root, _, fnames in os.walk(src_path)
                for fname in fnames
                if fname.endswith('.py')
            ]
        )

        active_detectors = (
            {self._framework: _DETECTORS[self._framework]}
            if self._framework and self._framework in _DETECTORS
            else _DETECTORS
        )

        results: list[NormalizedCommand] = []
        for _, (module_name, class_name) in active_detectors.items():
            try:
                import importlib
                mod = importlib.import_module(module_name)
                cls = getattr(mod, class_name)
                results.extend(cls().extract(files))
            except Exception:  # noqa: BLE001
                pass

        return results
