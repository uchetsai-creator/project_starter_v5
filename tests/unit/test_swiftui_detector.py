import sys
import tempfile
from pathlib import Path

_ADAPTERS_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "templates" / "script" / "validators" / "_spec_code_adapters"
)
sys.path.insert(0, str(_ADAPTERS_DIR))

from swiftui import SwiftuiDetector  # noqa: E402

sys.path.remove(str(_ADAPTERS_DIR))  # don't leak onto sys.path — see test_ansible_detector.py


def _extract(source: str):
    with tempfile.NamedTemporaryFile(suffix=".swift", mode="w", delete=False, encoding="utf-8") as f:
        f.write(source)
        path = f.name
    try:
        return SwiftuiDetector().extract([path])
    finally:
        Path(path).unlink()


def test_stored_properties_become_props():
    src = """
struct ProfileScreen: View {
    let username: String
    let age: Int

    var body: some View {
        Text(username)
    }
}
"""
    screens = _extract(src)
    assert len(screens) == 1
    assert screens[0].name == "ProfileScreen"
    props = {f.name: f.type for f in screens[0].props}
    assert props == {"username": "String", "age": "Int"}


def test_private_state_is_not_a_prop():
    src = """
struct CounterScreen: View {
    let label: String
    @State private var count: Int = 0

    var body: some View {
        Text(label)
    }
}
"""
    screens = _extract(src)
    props = {f.name for f in screens[0].props}
    assert props == {"label"}


def test_binding_property_wrapper_is_a_prop():
    src = """
struct ToggleScreen: View {
    @Binding var isOn: Bool

    var body: some View {
        Toggle("On", isOn: $isOn)
    }
}
"""
    screens = _extract(src)
    props = {f.name: f.type for f in screens[0].props}
    assert props == {"isOn": "Bool"}


def test_computed_property_body_is_not_treated_as_a_prop():
    src = """
struct EmptyScreen: View {
    var body: some View {
        Text("Hi")
    }
}
"""
    screens = _extract(src)
    assert screens[0].props == []


def test_multiple_protocol_conformance_still_detected_as_view():
    src = """
struct ListItemScreen: View, Identifiable {
    let id: Int
    var body: some View {
        Text("Item")
    }
}
"""
    screens = _extract(src)
    assert screens[0].name == "ListItemScreen"


def test_class_is_not_detected_as_a_screen():
    src = """
class ViewModel {
    let count: Int = 0
}
"""
    assert _extract(src) == []


def test_two_view_structs_do_not_leak_properties_into_each_other():
    src = """
struct FirstScreen: View {
    let a: String

    var body: some View {
        Text(a)
    }
}

struct SecondScreen: View {
    let b: Int

    var body: some View {
        Text("second")
    }
}
"""
    screens = _extract(src)
    by_name = {s.name: {f.name for f in s.props} for s in screens}
    assert by_name == {"FirstScreen": {"a"}, "SecondScreen": {"b"}}
