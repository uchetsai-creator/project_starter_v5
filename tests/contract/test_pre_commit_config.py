"""Contract tests for .pre-commit-config.yaml — the optional pre-commit-framework
entry point (see the file's own header comment for why it wraps .githooks/pre-commit
as a single local hook instead of reimplementing its checks).

Does not require the `pre-commit` package or network access — those were used to
verify this file manually (both a passing and a blocking run through the real
pre-commit CLI); these tests just guard the static structure from silently drifting
out of sync with .githooks/pre-commit's actual location.
"""
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent.parent
_CONFIG_PATH = _REPO_ROOT / ".pre-commit-config.yaml"


def _load_config() -> dict:
    return yaml.safe_load(_CONFIG_PATH.read_text(encoding="utf-8"))


def test_file_exists_and_is_valid_yaml():
    assert _CONFIG_PATH.exists()
    config = _load_config()
    assert isinstance(config.get("repos"), list)
    assert len(config["repos"]) >= 1


def test_local_hook_wraps_the_real_pre_commit_script():
    config = _load_config()
    local_repos = [r for r in config["repos"] if r.get("repo") == "local"]
    assert len(local_repos) == 1

    hooks = local_repos[0]["hooks"]
    assert len(hooks) == 1
    hook = hooks[0]

    assert hook["entry"] == "bash .githooks/pre-commit"
    assert hook["language"] == "system"
    assert hook.get("pass_filenames") is False
    assert hook.get("always_run") is True

    # The entry references a script that must actually exist in this repo.
    assert (_REPO_ROOT / ".githooks" / "pre-commit").exists()


def test_no_duplicate_hook_ids():
    config = _load_config()
    ids = []
    for repo in config["repos"]:
        for hook in repo.get("hooks", []):
            if "id" in hook:
                ids.append(hook["id"])
    assert len(ids) == len(set(ids)), f"duplicate hook ids: {ids}"
