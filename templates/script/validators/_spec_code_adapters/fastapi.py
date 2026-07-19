"""
fastapi.py — FastAPIDetector (+ legacy FastAPIAdapter) for project_starter_v5.

Phase 52.5: FastAPIDetector is the primary class — it receives pre-discovered
files from WebAPIAdapter and returns NormalizedEndpoint objects.
FastAPIAdapter is kept as a backward-compatible shim.

Extracts NormalizedEndpoint objects from:
  - Spec: api-contract.md (### METHOD /path sections with #### Request Body / #### Response Body tables)
  - Code: Python files — @app.{method}("/path") / @router.{method}("/path") decorated functions

No comparison logic here. All comparison lives in verify_spec_code.py.
"""
from __future__ import annotations

import ast
import os
import re

from _base import Detector, FrameworkAdapter, NormalizedEndpoint, NormalizedField
from _utils import _annotation_str, _HTTP_METHODS, _parse_field_table

_SKIP_PARAMS = frozenset({'self', 'request', 'response', 'db', 'session', 'background_tasks'})


class FastAPIDetector(Detector):
    """
    Framework detector for FastAPI (Phase 52.5).

    Receives pre-discovered .py files from WebAPIAdapter.
    Returns NormalizedEndpoint for each @app.{method} / @router.{method} decorated function.
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
                if not (isinstance(func, ast.Attribute) and func.attr.upper() in _HTTP_METHODS):
                    continue
                if not dec.args:
                    continue
                path_node = dec.args[0]
                if not isinstance(path_node, ast.Constant):
                    continue

                path = str(path_node.value)
                method = func.attr.upper()
                request_fields = [
                    NormalizedField(name=a.arg, type=_annotation_str(a.annotation))
                    for a in node.args.args
                    if a.arg not in _SKIP_PARAMS
                ]
                response_fields = []
                if node.returns:
                    ret = _annotation_str(node.returns)
                    if ret and ret.lower() not in ('none', 'any'):
                        response_fields.append(NormalizedField(name='return', type=ret))

                endpoints.append(NormalizedEndpoint(
                    method=method,
                    path=path,
                    request_fields=request_fields,
                    response_fields=response_fields,
                ))
                break

        return endpoints


class FastAPIAdapter(FrameworkAdapter):
    """Deprecated: use the corresponding capability adapter in _capability_*.py. This shim exists for backward compatibility with --adapter <name> CLI usage. Do not extend.

    Adapter for FastAPI (Python) Web App / Microservices projects.

    Spec format (api-contract.md):
      ### POST /orders
      #### Request Body
      | Field | Type | Required | Description |
      | customer_id | int | Yes | ... |
      #### Response Body
      | Field | Type | Description |
      | order_id | int | ... |

    Code format (Python):
      @app.post("/orders")
      async def create_order(body: CreateOrderRequest) -> OrderResponse:
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
                if not (isinstance(func, ast.Attribute) and func.attr.upper() in _HTTP_METHODS):
                    continue
                if not dec.args:
                    continue
                path_node = dec.args[0]
                if not isinstance(path_node, ast.Constant):
                    continue

                path = str(path_node.value)
                method = func.attr.upper()
                request_fields = [
                    NormalizedField(name=a.arg, type=_annotation_str(a.annotation))
                    for a in node.args.args
                    if a.arg not in _SKIP_PARAMS
                ]
                response_fields = []
                if node.returns:
                    ret = _annotation_str(node.returns)
                    if ret and ret.lower() not in ('none', 'any'):
                        response_fields.append(NormalizedField(name='return', type=ret))

                endpoints.append(NormalizedEndpoint(
                    method=method,
                    path=path,
                    request_fields=request_fields,
                    response_fields=response_fields,
                ))
                break

        return endpoints
