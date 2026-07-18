"""
python_library.py — PythonLibraryAdapter for project_starter_v5.

Extracts NormalizedFunction objects from:
  - Spec: public-api.md (### function_name sections with #### Parameters / #### Returns tables)
  - Code: Python files — functions listed in __all__ + their signatures

No comparison logic here. All comparison lives in verify_spec_code.py.
"""
from __future__ import annotations

import ast
import os
import re

from _base import FrameworkAdapter, NormalizedField, NormalizedFunction

_SKIP_PARAMS = frozenset({'self', 'cls', 'kwargs', 'args'})


def _annotation_str(node) -> str:
    if node is None:
        return ''
    try:
        return ast.unparse(node)
    except AttributeError:
        if isinstance(node, ast.Name):
            return node.id
        if isinstance(node, ast.Constant):
            return str(node.value)
        if isinstance(node, ast.Attribute):
            return f"{_annotation_str(node.value)}.{node.attr}"
        return ''


class PythonLibraryAdapter(FrameworkAdapter):
    """
    Adapter for Python Library / SDK projects.

    Spec format (public-api.md):
      ### function_name
      #### Parameters
      | Name | Type | Description |
      |---|---|---|
      | param1 | str | ... |
      #### Returns
      | Type | Description |
      |---|---|
      | dict | ... |

    Code format (Python):
      __all__ = ['function_name', ...]

      def function_name(param1: str, param2: int = 0) -> dict:
          ...
    """

    def extract_spec(self, spec_path: str) -> list[NormalizedFunction]:
        with open(spec_path, encoding='utf-8') as f:
            text = f.read()

        functions: list[NormalizedFunction] = []
        section_matches = list(re.finditer(r'^### (`?)(\w+)\1', text, re.MULTILINE))

        for idx, match in enumerate(section_matches):
            func_name = match.group(2)
            section_start = match.end()
            section_end = (section_matches[idx + 1].start()
                           if idx + 1 < len(section_matches) else len(text))
            section = text[section_start:section_end]

            functions.append(NormalizedFunction(
                name=func_name,
                params=self._parse_params_table(section),
                return_type=self._parse_return_type(section),
            ))

        return functions

    def _parse_params_table(self, section: str) -> list[NormalizedField]:
        h = re.search(r'^#### Parameters', section, re.MULTILINE)
        if not h:
            return []
        table_text = section[h.end():]
        next_h = re.search(r'^#{3,4} ', table_text, re.MULTILINE)
        if next_h:
            table_text = table_text[:next_h.start()]

        fields: list[NormalizedField] = []
        for row in re.finditer(r'(?m)^\|(.+)\|$', table_text):
            cols = [c.strip().strip('`') for c in row.group(1).split('|')]
            if len(cols) < 2:
                continue
            name, type_str = cols[0], cols[1] if len(cols) > 1 else ''
            if not name or re.match(r'^[-:]+$', name) or name.lower() in ('name', 'parameter', 'param'):
                continue
            fields.append(NormalizedField(name=name, type=type_str))
        return fields

    def _parse_return_type(self, section: str) -> str:
        h = re.search(r'^#### Returns', section, re.MULTILINE)
        if not h:
            return ''
        table_text = section[h.end():]
        next_h = re.search(r'^#{3,4} ', table_text, re.MULTILINE)
        if next_h:
            table_text = table_text[:next_h.start()]
        for row in re.finditer(r'(?m)^\|(.+)\|$', table_text):
            cols = [c.strip().strip('`') for c in row.group(1).split('|')]
            if cols and not re.match(r'^[-:]+$', cols[0]) and cols[0].lower() not in ('type', 'return type'):
                return cols[0]
        return ''

    def extract_code(self, src_path: str) -> list[NormalizedFunction]:
        files = (
            [src_path] if os.path.isfile(src_path)
            else [
                os.path.join(root, fname)
                for root, _, fnames in os.walk(src_path)
                for fname in fnames
                if fname.endswith('.py')
            ]
        )

        # Collect __all__ names across all files
        public_names: set[str] = set()
        for fpath in files:
            public_names.update(self._extract_all_names(fpath))

        functions: list[NormalizedFunction] = []
        seen: set[str] = set()
        for fpath in files:
            for fn in self._parse_file(fpath, public_names):
                if fn.name not in seen:
                    seen.add(fn.name)
                    functions.append(fn)
        return functions

    def _extract_all_names(self, fpath: str) -> list[str]:
        try:
            with open(fpath, encoding='utf-8') as f:
                source = f.read()
            tree = ast.parse(source, filename=fpath)
        except (OSError, SyntaxError):
            return []

        names: list[str] = []
        for node in ast.walk(tree):
            if not isinstance(node, ast.Assign):
                continue
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == '__all__':
                    if isinstance(node.value, ast.List):
                        names.extend(
                            elt.value for elt in node.value.elts
                            if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
                        )
        return names

    def _parse_file(self, fpath: str, public_names: set[str]) -> list[NormalizedFunction]:
        try:
            with open(fpath, encoding='utf-8') as f:
                source = f.read()
            tree = ast.parse(source, filename=fpath)
        except (OSError, SyntaxError):
            return []

        functions: list[NormalizedFunction] = []
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            # If __all__ is defined, only include listed names; else include all public names
            if public_names and node.name not in public_names:
                continue
            if not public_names and node.name.startswith('_'):
                continue

            params = [
                NormalizedField(name=a.arg, type=_annotation_str(a.annotation))
                for a in node.args.args
                if a.arg not in _SKIP_PARAMS
            ]
            return_type = _annotation_str(node.returns) if node.returns else ''
            functions.append(NormalizedFunction(
                name=node.name,
                params=params,
                return_type=return_type,
            ))

        return functions
