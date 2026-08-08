"""
gin.py — GinDetector for project_starter_v5 (Go / Gin web framework).

Extracts NormalizedEndpoint objects from Go source using tree-sitter's Go grammar:
  - Routes: r.GET("/path", handlerFunc) / r.POST(...) / etc. — Gin's
    (*gin.Engine).METHOD(path, handler) / (*gin.RouterGroup).METHOD(...) convention.
  - Request fields: the struct type bound via c.ShouldBindJSON(&x) / c.BindJSON(&x) /
    c.ShouldBind(&x) / c.Bind(&x) inside the handler function, read from that struct's
    field declarations and `json:"..."` tags (falls back to the Go field name when a
    field has no tag, and skips a field entirely when tagged `json:"-"`).
  - Response fields: the struct type passed as c.JSON(status, x) inside the handler.

Requires: pip install tree-sitter tree-sitter-go
Both are optional — not in requirements.txt, same treatment as bandit / eslint-plugin-security
in verify_security.py. extract() returns [] with an install-instructions [WARN] if either
package is missing; it never raises and never blocks projects that don't use Go.

Why tree-sitter instead of regex — every other JS/TS-family detector in this directory
(express.py) is pure regex, matching this project's Constitution ("Package First": prefer an
existing framework convention over new custom machinery). Route registration alone
(r.GET("/path", handler)) is no harder to match with regex than Express's router.get(path,
handler) and wouldn't justify a new dependency on its own. What actually needs a real parser
is the struct side: Go field declarations with json tags are multi-line, can be embedded or
reordered, and the tag lives in a separate raw-string-literal token next to the type — exactly
the shape regex handles unreliably. That's the one part of this detector regex could not do
as well, so it's the one part that justifies tree-sitter.

Known scope limits (documented, not silently swallowed):
  - Struct field types are recorded as the raw Go type text (e.g. 'float64', '*string',
    '[]Item') — no cross-referencing against other structs, no embedded-struct flattening.
  - Request/response variable binding recognizes `var x T` and `x := T{...}` — it does not
    trace values passed through helper functions or reassigned across multiple statements.
  - Only single-argument-list JSON tags of the form `json:"name"` / `json:"name,omitempty"`
    are read; struct tags using other keys (e.g. only `xml:"..."`) fall back to the Go field
    name.
"""
from __future__ import annotations

import re

from _base import Detector, NormalizedEndpoint, NormalizedField

