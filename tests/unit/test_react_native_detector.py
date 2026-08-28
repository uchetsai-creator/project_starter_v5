import sys
import tempfile
from pathlib import Path

_ADAPTERS_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "templates" / "script" / "validators" / "_spec_code_adapters"
)
sys.path.insert(0, str(_ADAPTERS_DIR))

from react_native import ReactNativeDetector  # noqa: E402

sys.path.remove(str(_ADAPTERS_DIR))  # don't leak onto sys.path — see test_ansible_detector.py


def _extract(source: str):
    with tempfile.NamedTemporaryFile(suffix=".tsx", mode="w", delete=False, encoding="utf-8") as f:
        f.write(source)
        path = f.name
    try:
        return ReactNativeDetector().extract([path])
    finally:
        Path(path).unlink()


def _props_by_name(screens):
    return {s.name: {p.name for p in s.props} for s in screens}


def test_destructured_parameter_still_works():
    src = '''
function HomeScreen({ title, onPress }: Props) {
  return null;
}
'''
    result = _props_by_name(_extract(src))
    assert result == {"HomeScreen": {"title", "onPress"}}


def test_non_destructured_props_param_destructured_in_body():
    src = '''
type ProfileScreenProps = { title: string; onPress: () => void };
function ProfileScreen(props: ProfileScreenProps) {
  const { title, onPress } = props;
  return null;
}
'''
    result = _props_by_name(_extract(src))
    assert result == {"ProfileScreen": {"title", "onPress"}}


def test_non_destructured_props_param_accessed_via_dot():
    src = '''
function StatusScreen(props) {
  return renderStatus(props.status, props.message);
}
'''
    result = _props_by_name(_extract(src))
    assert result == {"StatusScreen": {"status", "message"}}


def test_class_component_props_via_this_props():
    src = '''
class SettingsScreen extends React.Component {
  render() {
    return this.props.title + this.props.onSave;
  }
}
'''
    result = _props_by_name(_extract(src))
    assert result == {"SettingsScreen": {"title", "onSave"}}


def test_const_arrow_non_destructured_props():
    src = '''
const DetailScreen = (props: DetailProps) => {
  const { id, name } = props;
  return null;
};
'''
    result = _props_by_name(_extract(src))
    assert result == {"DetailScreen": {"id", "name"}}
