"""Golden drift-detection coverage for the IaC adapters: terraform, pulumi, ansible.
See tests/unit/test_adapter_drift_detection.py for the full rationale.

Note: NormalizedResource's comparison key is the resource `name` only (resource_type
is informational, not compared — see verify_spec_code.py's _FORM_HANDLERS), and every
config_keys field is built with type='' on both sides, so type-mismatch drift never
fires here — only missing/extra config keys are detectable for IaC resources.
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
# Terraform
# ---------------------------------------------------------------------------

_TERRAFORM_SPEC = """\
### web_server (aws_instance)
#### Configuration
| Key | Value | Description |
|---|---|---|
| instance_type | t3.micro | EC2 instance type |
| ami | ami-0abc | Amazon Machine Image |
"""

_TERRAFORM_CODE_CLEAN = """\
resource "aws_instance" "web_server" {
  instance_type = "t3.micro"
  ami           = "ami-0abc"
}
"""


def test_terraform_clean_spec_and_code_report_no_mismatches(tmp_path):
    spec = tmp_path / "topology.md"
    spec.write_text(_TERRAFORM_SPEC, encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    (src / "main.tf").write_text(_TERRAFORM_CODE_CLEAN, encoding="utf-8")

    result = _run("--adapter", "terraform", "--spec", str(spec), "--src", str(src), "--strict")
    assert "No mismatches" in result.stdout, result.stdout
    assert result.returncode == 0


def test_terraform_missing_config_key_is_caught(tmp_path):
    spec = tmp_path / "topology.md"
    spec.write_text(_TERRAFORM_SPEC, encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    code = _TERRAFORM_CODE_CLEAN.replace('  ami           = "ami-0abc"\n', '')
    (src / "main.tf").write_text(code, encoding="utf-8")

    result = _run("--adapter", "terraform", "--spec", str(spec), "--src", str(src), "--strict")
    assert "[FAIL]" in result.stdout, result.stdout
    assert "ami" in result.stdout, result.stdout
    assert result.returncode == 1


def test_terraform_extra_config_key_is_caught(tmp_path):
    spec = tmp_path / "topology.md"
    spec.write_text(_TERRAFORM_SPEC, encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    # Drift: an extra key added in code that the spec never declared.
    code = _TERRAFORM_CODE_CLEAN.replace(
        '  ami           = "ami-0abc"\n', '  ami           = "ami-0abc"\n  monitoring    = true\n'
    )
    (src / "main.tf").write_text(code, encoding="utf-8")

    result = _run("--adapter", "terraform", "--spec", str(spec), "--src", str(src), "--strict")
    assert "[FAIL]" in result.stdout, result.stdout
    assert "monitoring" in result.stdout, result.stdout
    assert result.returncode == 1


def test_terraform_key_nested_in_block_is_not_top_level(tmp_path):
    """A key inside a nested block (e.g. tags = { Name = "x" }) belongs to the nested
    structure, not the resource itself — proves the parser doesn't flatten nested
    blocks into false top-level config key drift."""
    spec = tmp_path / "topology.md"
    spec.write_text(_TERRAFORM_SPEC, encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    code = _TERRAFORM_CODE_CLEAN.replace(
        '  ami           = "ami-0abc"\n',
        '  ami           = "ami-0abc"\n  tags = {\n    Name = "web"\n  }\n',
    )
    (src / "main.tf").write_text(code, encoding="utf-8")

    result = _run("--adapter", "terraform", "--spec", str(spec), "--src", str(src), "--strict")
    # "tags" is a new top-level key (expected drift); "Name" (nested inside tags) must not appear.
    assert "tags" in result.stdout, result.stdout
    assert "Name" not in result.stdout, result.stdout


# ---------------------------------------------------------------------------
# Pulumi
# ---------------------------------------------------------------------------

_PULUMI_SPEC = """\
### web_server (aws:ec2/instance:Instance)
#### Configuration
| Key | Value | Description |
|---|---|---|
| instance_type | t3.micro | EC2 instance type |
| ami | ami-0abc | Amazon Machine Image |
"""

_PULUMI_CODE_CLEAN = """\
import pulumi_aws as aws

