"""Golden drift-detection coverage for the mobile adapters: react_native, flutter,
swiftui. See tests/unit/test_adapter_drift_detection.py for the full rationale.

Note: ReactNativeDetector never resolves a prop's type (always ''), so its drift
coverage is prop-name presence only, not type-level — see react_native.py's
_extract_destructured_props(). Flutter and SwiftUI both extract real types.
"""
import os
import subprocess
import sys
from pathlib import Path

_VALIDATORS_DIR = Path(__file__).resolve().parent.parent.parent / "templates/script/validators"
SCRIPT = _VALIDATORS_DIR / "verify_spec_code.py"


def _run(*args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True, text=True, encoding="utf-8", errors="replace",
        env={**os.environ, "PYTHONUTF8": "1"},
    )


# ---------------------------------------------------------------------------
# React Native
# ---------------------------------------------------------------------------

_RN_SPEC = """\
### HomeScreen
#### Props
| Name | Type | Required | Description |
|---|---|---|---|
| userId | string | Yes | Current user ID |
| onLogout | () => void | No | Logout handler |
"""

_RN_CODE_CLEAN = """\
function HomeScreen({ userId, onLogout }: HomeScreenProps) {
  return <View />;
}
"""


def test_react_native_clean_spec_and_code_report_no_mismatches(tmp_path):
    spec = tmp_path / "mobile-contract.md"
    spec.write_text(_RN_SPEC, encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    (src / "HomeScreen.tsx").write_text(_RN_CODE_CLEAN, encoding="utf-8")

    result = _run("--adapter", "react_native", "--spec", str(spec), "--src", str(src), "--strict")
    assert "No mismatches" in result.stdout, result.stdout
    assert result.returncode == 0


def test_react_native_missing_prop_is_caught(tmp_path):
    spec = tmp_path / "mobile-contract.md"
    spec.write_text(_RN_SPEC, encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    code = _RN_CODE_CLEAN.replace(", onLogout", "")
    (src / "HomeScreen.tsx").write_text(code, encoding="utf-8")

    result = _run("--adapter", "react_native", "--spec", str(spec), "--src", str(src), "--strict")
    assert "[FAIL]" in result.stdout, result.stdout
    assert "onLogout" in result.stdout, result.stdout
    assert result.returncode == 1


def test_react_native_class_component_props_usage_is_detected(tmp_path):
    """A class component's props (accessed as this.props.x) uses a different code
    path than function components — proves it isn't silently invisible to the
    detector, since that would make an entire class of drift undetectable."""
    spec = tmp_path / "mobile-contract.md"
    spec.write_text(_RN_SPEC, encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    (src / "HomeScreen.tsx").write_text(
        "class HomeScreen extends React.Component {\n"
        "  render() {\n"
        "    return this.props.userId;\n"
        "  }\n"
        "}\n",
        encoding="utf-8",
    )

    result = _run("--adapter", "react_native", "--spec", str(spec), "--src", str(src), "--strict")
    # this.props.onLogout is never referenced in the body, so it's correctly missing.
    assert "[FAIL]" in result.stdout, result.stdout
    assert "onLogout" in result.stdout, result.stdout


# ---------------------------------------------------------------------------
# Flutter
# ---------------------------------------------------------------------------

_FLUTTER_SPEC = """\
### HomeScreen
#### Props
| Name | Type | Required | Description |
|---|---|---|---|
| userId | String | Yes | Current user ID |
| onLogout | VoidCallback | No | Logout handler |
"""

_FLUTTER_CODE_CLEAN = """\
class HomeScreen extends StatelessWidget {
  final String userId;
  final VoidCallback onLogout;

  const HomeScreen({required this.userId, this.onLogout});
}
"""


def test_flutter_clean_spec_and_code_report_no_mismatches(tmp_path):
    spec = tmp_path / "mobile-contract.md"
    spec.write_text(_FLUTTER_SPEC, encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    (src / "home_screen.dart").write_text(_FLUTTER_CODE_CLEAN, encoding="utf-8")

    result = _run("--adapter", "flutter", "--spec", str(spec), "--src", str(src), "--strict")
    assert "No mismatches" in result.stdout, result.stdout
    assert result.returncode == 0


def test_flutter_missing_field_is_caught(tmp_path):
    spec = tmp_path / "mobile-contract.md"
    spec.write_text(_FLUTTER_SPEC, encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    code = _FLUTTER_CODE_CLEAN.replace("  final VoidCallback onLogout;\n", "")
    code = code.replace(", this.onLogout});", "});")
    (src / "home_screen.dart").write_text(code, encoding="utf-8")

    result = _run("--adapter", "flutter", "--spec", str(spec), "--src", str(src), "--strict")
    assert "[FAIL]" in result.stdout, result.stdout
    assert "onLogout" in result.stdout, result.stdout
    assert result.returncode == 1


def test_flutter_field_type_change_is_caught(tmp_path):
    spec = tmp_path / "mobile-contract.md"
    spec.write_text(_FLUTTER_SPEC, encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    code = _FLUTTER_CODE_CLEAN.replace("final String userId;", "final int userId;")
    (src / "home_screen.dart").write_text(code, encoding="utf-8")

    result = _run("--adapter", "flutter", "--spec", str(spec), "--src", str(src), "--strict")
    assert "[FAIL]" in result.stdout, result.stdout
    assert "userId" in result.stdout, result.stdout
    assert result.returncode == 1


def test_flutter_non_widget_class_is_not_detected(tmp_path):
    spec = tmp_path / "mobile-contract.md"
    spec.write_text(_FLUTTER_SPEC, encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    (src / "helper.dart").write_text(
        "class NotAWidget {\n  final String userId;\n}\n", encoding="utf-8",
    )

    result = _run("--adapter", "flutter", "--spec", str(spec), "--src", str(src), "--strict")
    # Nothing in code matches a Widget subclass -> both HomeScreen props report missing.
    assert "[FAIL]" in result.stdout, result.stdout
    assert result.returncode == 1


# ---------------------------------------------------------------------------
# SwiftUI
# ---------------------------------------------------------------------------

_SWIFTUI_SPEC = """\
### HomeScreen
#### Props
| Name | Type | Required | Description |
|---|---|---|---|
| title | String | Yes | Title text |
| isFavorite | Bool | Yes | Favorite flag |
"""

_SWIFTUI_CODE_CLEAN = """\
struct HomeScreen: View {
    let title: String
    @Binding var isFavorite: Bool
    @State private var isExpanded: Bool = false

    var body: some View {
        Text(title)
    }
}
"""


def test_swiftui_clean_spec_and_code_report_no_mismatches(tmp_path):
    spec = tmp_path / "mobile-contract.md"
    spec.write_text(_SWIFTUI_SPEC, encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    (src / "HomeScreen.swift").write_text(_SWIFTUI_CODE_CLEAN, encoding="utf-8")

    result = _run("--adapter", "swiftui", "--spec", str(spec), "--src", str(src), "--strict")
    assert "No mismatches" in result.stdout, result.stdout
    assert result.returncode == 0


def test_swiftui_missing_prop_is_caught(tmp_path):
    spec = tmp_path / "mobile-contract.md"
    spec.write_text(_SWIFTUI_SPEC, encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    code = _SWIFTUI_CODE_CLEAN.replace("    @Binding var isFavorite: Bool\n", "")
    (src / "HomeScreen.swift").write_text(code, encoding="utf-8")

    result = _run("--adapter", "swiftui", "--spec", str(spec), "--src", str(src), "--strict")
    assert "[FAIL]" in result.stdout, result.stdout
    assert "isFavorite" in result.stdout, result.stdout
    assert result.returncode == 1


def test_swiftui_field_type_change_is_caught(tmp_path):
    spec = tmp_path / "mobile-contract.md"
    spec.write_text(_SWIFTUI_SPEC, encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    code = _SWIFTUI_CODE_CLEAN.replace("let title: String", "let title: Int")
    (src / "HomeScreen.swift").write_text(code, encoding="utf-8")

    result = _run("--adapter", "swiftui", "--spec", str(spec), "--src", str(src), "--strict")
    assert "[FAIL]" in result.stdout, result.stdout
    assert "title" in result.stdout, result.stdout
    assert result.returncode == 1


def test_swiftui_private_state_is_not_treated_as_a_prop(tmp_path):
    """@State private var isExpanded must never surface as a prop — proves the
    private-state exclusion (see swiftui.py module docstring) actually holds, not
    just that the clean fixture happens to pass."""
    spec = tmp_path / "mobile-contract.md"
    spec.write_text(_SWIFTUI_SPEC, encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    (src / "HomeScreen.swift").write_text(_SWIFTUI_CODE_CLEAN, encoding="utf-8")

    result = _run(
        "--adapter", "swiftui", "--spec", str(spec), "--src", str(src), "--json",
    )
    import json
    payload = json.loads(result.stdout)
    assert "isExpanded" not in result.stdout
    assert payload["extra_in_code"] == []
