#!/usr/bin/env python3
"""
generate_openapi.py — generate an OpenAPI 3.0 document from api-contract.md.

Bridges this framework's narrative markdown spec to the tooling ecosystem built around
real OpenAPI schemas (oasdiff, Schemathesis, client codegen, ...) without making
api-contract.md itself stop being the authored, human-readable source of truth:

  api-contract.md (human-authored: endpoints, Design Notes, Edge Cases, NFRs, ...)
          │
          ▼  WebAPIAdapter.extract_spec()  ← reused as-is from
          │    _spec_code_adapters/_capability_web_api.py; this is the SAME parser
          │    verify_spec_code.py already uses to compare the spec against code
  NormalizedEndpoint[]  (method, path, request_fields, response_fields)
          │
          ▼  this script (new: serializes the other direction)
  openapi.yaml  ← generated artifact, not hand-edited; regenerate after every
                   api-contract.md change, same lifecycle as .ai/AI_CONTEXT.md

api-contract.md keeps everything a schema has no field for — Design Notes explaining why
two similar endpoints stay separate, the Edge Cases table, Non-Functional Requirements,
the WebSocket/GraphQL/gRPC sections. None of that is lost, because none of it was ever
part of what extract_spec() reads into a NormalizedEndpoint in the first place — this
script only ever sees the same method/path/field data verify_spec_code.py already
compares against code. See README.md -> "Beyond static comparison: runtime contract
testing" for what oasdiff / Schemathesis do with the output.

Known scope limits (documented, not silently swallowed):
  - Response status codes are inferred from HTTP method (GET/PUT/PATCH -> 200, POST -> 201,
    DELETE -> 204, HEAD/OPTIONS -> 200) — api-contract.md's per-endpoint "Success 201
    Created" text is not machine-parsed today, so an endpoint using a non-default code for
    its method needs the generated YAML hand-corrected, or --status-map overridden per path.
  - Field types are mapped through the same alias groups verify_spec_code.py's
    _normalize_type() uses (string/str/text -> string, integer/int/long -> integer, ...);
    an unrecognized type string passes through as OpenAPI `string` with the original text
    kept in `description` — never silently dropped, never guessed into a wrong type.
  - WebSocket / GraphQL / gRPC sections are not converted — OpenAPI only describes REST.
  - DELETE endpoints get no request/response body (matches the template's `204 No Content`
    convention) even if response_fields were parsed — 204 responses cannot carry a body.

Usage:
  python3 templates/script/generators/generate_openapi.py \\
      --spec docs/specs/api-contract.md --output openapi.yaml
  python3 templates/script/generators/generate_openapi.py \\
      --spec docs/specs/api-contract.md --title "Orders API" --api-version 1.2.0
"""
from __future__ import annotations

import argparse
import os
import re
import sys

import yaml

_ADAPTER_DIR = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), '..', 'validators', '_spec_code_adapters',
)
sys.path.insert(0, os.path.abspath(_ADAPTER_DIR))

from _capability_web_api import WebAPIAdapter  # noqa: E402

_DEFAULT_STATUS = {
    'GET': '200', 'PUT': '200', 'PATCH': '200',
    'POST': '201', 'DELETE': '204', 'HEAD': '200', 'OPTIONS': '200',
}

# Same alias groups as verify_spec_code.py's _TYPE_ALIAS_GROUPS, remapped to the OpenAPI
# type vocabulary instead of a canonical comparison token.
_TYPE_MAP = {
    'string': 'string', 'str': 'string', 'text': 'string', 'char': 'string', 'varchar': 'string',
    'uuid': 'string', 'date': 'string', 'datetime': 'string', 'email': 'string',
    'boolean': 'boolean', 'bool': 'boolean',
    'integer': 'integer', 'int': 'integer', 'long': 'integer',
    'number': 'number', 'float': 'number', 'double': 'number', 'decimal': 'number',
    'array': 'array', 'list': 'array',
    'object': 'object', 'dict': 'object', 'map': 'object',
}

_PATH_PARAM_RE = re.compile(r':(\w+)')


