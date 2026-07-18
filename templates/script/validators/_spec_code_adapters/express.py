"""
express.py — ExpressAdapter for project_starter_v5.

Extracts NormalizedEndpoint objects from:
  - Spec: api-contract.md (### METHOD /path sections with #### Request Body / #### Response Body tables)
  - Code: JavaScript / TypeScript files — router.{method}('/path', ...) / app.{method}('/path', ...)

No comparison logic here. All comparison lives in verify_spec_code.py.
"""
from __future__ import annotations

import os
import re

from _base import FrameworkAdapter, NormalizedEndpoint, NormalizedField

_HTTP_METHODS = frozenset({'get', 'post', 'put', 'delete', 'patch', 'head', 'options'})
_JS_EXTENSIONS = ('.js', '.ts', '.mjs', '.cjs')


def _parse_field_table(section: str, header: str) -> list[NormalizedField]:
    h = re.search(rf'^#### {re.escape(header)}', section, re.MULTILINE)
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
        if not name or re.match(r'^[-:]+$', name) or name.lower() in ('field', 'name', 'parameter', 'property'):
            continue
        fields.append(NormalizedField(name=name, type=type_str))
    return fields


class ExpressAdapter(FrameworkAdapter):
    """
    Adapter for Express (Node.js) Web App / Microservices projects.

    Spec format (api-contract.md):
      ### POST /orders
      #### Request Body
      | Field | Type | Required | Description |
      | customer_id | int | Yes | ... |

    Code format (JS/TS):
      router.post('/orders', async (req, res) => { ... });
      app.get('/health', handler);
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
                if any(fname.endswith(ext) for ext in _JS_EXTENSIONS)
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
        except OSError:
            return []

        endpoints: list[NormalizedEndpoint] = []
        # Match: <identifier>.(get|post|...)('path' or "path" or `path`, ...)
        pattern = re.compile(
            r'\b\w+\.(get|post|put|delete|patch|head|options)\s*\(\s*[\'"`]([^\'"` \n]+)[\'"`]',
            re.IGNORECASE,
        )
        for m in pattern.finditer(source):
            method = m.group(1).upper()
            path = m.group(2)
            endpoints.append(NormalizedEndpoint(method=method, path=path))

        return endpoints
