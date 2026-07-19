"""
pulumi.py — PulumiDetector (+ legacy PulumiAdapter) for project_starter_v5.

Phase 52.5: PulumiDetector is the primary class — it receives pre-discovered
files from IaCAdapter and returns NormalizedResource objects.
PulumiAdapter is kept as a backward-compatible shim.

Extracts NormalizedResource objects from:
  - Spec: topology.md (### label (resource_type) sections with #### Configuration tables)
  - Code: Python files — ResourceType("name", key=value, ...) resource constructor calls

No comparison logic here. All comparison lives in verify_spec_code.py.
"""
from __future__ import annotations

import ast
import os
import re

from _base import Detector, FrameworkAdapter, NormalizedResource
from _utils import _parse_config_table


def _class_name_to_snake(name: str) -> str:
    """Convert CamelCase resource type to rough snake_case provider.resource label."""
    s = re.sub(r'([A-Z])', r'_\1', name).lower().lstrip('_')
    return s


class PulumiDetector(Detector):
    """
    Framework detector for Pulumi (Python) IaC (Phase 52.5).

    Receives pre-discovered .py files from IaCAdapter.
    Returns NormalizedResource for each ResourceType("name", ...) constructor call.
    Must not perform file discovery.
    """

    def extract(self, files: list[str]) -> list[NormalizedResource]:
        resources: list[NormalizedResource] = []
        for fpath in files:
            if fpath.endswith('.py'):
                resources.extend(self._parse_file(fpath))
        return resources

    def _parse_file(self, fpath: str) -> list[NormalizedResource]:
        try:
            with open(fpath, encoding='utf-8') as f:
                source = f.read()
            tree = ast.parse(source, filename=fpath)
        except (OSError, SyntaxError):
            return []

        resources: list[NormalizedResource] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Assign):
                continue
            val = node.value
            if not isinstance(val, ast.Call):
                continue
            func = val.func
            class_name = ''
            if isinstance(func, ast.Attribute):
                class_name = func.attr
            elif isinstance(func, ast.Name):
                class_name = func.id
            if not class_name or not class_name[0].isupper():
                continue

            if not val.args or not isinstance(val.args[0], ast.Constant):
                continue
            resource_name = str(val.args[0].value)

            config_keys = [kw.arg for kw in val.keywords if kw.arg and kw.arg != 'opts']

            if config_keys:
                resources.append(NormalizedResource(
                    name=resource_name,
                    resource_type=class_name,
                    config_keys=config_keys,
                ))

        return resources


class PulumiAdapter(FrameworkAdapter):
    """Deprecated: use the corresponding capability adapter in _capability_*.py. This shim exists for backward compatibility with --adapter <name> CLI usage. Do not extend.

    Adapter for Pulumi (Python) IaC / DevOps projects.

    Spec format (topology.md): same as TerraformAdapter.
      ### web_server (aws:ec2/instance:Instance)
      #### Configuration
      | Key | Value | Description |
      | instance_type | t3.micro | EC2 instance type |

    Code format (Python):
      server = aws.ec2.Instance("web_server",
          instance_type="t3.micro",
          ami="ami-0abc",
      )
    """

    def extract_spec(self, spec_path: str) -> list[NormalizedResource]:
        try:
            with open(spec_path, encoding='utf-8') as f:
                text = f.read()
        except OSError:
            return []

        resources: list[NormalizedResource] = []
        section_matches = list(re.finditer(
            r'^### (`?)(\w+)\1(?:\s+\(([^)]+)\))?',
            text, re.MULTILINE,
        ))

        for idx, match in enumerate(section_matches):
            label = match.group(2)
            rtype = (match.group(3) or '').strip()
            section_start = match.end()
            section_end = (section_matches[idx + 1].start()
                           if idx + 1 < len(section_matches) else len(text))
            section = text[section_start:section_end]

            resources.append(NormalizedResource(
                name=label,
                resource_type=rtype,
                config_keys=_parse_config_table(section),
            ))

        return resources

    def extract_code(self, src_path: str) -> list[NormalizedResource]:
        files = (
            [src_path] if os.path.isfile(src_path)
            else [
                os.path.join(root, fname)
                for root, _, fnames in os.walk(src_path)
                for fname in fnames
                if fname.endswith('.py')
            ]
        )
        resources: list[NormalizedResource] = []
        for fpath in files:
            resources.extend(self._parse_file(fpath))
        return resources

    def _parse_file(self, fpath: str) -> list[NormalizedResource]:
        try:
            with open(fpath, encoding='utf-8') as f:
                source = f.read()
            tree = ast.parse(source, filename=fpath)
        except (OSError, SyntaxError):
            return []

        resources: list[NormalizedResource] = []
        for node in ast.walk(tree):
            # Match: var = SomeModule.ResourceClass("name", key=val, ...)
            # at assignment level
            if not isinstance(node, ast.Assign):
                continue
            val = node.value
            if not isinstance(val, ast.Call):
                continue
            func = val.func
            # Class name must start with uppercase (heuristic for Pulumi resource)
            class_name = ''
            if isinstance(func, ast.Attribute):
                class_name = func.attr
            elif isinstance(func, ast.Name):
                class_name = func.id
            if not class_name or not class_name[0].isupper():
                continue

            # First positional arg is the resource name
            if not val.args or not isinstance(val.args[0], ast.Constant):
                continue
            resource_name = str(val.args[0].value)

            config_keys = [kw.arg for kw in val.keywords if kw.arg and kw.arg != 'opts']

            if config_keys:
                resources.append(NormalizedResource(
                    name=resource_name,
                    resource_type=class_name,
                    config_keys=config_keys,
                ))

        return resources