web_server = aws.ec2.Instance("web_server",
    instance_type="t3.micro",
    ami="ami-0abc",
)
"""


def test_pulumi_clean_spec_and_code_report_no_mismatches(tmp_path):
    spec = tmp_path / "topology.md"
    spec.write_text(_PULUMI_SPEC, encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    (src / "__main__.py").write_text(_PULUMI_CODE_CLEAN, encoding="utf-8")

    result = _run("--adapter", "pulumi", "--spec", str(spec), "--src", str(src), "--strict")
    assert "No mismatches" in result.stdout, result.stdout
    assert result.returncode == 0


def test_pulumi_missing_config_key_is_caught(tmp_path):
    spec = tmp_path / "topology.md"
    spec.write_text(_PULUMI_SPEC, encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    code = _PULUMI_CODE_CLEAN.replace('    ami="ami-0abc",\n', '')
    (src / "__main__.py").write_text(code, encoding="utf-8")

    result = _run("--adapter", "pulumi", "--spec", str(spec), "--src", str(src), "--strict")
    assert "[FAIL]" in result.stdout, result.stdout
    assert "ami" in result.stdout, result.stdout
    assert result.returncode == 1


# ---------------------------------------------------------------------------
# Ansible
# ---------------------------------------------------------------------------

_ANSIBLE_SPEC = """\
### web-server-1 (amazon.aws.ec2_instance)
#### Configuration
| Key | Value | Description |
|---|---|---|
| instance_type | t3.micro | EC2 instance type |
| image_id | ami-12345 | AMI |
"""

_ANSIBLE_CODE_CLEAN = """\
- name: Configure infrastructure
  hosts: localhost
  tasks:
    - name: Launch web server
      amazon.aws.ec2_instance:
        name: web-server-1
        instance_type: t3.micro
        image_id: ami-12345
"""


def test_ansible_clean_spec_and_code_report_no_mismatches(tmp_path):
    spec = tmp_path / "topology.md"
    spec.write_text(_ANSIBLE_SPEC, encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    (src / "playbook.yml").write_text(_ANSIBLE_CODE_CLEAN, encoding="utf-8")

    result = _run("--adapter", "ansible", "--spec", str(spec), "--src", str(src), "--strict")
    assert "No mismatches" in result.stdout, result.stdout
    assert result.returncode == 0


def test_ansible_missing_config_key_is_caught(tmp_path):
    spec = tmp_path / "topology.md"
    spec.write_text(_ANSIBLE_SPEC, encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    code = _ANSIBLE_CODE_CLEAN.replace("        image_id: ami-12345\n", "")
    (src / "playbook.yml").write_text(code, encoding="utf-8")

    result = _run("--adapter", "ansible", "--spec", str(spec), "--src", str(src), "--strict")
    assert "[FAIL]" in result.stdout, result.stdout
    assert "image_id" in result.stdout, result.stdout
    assert result.returncode == 1


def test_ansible_task_when_directive_does_not_confuse_module_detection(tmp_path):
    """A task's own `when:` conditional must not be mistaken for the module
    invocation key — proves the meta-key exclusion list actually works."""
    spec = tmp_path / "topology.md"
    spec.write_text(_ANSIBLE_SPEC, encoding="utf-8")
    src = tmp_path / "src"
    src.mkdir()
    code = _ANSIBLE_CODE_CLEAN.replace(
        "        image_id: ami-12345\n",
        "        image_id: ami-12345\n      when: deploy_web\n",
    )
    (src / "playbook.yml").write_text(code, encoding="utf-8")

    result = _run("--adapter", "ansible", "--spec", str(spec), "--src", str(src), "--strict")
    assert "No mismatches" in result.stdout, result.stdout
    assert result.returncode == 0