_GO_EXTENSIONS = ('.go',)
_HTTP_METHODS = frozenset({'GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'HEAD', 'OPTIONS'})
_BIND_CALLS = frozenset({'ShouldBindJSON', 'BindJSON', 'ShouldBind', 'Bind'})
_JSON_TAG_RE = re.compile(r'json:"([^",]*)')


def _get_parser():
    """Lazily build a tree-sitter Go parser. Returns None (with a [WARN]) if the
    optional tree-sitter / tree-sitter-go packages aren't installed."""
    try:
        import tree_sitter_go as tsgo  # noqa: PLC0415
        from tree_sitter import Language, Parser  # noqa: PLC0415
    except ImportError:
        print(
            "[WARN] gin adapter requires tree-sitter + tree-sitter-go — skipping .go files.\n"
            "    Install with: pip install tree-sitter tree-sitter-go",
        )
        return None
    return Parser(Language(tsgo.language()))


# ---------------------------------------------------------------------------
# Tree-walking helpers (small, generic — no Go-specific knowledge here)
# ---------------------------------------------------------------------------

def _text(node) -> str:
    return node.text.decode('utf-8', errors='replace')


def _iter_nodes(node, type_name: str):
    if node.type == type_name:
        yield node
    for child in node.children:
        yield from _iter_nodes(child, type_name)


def _children_of_type(node, type_name: str) -> list:
    return [c for c in node.children if c.type == type_name]


def _first_child_of_type(node, type_name: str):
    for c in node.children:
        if c.type == type_name:
            return c
    return None


def _string_literal_value(node) -> str:
    content = (
        _first_child_of_type(node, 'interpreted_string_literal_content')
        or _first_child_of_type(node, 'raw_string_literal_content')
    )
    return _text(content) if content is not None else _text(node).strip('"`')


# ---------------------------------------------------------------------------
# Struct table — name -> [NormalizedField] from `type X struct { ... }`
# ---------------------------------------------------------------------------

def _collect_structs(root) -> dict[str, list[NormalizedField]]:
    structs: dict[str, list[NormalizedField]] = {}
    for decl in _iter_nodes(root, 'type_declaration'):
        for spec in _children_of_type(decl, 'type_spec'):
            name_node = _first_child_of_type(spec, 'type_identifier')
            struct_node = _first_child_of_type(spec, 'struct_type')
            if name_node is None or struct_node is None:
                continue
            structs[_text(name_node)] = _struct_fields(struct_node)
    return structs


def _struct_fields(struct_node) -> list[NormalizedField]:
    fields: list[NormalizedField] = []
    field_list = _first_child_of_type(struct_node, 'field_declaration_list')
    if field_list is None:
        return fields
    for decl in _children_of_type(field_list, 'field_declaration'):
        name_node = _first_child_of_type(decl, 'field_identifier')
        if name_node is None:
            continue
        go_name = _text(name_node)
        type_node = next(
            (c for c in decl.children
             if c.is_named and c.type not in ('field_identifier', 'raw_string_literal',
                                               'interpreted_string_literal')),
            None,
        )
        go_type = _text(type_node) if type_node is not None else ''
        json_name = _json_tag_name(decl)
        if json_name == '-':
            continue
        fields.append(NormalizedField(name=json_name or go_name, type=go_type))
    return fields


def _json_tag_name(field_decl_node) -> str | None:
    for tag_node in _iter_nodes(field_decl_node, 'raw_string_literal'):
        m = _JSON_TAG_RE.search(_text(tag_node))
        if m:
            return m.group(1)
    return None


# ---------------------------------------------------------------------------
# Function table + request/response struct binding inside a handler body
# ---------------------------------------------------------------------------

def _collect_functions(root) -> dict[str, object]:
    functions: dict[str, object] = {}
    for decl in _iter_nodes(root, 'function_declaration'):
        name_node = _first_child_of_type(decl, 'identifier')
        if name_node is not None:
            functions[_text(name_node)] = decl
    return functions


def _local_var_types(func_node) -> dict[str, str]:
    """name -> struct type name, from `var x T` and `x := T{...}` inside func_node."""
    var_types: dict[str, str] = {}

    for spec in _iter_nodes(func_node, 'var_spec'):
        name_node = _first_child_of_type(spec, 'identifier')
        type_node = _first_child_of_type(spec, 'type_identifier')
        if name_node is not None and type_node is not None:
            var_types[_text(name_node)] = _text(type_node)

    for decl in _iter_nodes(func_node, 'short_var_declaration'):
        lists = _children_of_type(decl, 'expression_list')
        if len(lists) != 2:
            continue
        lhs_ident = _first_child_of_type(lists[0], 'identifier')
        composite = _first_child_of_type(lists[1], 'composite_literal')
        if lhs_ident is None or composite is None:
            continue
        type_node = _first_child_of_type(composite, 'type_identifier')
        if type_node is not None:
            var_types[_text(lhs_ident)] = _text(type_node)

    return var_types


def _bound_structs(func_node) -> tuple[str | None, str | None]:
    """Return (request_struct_name, response_struct_name) referenced in func_node's body."""
    var_types = _local_var_types(func_node)
    request_struct: str | None = None
    response_struct: str | None = None

    for call in _iter_nodes(func_node, 'call_expression'):
        selector = _first_child_of_type(call, 'selector_expression')
        if selector is None:
            continue
        method_node = _first_child_of_type(selector, 'field_identifier')
        if method_node is None:
            continue
        method_name = _text(method_node)
        args = _first_child_of_type(call, 'argument_list')
        if args is None:
            continue
        arg_nodes = [c for c in args.children if c.is_named]

        if method_name in _BIND_CALLS and arg_nodes:
            arg = arg_nodes[0]
            ident = None
            if arg.type == 'unary_expression':
                ident = _first_child_of_type(arg, 'identifier')
            elif arg.type == 'identifier':
                ident = arg
            if ident is not None:
                request_struct = var_types.get(_text(ident), request_struct)
        elif method_name == 'JSON' and len(arg_nodes) >= 2:
            resp_arg = arg_nodes[1]
            if resp_arg.type == 'identifier':
                response_struct = var_types.get(_text(resp_arg), response_struct)
            elif resp_arg.type == 'composite_literal':
                type_node = _first_child_of_type(resp_arg, 'type_identifier')
                if type_node is not None:
                    response_struct = _text(type_node)

    return request_struct, response_struct


# ---------------------------------------------------------------------------
# Route table — (method, path, handler_function_name) from r.GET("/path", handler)
# ---------------------------------------------------------------------------

def _collect_routes(root) -> list[tuple[str, str, str]]:
    routes: list[tuple[str, str, str]] = []
    for call in _iter_nodes(root, 'call_expression'):
        selector = _first_child_of_type(call, 'selector_expression')
        if selector is None:
            continue
        method_node = _first_child_of_type(selector, 'field_identifier')
        if method_node is None or _text(method_node) not in _HTTP_METHODS:
            continue
        args = _first_child_of_type(call, 'argument_list')
        if args is None:
            continue
        arg_nodes = [c for c in args.children if c.is_named]
        if len(arg_nodes) < 2:
            continue
        path_node, handler_node = arg_nodes[0], arg_nodes[1]
        if path_node.type not in ('interpreted_string_literal', 'raw_string_literal'):
            continue
        if handler_node.type != 'identifier':
            continue
        routes.append((_text(method_node), _string_literal_value(path_node), _text(handler_node)))
    return routes


# ---------------------------------------------------------------------------
# Detector
# ---------------------------------------------------------------------------

class GinDetector(Detector):
    """Framework detector for Go / Gin (github.com/gin-gonic/gin)."""

    def extract(self, files: list[str]) -> list[NormalizedEndpoint]:
        go_files = [f for f in files if f.endswith(_GO_EXTENSIONS)]
        if not go_files:
            return []
        parser = _get_parser()
        if parser is None:
            return []
        endpoints: list[NormalizedEndpoint] = []
        for fpath in go_files:
            endpoints.extend(self._parse_file(fpath, parser))
        return endpoints

    def _parse_file(self, fpath: str, parser) -> list[NormalizedEndpoint]:
        try:
            with open(fpath, 'rb') as f:
                source = f.read()
        except OSError:
            return []

        try:
            tree = parser.parse(source)
        except Exception:  # noqa: BLE001 — malformed Go source must not crash the run
            return []

        root = tree.root_node
        structs = _collect_structs(root)
        functions = _collect_functions(root)

        endpoints: list[NormalizedEndpoint] = []
        for method, path, handler_name in _collect_routes(root):
            func = functions.get(handler_name)
            request_fields: list[NormalizedField] = []
            response_fields: list[NormalizedField] = []
            if func is not None:
                request_struct, response_struct = _bound_structs(func)
                request_fields = structs.get(request_struct, []) if request_struct else []
                response_fields = structs.get(response_struct, []) if response_struct else []
            endpoints.append(NormalizedEndpoint(
                method=method,
                path=path,
                request_fields=request_fields,
                response_fields=response_fields,
            ))
        return endpoints
