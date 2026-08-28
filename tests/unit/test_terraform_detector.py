import sys
import tempfile
from pathlib import Path

_ADAPTERS_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "templates" / "script" / "validators" / "_spec_code_adapters"
)
sys.path.insert(0, str(_ADAPTERS_DIR))

from terraform import TerraformDetector, _top_level_keys  # noqa: E402

sys.path.remove(str(_ADAPTERS_DIR))  # don't leak onto sys.path — see test_ansible_detector.py


def _extract(hcl_source: str):
    with tempfile.NamedTemporaryFile(suffix=".tf", mode="w", delete=False, encoding="utf-8") as f:
        f.write(hcl_source)
        path = f.name
    try:
        return TerraformDetector().extract([path])
    finally:
        Path(path).unlink()


def test_nested_map_keys_excluded_from_top_level_config():
    body = '''
  ami           = "ami-123456"
  instance_type = "t3.micro"

  tags = {
    Name = "web-server"
    Env  = "prod"
  }

  root_block_device {
    volume_size = 20
  }
'''
    assert _top_level_keys(body) == ["ami", "instance_type", "tags"]


def test_real_resource_reports_only_top_level_keys():
    src = '''
resource "aws_instance" "web" {
  ami           = "ami-123456"
  instance_type = "t3.micro"

  tags = {
    Name = "web-server"
    Env  = "prod"
  }
}
'''
    resources = _extract(src)
    assert len(resources) == 1
    assert set(resources[0].config_keys) == {"ami", "instance_type", "tags"}
    assert "Name" not in resources[0].config_keys
    assert "Env" not in resources[0].config_keys
