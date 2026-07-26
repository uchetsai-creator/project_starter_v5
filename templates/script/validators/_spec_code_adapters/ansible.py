"""
ansible.py — AnsibleDetector for project_starter_v5.

Extracts NormalizedResource objects from Ansible playbook/task YAML — a
genuinely different shape from Terraform/Pulumi: declarative YAML, not code,
with more than one valid file layout: a bare task list (a role's
`tasks/main.yml`), a full playbook (a list of plays, each with `tasks:` /
`pre_tasks:` / `post_tasks:` / `handlers:`), or tasks nested under `block:`.

Each task is a dict with a `name:` (human description) and exactly one other
key that names the Ansible *module* being invoked (e.g.
`amazon.aws.ec2_instance`, `file`, `template`), whose value is the module's
argument dict — that module name is the resource_type.

The resource's identity (what a Terraform label or Pulumi resource-name
argument gives for free) comes from the module argument dict's own `name:`
parameter when present — the convention nearly every cloud/file/user module
follows (`amazon.aws.s3_bucket: name: my-bucket`) — falling back to the
task's own `name:` description when the module has no `name` argument of
its own. `config_keys` is the module's argument keys minus `name`, mirroring
how Terraform's block label is kept separate from its body's config keys.

Spec: topology.md — shared iac format, parsed by IaCAdapter, not here.
"""
from __future__ import annotations

from _base import Detector, NormalizedResource

# Task-level directives that are not a module invocation, so a task dict's
# module key is whichever remaining key holds a dict of arguments.
_TASK_META_KEYS = frozenset({
    'name', 'when', 'tags', 'register', 'become', 'become_user', 'loop',
    'with_items', 'with_dict', 'notify', 'ignore_errors', 'vars', 'delegate_to',
    'run_once', 'changed_when', 'failed_when', 'until', 'retries', 'delay',
    'no_log', 'check_mode', 'environment',
})
_NESTED_TASK_LIST_KEYS = ('tasks', 'pre_tasks', 'post_tasks', 'handlers', 'block', 'rescue', 'always')


class AnsibleDetector(Detector):
    """
    Framework detector for Ansible (iac).
    Receives pre-discovered .yml/.yaml files from IaCAdapter. Must not perform file discovery.
    """

    def extract(self, files: list[str]) -> list[NormalizedResource]:
        resources: list[NormalizedResource] = []
        for fpath in files:
            if fpath.endswith(('.yml', '.yaml')):
                resources.extend(self._parse_file(fpath))
        return resources

    def _parse_file(self, fpath: str) -> list[NormalizedResource]:
        import yaml  # lazy import — not a hard dependency of the base SDK

        try:
            with open(fpath, encoding='utf-8') as f:
                docs = list(yaml.safe_load_all(f))
        except (OSError, yaml.YAMLError):
            return []

        resources: list[NormalizedResource] = []
        for doc in docs:
            if not isinstance(doc, list):
                continue
            for task in self._iter_tasks(doc):
                resource = self._resource_from_task(task)
                if resource is not None:
                    resources.append(resource)
        return resources

    def _iter_tasks(self, task_list):
        for item in task_list:
            if not isinstance(item, dict):
                continue
            if self._module_key(item) is not None:
                yield item
            for nested_key in _NESTED_TASK_LIST_KEYS:
                nested = item.get(nested_key)
                if isinstance(nested, list):
                    yield from self._iter_tasks(nested)

    @staticmethod
    def _module_key(task: dict) -> str | None:
        """The one task key that's a module invocation (dict-valued, not a
        directive like `when`/`tags`/`vars`), or None if the task is only a
        container for a nested task list (e.g. a play with just `tasks:`)."""
        candidates = [
            k for k, v in task.items()
            if k not in _TASK_META_KEYS and k not in _NESTED_TASK_LIST_KEYS and isinstance(v, dict)
        ]
        return candidates[0] if len(candidates) == 1 else None

    def _resource_from_task(self, task: dict) -> NormalizedResource | None:
        module_key = self._module_key(task)
        args = task.get(module_key) or {}
        if not isinstance(args, dict):
            return None

        name = args.get('name') or task.get('name')
        if not name:
            return None

        config_keys = [k for k in args if k != 'name']
        return NormalizedResource(name=str(name), resource_type=module_key, config_keys=config_keys)


if __name__ == '__main__':
    import tempfile
    from pathlib import Path

    src = '''
- name: Configure infrastructure
  hosts: localhost
  tasks:
    - name: Create data bucket
      amazon.aws.s3_bucket:
        name: my-data-bucket
        region: us-east-1
        state: present
        tags:
          Environment: production

    - name: Launch web server
      amazon.aws.ec2_instance:
        name: web-server-1
        instance_type: t3.micro
        image_id: ami-12345
        state: running
      when: deploy_web

  handlers:
    - name: restart nginx
      ansible.builtin.service:
        name: nginx
        state: restarted
'''

    with tempfile.NamedTemporaryFile(suffix=".yml", mode="w", delete=False, encoding="utf-8") as f:
        f.write(src)
        path = f.name

    try:
        detector = AnsibleDetector()
        assert detector.extract([]) == [], "extract([]) must return an empty list"

        resources = detector.extract([path])
        by_name = {r.name: r for r in resources}

        assert "my-data-bucket" in by_name, resources
        assert by_name["my-data-bucket"].resource_type == "amazon.aws.s3_bucket"
        assert set(by_name["my-data-bucket"].config_keys) == {"region", "state", "tags"}

        assert "web-server-1" in by_name, resources          # task's own `when:` must not confuse module detection
        assert by_name["web-server-1"].resource_type == "amazon.aws.ec2_instance"

        assert "nginx" in by_name, resources                 # handlers: nested list must also be scanned
        assert by_name["nginx"].resource_type == "ansible.builtin.service"

        assert len(resources) == 3
    finally:
        Path(path).unlink()

    print("[OK] ansible.py self-test passed")