def _to_openapi_path(path: str) -> str:
    """Convert :param (Express/Ruby-style, used in this framework's api-contract.md
    template — see README.md's own note on this) to OpenAPI's required {param} form."""
    return _PATH_PARAM_RE.sub(r'{\1}', path)


def _openapi_type(raw_type: str) -> tuple[str, str | None]:
    """Return (openapi_type, original_text_if_unmapped)."""
    key = raw_type.strip().lower()
    key = re.sub(r'^(optional|list|array)\[(.+)\]$', r'\2', key).split('|')[0].strip().rstrip('?')
    mapped = _TYPE_MAP.get(key)
    if mapped:
        return mapped, None
    return 'string', raw_type.strip() or None


def _fields_schema(fields) -> dict:
    properties = {}
    for f in fields:
        otype, original = _openapi_type(f.type or '')
        prop: dict = {'type': otype}
        if original:
            prop['description'] = f'original spec type: {original}'
        properties[f.name] = prop
    schema: dict = {'type': 'object'}
    if properties:
        schema['properties'] = properties
    return schema


def build_openapi(
    endpoints: list,
    title: str,
    api_version: str,
    status_map: dict[str, str] | None = None,
) -> dict:
    status_map = status_map or {}
    paths: dict = {}

    for ep in endpoints:
        oapi_path = _to_openapi_path(ep.path)
        method = ep.method.lower()
        operation: dict = {
            'operationId': f'{ep.method.lower()}_{re.sub(r"[^a-zA-Z0-9]+", "_", ep.path).strip("_")}',
            'responses': {},
        }

        if ep.method.upper() in ('POST', 'PUT', 'PATCH') and ep.request_fields:
            operation['requestBody'] = {
                'required': True,
                'content': {'application/json': {'schema': _fields_schema(ep.request_fields)}},
            }

        status = status_map.get(f'{ep.method.upper()}:{ep.path}') or _DEFAULT_STATUS.get(
            ep.method.upper(), '200',
        )
        if status == '204':
            operation['responses'][status] = {'description': 'No Content'}
        else:
            resp: dict = {'description': 'Success'}
            if ep.response_fields:
                resp['content'] = {
                    'application/json': {'schema': _fields_schema(ep.response_fields)},
                }
            operation['responses'][status] = resp

        paths.setdefault(oapi_path, {})[method] = operation

    return {
        'openapi': '3.0.3',
        'info': {'title': title, 'version': api_version},
        'paths': paths,
    }


def main() -> None:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')

    parser = argparse.ArgumentParser(
        description='Generate an OpenAPI 3.0 document from api-contract.md (derived artifact — regenerate, do not hand-edit).',
    )
    parser.add_argument('--spec', required=True, metavar='PATH', help='Path to api-contract.md')
    parser.add_argument('--output', default='openapi.yaml', metavar='PATH', help='Output file (default: openapi.yaml)')
    parser.add_argument('--title', default='API', help='OpenAPI info.title (default: API)')
    parser.add_argument('--api-version', default='0.1.0', help='OpenAPI info.version (default: 0.1.0)')
    args = parser.parse_args()

    if not os.path.exists(args.spec):
        print(f'error: spec file not found: {args.spec}', file=sys.stderr)
        sys.exit(2)

    endpoints = WebAPIAdapter().extract_spec(args.spec)
    if not endpoints:
        print(
            f'[WARN] no ### METHOD /path sections found in {args.spec} — nothing to generate.\n'
            '    This does not necessarily mean the spec is empty: WebSocket/GraphQL/gRPC\n'
            '    sections are not REST endpoints and are never converted (see this script\'s\n'
            '    docstring). Check the file has at least one REST "### METHOD /path" heading.',
        )
        sys.exit(0)

    doc = build_openapi(endpoints, args.title, args.api_version)

    with open(args.output, 'w', encoding='utf-8') as f:
        yaml.safe_dump(doc, f, sort_keys=False, default_flow_style=False, allow_unicode=True)

    print(f'[OK] Generated {len(endpoints)} endpoint(s) -> {args.output}')
    print('    This file is a derived artifact — regenerate after every api-contract.md')
    print('    change rather than hand-editing it; consider adding it to .gitignore.')


if __name__ == '__main__':
    main()
