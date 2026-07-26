import sys
import tempfile
from pathlib import Path

_ADAPTERS_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "templates" / "script" / "validators" / "_spec_code_adapters"
)
sys.path.insert(0, str(_ADAPTERS_DIR))

from ansible import AnsibleDetector  # noqa: E402


def _extract(yaml_source: str):
    with tempfile.NamedTemporaryFile(suffix=".yml", mode="w", delete=False, encoding="utf-8") as f:
        f.write(yaml_source)
        path = f.name
    try:
        return AnsibleDetector().extract([path])
    finally:
        Path(path).unlink()


def test_bare_task_list_uses_module_arg_name_as_resource_identity():
    src = """
- name: Create bucket
  amazon.aws.s3_bucket:
    name: my-bucket
    region: us-east-1
"""
    resources = _extract(src)
    assert len(resources) == 1
    assert resources[0].name == "my-bucket"
    assert resources[0].resource_type == "amazon.aws.s3_bucket"
    assert set(resources[0].config_keys) == {"region"}


def test_falls_back_to_task_name_when_module_has_no_name_arg():
    src = """
- name: Ensure config file present
  ansible.builtin.copy:
    src: app.conf
    dest: /etc/app.conf
"""
    resources = _extract(src)
    assert resources[0].name == "Ensure config file present"


def test_playbook_with_nested_tasks_and_handlers_is_scanned():
    src = """
- hosts: web
  tasks:
    - name: Launch instance
      amazon.aws.ec2_instance:
        name: web-1
        instance_type: t3.micro
  handlers:
    - name: restart nginx
      ansible.builtin.service:
        name: nginx
        state: restarted
"""
    resources = _extract(src)
    names = {r.name for r in resources}
    assert names == {"web-1", "nginx"}


def test_directives_like_when_and_tags_do_not_confuse_module_detection():
    src = """
- name: Launch instance
  amazon.aws.ec2_instance:
    name: web-1
    instance_type: t3.micro
  when: deploy_web
  tags: [deploy]
  register: result
"""
    resources = _extract(src)
    assert len(resources) == 1
    assert resources[0].resource_type == "amazon.aws.ec2_instance"
    assert "when" not in resources[0].config_keys


def test_block_nested_tasks_are_scanned():
    src = """
- name: Setup
  block:
    - name: Create bucket
      amazon.aws.s3_bucket:
        name: block-bucket
        region: us-east-1
"""
    resources = _extract(src)
    assert resources[0].name == "block-bucket"


def test_play_level_dict_with_no_module_key_produces_no_resource_itself():
    """A play dict (hosts/tasks/handlers) has no module invocation of its own —
    only the tasks nested inside it should become resources."""
    src = """
- hosts: localhost
  become: true
  tasks:
    - name: Create bucket
      amazon.aws.s3_bucket:
        name: only-bucket
        region: us-east-1
"""
    resources = _extract(src)
    assert len(resources) == 1
    assert resources[0].name == "only-bucket"
