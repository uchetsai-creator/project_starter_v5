"""
terraform.py — TerraformDetector (+ legacy TerraformAdapter) for project_starter_v5.

Phase 52.5: TerraformDetector is the primary class — it receives pre-discovered
files from IaCAdapter and returns NormalizedResource objects.
TerraformAdapter is kept as a backward-compatible shim.

Extracts NormalizedResource objects from:
  - Spec: topology.md (### label (resource_type) sections with #### Configuration tables)
  - Code: .tf HCL files — resource "type" "name" { key = value } blocks

No comparison logic here. All comparison lives in verify_spec_code.py.
"""
from __future__ import annotations

import os
import re

from _base import Detector, FrameworkAdapter, NormalizedResource
from _utils import _parse_config_table

_TF_EXTENSIONS = ('.tf',)


class TerraformDetector(Detector):
    """
    Framework detector for Terraform HCL (Phase 52.5).

    Receives pre-discovered .tf files from IaCAdapter.
    Returns NormalizedResource for each resource block.
    Must not perform file discovery.
    """

    def extract(self, files: list[str]) -> list[NormalizedResource]:
        resources: list[NormalizedResource] = []
        for fpath in files:
            if any(fpath.endswith(ext) for ext in _TF_EXTENSIONS):
                resources.extend(self._parse_file(fpath))
        return resources

    def _parse_file(self, fpath: str) -> list[NormalizedResource]:
        try:
            with open(fpath, encoding='utf-8') as f:
                source = f.read()
        except OSError:
            return []

        resources: list[NormalizedResource] = []
        block_pattern = re.compile(
            r'\bresource\s+"([^"]+)"\s+"([^"]+)"\s*\{([^}]*(?:\{[^}]*\}[^}]*)*)\}',
            re.DOTALL,
        )
        for m in block_pattern.finditer(source):
            rtype = m.group(1)
            label = m.group(2)
            body = m.group(3)
            config_keys = re.findall(r'^\s{0,4}(\w+)\s*=', body, re.MULTILINE)
            resources.append(NormalizedResource(
                name=label,
                resource_type=rtype,
                config_keys=config_keys,
            ))

        return resources


class TerraformAdapter(FrameworkAdapter):
    """Deprecated: use the corresponding capability adapter in _capability_*.py. This shim exists for backward compatibility with --adapter <name> CLI usage. Do not extend.

    Adapter for Terraform HCL IaC / DevOps projects.

    Spec format (topology.md):
      ### web_server (aws_instance)
      #### Configuration
      | Key | Value | Description |
      |---|---|---|
      | instance_type | t3.micro | EC2 instance type |
      | ami | ami-0abc | Amazon Machine Image |

    Code format (.tf):
      resource "aws_instance" "web_server" {
        instance_type = "t3.micro"
        ami           = "ami-0abc"
      }
    """

    def extract_spec(self, spec_path: str) -> list[NormalizedResource]:
        try:
            with open(spec_path, encoding='utf-8') as f:
                text = f.read()
        except OSError:
            return []

        resources: list[NormalizedResource] = []
        # Match: ### label (resource_type)  or  ### label
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

            config_keys = _parse_config_table(section)
            resources.append(NormalizedResource(
                name=label,
                resource_type=rtype,
                config_keys=config_keys,
            ))

        return resources

    def extract_code(self, src_path: str) -> list[NormalizedResource]:
        files = (
            [src_path] if os.path.isfile(src_path)
            else [
                os.path.join(root, fname)
                for root, _, fnames in os.walk(src_path)
                for fname in fnames
                if any(fname.endswith(ext) for ext in _TF_EXTENSIONS)
            ]
        )
        resources: list[NormalizedResource] = []
        for fpath in files:
            resources.extend(self._parse_file(fpath))
        return resources

    def _parse_file(self, fpath: str) -> list[NormalizedResource]:
        return TerraformDetector()._parse_file(fpath)
