"""
django.py — DjangoDetector for project_starter_v5.

Extracts NormalizedEndpoint objects from Django REST Framework code:
  - Code: view functions decorated with @api_view([...]) (rest_framework.decorators),
    correlated with the URL path assigned to them via path()/re_path() calls in
    urlpatterns. Django keeps routing (urls.py) and view logic (views.py) in
    separate files, unlike Flask/FastAPI's inline @app.route — so, unlike its
    siblings, this detector makes two passes across every discovered file before
    it can emit a single endpoint: one to map view name -> URL path, one to map
    view name -> HTTP methods. A view not wired into any urlpatterns scanned in
    this run is skipped (no path to compare against), not fabricated.
  - Spec: api-contract.md — shared web-api format, parsed by WebAPIAdapter, not here.

Scope: function-based views decorated with @api_view. Plain Django views (no
DRF) and class-based views/ViewSets are out of scope for this first pass.
"""
from __future__ import annotations

import ast
import re

from _base import Detector, NormalizedEndpoint, NormalizedField
from _utils import _HTTP_METHODS, _annotation_str, _resolve_output_fields

_SKIP_PARAMS = frozenset({'self', 'request', 'kwargs'})

# path()'s converter syntax: <int:post_id>, <slug:name>, or bare <post_id>.
_PATH_CONVERTER_RE = re.compile(r'<(?:\w+:)?(\w+)>')
# re_path()'s regex named groups: (?P<post_id>\d+).
_NAMED_GROUP_RE = re.compile(r'\(\?P<(\w+)>[^)]*\)')


def _clean_path(raw: str, *, is_regex: bool) -> str:
    """Normalize a Django URL pattern to a plain path with {name} placeholders,
    so it's directly comparable to how a spec author would write the same route:
      path():    'posts/<int:post_id>/'        -> '/posts/{post_id}/'
      re_path(): r'^posts/(?P<post_id>\\d+)/$'  -> '/posts/{post_id}/'
    """
    p = raw
    if is_regex:
        p = p.lstrip('^').rstrip('$')
        p = _NAMED_GROUP_RE.sub(lambda m: '{' + m.group(1) + '}', p)
    else:
        p = _PATH_CONVERTER_RE.sub(lambda m: '{' + m.group(1) + '}', p)
    return '/' + p.lstrip('/')


