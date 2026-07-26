import sys
import tempfile
from pathlib import Path

_ADAPTERS_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "templates" / "script" / "validators" / "_spec_code_adapters"
)
sys.path.insert(0, str(_ADAPTERS_DIR))

from django import DjangoDetector  # noqa: E402


def _extract(*sources: str):
    paths = []
    for src in sources:
        with tempfile.NamedTemporaryFile(suffix=".py", mode="w", delete=False, encoding="utf-8") as f:
            f.write(src)
            paths.append(f.name)
    try:
        return DjangoDetector().extract(paths)
    finally:
        for p in paths:
            Path(p).unlink()


def test_correlates_path_with_api_view_across_two_files():
    views = """
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(["GET"])
def list_orders(request):
    return Response({"orders": []})
"""
    urls = """
from django.urls import path
from . import views

urlpatterns = [
    path("orders/", views.list_orders),
]
"""
    endpoints = _extract(views, urls)
    assert ("GET", "/orders/") in {(e.method, e.path) for e in endpoints}


def test_re_path_named_group_normalizes_to_brace_placeholder():
    views = """
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(["DELETE"])
def delete_order(request, order_id: int):
    return Response({"deleted": True})
"""
    urls = r"""
from django.urls import re_path
from . import views

urlpatterns = [
    re_path(r"^orders/(?P<order_id>\d+)/$", views.delete_order),
]
"""
    endpoints = _extract(views, urls)
    assert ("DELETE", "/orders/{order_id}/") in {(e.method, e.path) for e in endpoints}


def test_path_converter_normalizes_to_brace_placeholder():
    views = """
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(["GET"])
def get_order(request, order_id: int):
    return Response({"id": order_id})
"""
    urls = """
from django.urls import path
from . import views

urlpatterns = [
    path("orders/<int:order_id>/", views.get_order),
]
"""
    endpoints = _extract(views, urls)
    assert ("GET", "/orders/{order_id}/") in {(e.method, e.path) for e in endpoints}


def test_view_without_api_view_decorator_is_ignored():
    views = """
from rest_framework.response import Response

def plain_django_view(request):
    return Response({})
"""
    urls = """
from django.urls import path
from . import views

urlpatterns = [
    path("legacy/", views.plain_django_view),
]
"""
    endpoints = _extract(views, urls)
    assert endpoints == []


def test_api_view_not_wired_into_any_urlpatterns_is_skipped():
    views = """
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(["GET"])
def orphaned_view(request):
    return Response({})
"""
    endpoints = _extract(views)
    assert endpoints == []


def test_bare_name_view_reference_is_resolved():
    """path() referencing an imported view directly by name, not via views.<name>."""
    views = """
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(["GET"])
def health(request):
    return Response({"status": "ok"})
"""
    urls = """
from django.urls import path
from .views import health

urlpatterns = [
    path("health/", health),
]
"""
    endpoints = _extract(views, urls)
    assert ("GET", "/health/") in {(e.method, e.path) for e in endpoints}


def test_multiple_methods_on_one_api_view_each_become_an_endpoint():
    views = """
from rest_framework.decorators import api_view
from rest_framework.response import Response

@api_view(["GET", "HEAD"])
def list_items(request):
    return Response({"items": []})
"""
    urls = """
from django.urls import path
from . import views

urlpatterns = [
    path("items/", views.list_items),
]
"""
    endpoints = _extract(views, urls)
    methods = {e.method for e in endpoints if e.path == "/items/"}
    assert methods == {"GET", "HEAD"}
