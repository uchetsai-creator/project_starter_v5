"""
flask.py — FlaskDetector (+ legacy FlaskAdapter) for project_starter_v5.

Phase 52.5: FlaskDetector is the primary class — it receives pre-discovered
files from WebAPIAdapter and returns NormalizedEndpoint objects.
FlaskAdapter is kept as a backward-compatible shim.

Extracts NormalizedEndpoint objects from:
  - Spec: api-contract.md (### METHOD /path sections with #### Request Body / #### Response Body tables)
  - Code: Python files — @app.route('/path', methods=['POST']) / @bp.route decorators

No comparison logic here. All comparison lives in verify_spec_code.py.
"""
from __future__ import annotations

import ast
import os
import re

from _base import Detector, FrameworkAdapter, NormalizedEndpoint, NormalizedField
from _utils import _annotation_str, _HTTP_METHODS, _parse_field_table

_SKIP_PARAMS = frozenset({'self', 'request', 'kwargs'})


class FlaskDetector(Detector):
    """
    Framework detector for Flask (Phase 52.5).

    Receives pre-discovered .py files from WebAPIAdapter.
    Returns NormalizedEndpoint for each @app.route / @bp.route decorated function.
    Must not perform file discovery.
    """

    def extract(self, files: list[str]) -> list[NormalizedEndpoint]:
        endpoints: list[NormalizedEndpoint] = []
        for fpath in files:
            if fpath.endswith('.py'):
                endpoints.extend(self._parse_file(fpath))
        return endpoints

    def _parse_file(self, fpath: str) -> list[NormalizedEndpoint]:
        try:
            with open(fpath, encoding='utf-8') as f:
                source = f.read()
            tree = ast.parse(source, filename=fpath)
        except (OSError, SyntaxError):
            return []

        endpoints: list[NormalizedEndpoint] = []
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue

            for dec in node.decorator_list:
                if not isinstance(dec, ast.Call):
                    continue
                func = dec.func
                if not (isinstance(func, ast.Attribute) and func.attr == 'route'):
                    continue
                if not dec.args:
                    continue
                path_node = dec.args[0]
                if not isinstance(path_node, ast.Constant):
                    continue

                path = str(path_node.value)
                methods = ['GET']
                for kw in dec.keywords:
                    if kw.arg == 'methods' and isinstance(kw.value, ast.List):
                        methods = [
                            elt.value.upper()
                            for elt in kw.value.elts
                            if isinstance(elt, ast.Constant)
                        ]

                request_fields = [
                    NormalizedField(name=a.arg, type=_annotation_str(a.annotation))
                    for a in node.args.args
                    if a.arg not in _SKIP_PARAMS
                ]

                for method in methods:
                    if method in _HTTP_METHODS:
                        endpoints.append(NormalizedEndpoint(
                            method=method,
                            path=path,
                            request_fields=list(request_fields),
                            response_fields=[],
                        ))
                break

        return endpoints


class FlaskAdapter(FrameworkAdapter):
    """Deprecated: use the corresponding capability adapter in _capability_*.py. This shim exists for backward compatibility with --adapter <name> CLI usage. Do not extend.

    Adapter for Flask (Python) Web App / Microservices projects.

    Spec format (api-contract.md):
      ### POST /orders
      #### Request Body
      | Field | Type | Required | Description |
      | customer_id | int | Yes | ... |

    Code format (Python):
      @app.route('/orders', methods=['POST'])
      def create_order():
          ...
    """

    def extract_spec(self, spec_path: str) -> list[NormalizedEndpoint]:
        try:
            with open(spec_path, encoding='utf-8') as f:
                text = f.read()
        except OSError:
            return []

        endpoints: list[NormalizedEndpoint] = []
        section_matches = list(re.finditer(
            r'^### (GET|POST|PUT|DELETE|PATCH|HEAD|OPTIONS)\s+(\S+)',
            text, re.MULTILINE | re.IGNORECASE,
        ))

        for idx, match in enumerate(section_matches):
            method = match.group(1).upper()
            path = match.group(2)
            section_start = match.end()
            section_end = (section_matches[idx + 1].start()
                           if idx + 1 < len(section_matches) else len(text))
            section = text[section_start:section_end]

            endpoints.append(NormalizedEndpoint(
                method=method,
                path=path,
                request_fields=_parse_field_table(section, 'Request Body'),
                response_fields=_parse_field_table(section, 'Response Body'),
            ))

        return endpoints

    def extract_code(self, src_path: str) -> list[NormalizedEndpoint]:
        files = (
            [src_path] if os.path.isfile(src_path)
            else [
                os.path.join(root, fname)
                for root, _, fnames in os.walk(src_path)
                for fname in fnames
                if fname.endswith('.py')
            ]
        )
        endpoints: list[NormalizedEndpoint] = []
        for fpath in files:
            endpoints.extend(self._parse_file(fpath))
        return endpoints

    def _parse_file(self, fpath: str) -> list[NormalizedEndpoint]:
        try:
            with open(fpath, encoding='utf-8') as f:
                source = f.read()
            tree = ast.parse(source, filename=fpath)
        except (OSError, SyntaxError):
            return []

        endpoints: list[NormalizedEndpoint] = []
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue

            for dec in node.decorator_list:
                if not isinstance(dec, ast.Call):
                    continue
                func = dec.func
                if not (isinstance(func, ast.Attribute) and func.attr == 'route'):
                    continue
                if not dec.args:
                    continue
                path_node = dec.args[0]
                if not isinstance(path_node, ast.Constant):
                    continue

                path = str(path_node.value)
                methods = ['GET']
                for kw in dec.keywords:
                    if kw.arg == 'methods' and isinstance(kw.value, ast.List):
                        methods = [
                            elt.value.upper()
                            for elt in kw.value.elts
                            if isinstance(elt, ast.Constant)
                        ]

                request_fields = [
                    NormalizedField(name=a.arg, type=_annotation_str(a.annotation))
                    for a in node.args.args
                    if a.arg not in _SKIP_PARAMS
                ]

                for method in methods:
                    if method in _HTTP_METHODS:
                        endpoints.append(NormalizedEndpoint(
                            method=method,
                            path=path,
                            request_fields=list(request_fields),
                            response_fields=[],
                        ))
                break

        return endpoints