class DjangoDetector(Detector):
    """
    Framework detector for Django REST Framework (web-api).
    Receives pre-discovered .py files from WebAPIAdapter. Must not perform file discovery.
    """

    def extract(self, files: list[str]) -> list[NormalizedEndpoint]:
        url_paths: dict[str, str] = {}
        views: dict[str, tuple] = {}

        for fpath in files:
            if not fpath.endswith('.py'):
                continue
            try:
                with open(fpath, encoding='utf-8') as f:
                    source = f.read()
                tree = ast.parse(source, filename=fpath)
            except (OSError, SyntaxError):
                continue

            url_paths.update(self._find_url_paths(tree))
            for name, (methods, func_node) in self._find_api_views(tree).items():
                views[name] = (methods, func_node, tree)

        endpoints: list[NormalizedEndpoint] = []
        for name, (methods, func_node, tree) in views.items():
            path = url_paths.get(name)
            if path is None:
                continue

            request_fields = [
                NormalizedField(name=a.arg, type=_annotation_str(a.annotation))
                for a in func_node.args.args
                if a.arg not in _SKIP_PARAMS
            ]
            response_fields = _resolve_output_fields(tree, func_node)

            for method in methods:
                if method in _HTTP_METHODS:
                    endpoints.append(NormalizedEndpoint(
                        method=method,
                        path=path,
                        request_fields=list(request_fields),
                        response_fields=list(response_fields),
                    ))

        return endpoints

    @staticmethod
    def _find_url_paths(tree: ast.AST) -> dict[str, str]:
        """Map view function name -> URL path from any path()/re_path() call
        (Django convention: urlpatterns = [path('orders/', views.list_orders), ...])."""
        mapping: dict[str, str] = {}
        for node in ast.walk(tree):
            if not (isinstance(node, ast.Call) and isinstance(node.func, ast.Name)
                    and node.func.id in ('path', 're_path')):
                continue
            if len(node.args) < 2:
                continue
            path_node, view_node = node.args[0], node.args[1]
            if not (isinstance(path_node, ast.Constant) and isinstance(path_node.value, str)):
                continue

            # view_node is `views.list_orders` (Attribute) or a bare `list_orders` (Name) —
            # not `SomeView.as_view()` (a Call), which is out of scope (class-based views).
            if isinstance(view_node, ast.Attribute):
                view_name = view_node.attr
            elif isinstance(view_node, ast.Name):
                view_name = view_node.id
            else:
                continue

            is_regex = node.func.id == 're_path'
            mapping[view_name] = _clean_path(str(path_node.value), is_regex=is_regex)
        return mapping

    @staticmethod
    def _find_api_views(tree: ast.AST) -> dict[str, tuple]:
        """Map view function name -> (methods, func_node) for every function
        decorated with @api_view([...]) (rest_framework.decorators.api_view)."""
        views: dict[str, tuple] = {}
        for node in ast.walk(tree):
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue

            for dec in node.decorator_list:
                if not isinstance(dec, ast.Call):
                    continue
                func = dec.func
                dec_name = func.id if isinstance(func, ast.Name) else getattr(func, 'attr', None)
                if dec_name != 'api_view' or not dec.args:
                    continue

                methods_node = dec.args[0]
                if isinstance(methods_node, ast.List):
                    methods = [
                        elt.value.upper() for elt in methods_node.elts
                        if isinstance(elt, ast.Constant) and isinstance(elt.value, str)
                    ]
                else:
                    methods = ['GET']

                views[node.name] = (methods, node)
                break

        return views


if __name__ == '__main__':
    import tempfile
    from pathlib import Path

    views_src = '''
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(["GET"])
def list_orders(request):
    return Response({"orders": []})

@api_view(["POST"])
def create_order(request, customer_id: int):
    return Response({"id": 1, "status": "created"})

@api_view(["DELETE"])
def delete_order(request, order_id: int):
    return Response({"deleted": True})

@api_view(["GET"])
def get_order(request, order_id: int):
    return Response({"id": order_id})

def not_wired_up(request):
    """No @api_view — must not be detected as an endpoint."""
    return Response({})
'''
    urls_src = r'''
from django.urls import path, re_path
from . import views

urlpatterns = [
    path("orders/", views.list_orders),
    path("orders/create/", views.create_order),
    path("orders/<int:order_id>/", views.get_order),
    re_path(r"^orders/(?P<order_id>\d+)/delete/$", views.delete_order),
]
'''

    with tempfile.TemporaryDirectory() as tmp:
        views_path = Path(tmp) / "views.py"
        urls_path = Path(tmp) / "urls.py"
        views_path.write_text(views_src, encoding="utf-8")
        urls_path.write_text(urls_src, encoding="utf-8")

        detector = DjangoDetector()
        assert detector.extract([]) == [], "extract([]) must return an empty list"

        endpoints = detector.extract([str(views_path), str(urls_path)])
        by_path = {(e.method, e.path): e for e in endpoints}

        assert ('GET', '/orders/') in by_path, endpoints
        assert ('POST', '/orders/create/') in by_path, endpoints
        assert ('GET', '/orders/{order_id}/') in by_path, endpoints          # path() converter -> {name}
        assert ('DELETE', '/orders/{order_id}/delete/') in by_path, endpoints  # re_path -> {name}
        assert {f.name for f in by_path[('GET', '/orders/')].response_fields} == {'orders'}
        assert {f.name for f in by_path[('POST', '/orders/create/')].request_fields} == {'customer_id'}
        assert {f.name for f in by_path[('POST', '/orders/create/')].response_fields} == {'id', 'status'}
        assert not any(e.path is None for e in endpoints)
        assert len(endpoints) == 4, "not_wired_up (no @api_view) must not produce an endpoint"

    print("[OK] django.py self-test passed")
