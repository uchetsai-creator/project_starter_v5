#!/usr/bin/env python3
"""SessionStart helper (Claude Code only — invoked by session-start-hook.sh): compares
.project-starter.yml's framework_commit against project_starter_v5's current upstream
HEAD via `git ls-remote`, and prints one line of additionalContext text on stdout if the
two differ.

Opt-in and always silent on failure or when nothing is configured: prints nothing (and
this always exits 0) when framework_commit is blank/absent, when git or the network
aren't available, or when the ls-remote call times out -- same "non-blocking nudge, not
a gate" contract as every other check in session-start-hook.sh. Never touches the local
project's own git repo, only the configured upstream URL.

When a diff is found, this also makes a best-effort attempt to classify it: if
document-registry.yaml's top-level document keys at the old commit are missing at the new
one, that's a structural change (a document renamed or split -- see retrofit.md's "Update
recheck" step 3) and gets a different, more specific nudge than a plain additive update.
This classification is pure enrichment -- any failure in fetching or parsing the two
revisions (private repo, server without SHA1-in-want, non-YAML content, etc.) just falls
back to the original generic nudge, same silent-on-failure contract as the rest of this file.
"""
from __future__ import annotations

import os
import re
import subprocess
import tempfile

import yaml

DEFAULT_REPO_URL = "https://github.com/uchetsai-creator/project_starter_v5.git"
CONFIG_PATH = ".project-starter.yml"
REGISTRY_PATH = "document-registry.yaml"
TIMEOUT_SECONDS = 4


def _read_field(config_text: str, key: str) -> str:
    match = re.search(rf"^{re.escape(key)}:[ \t]*(\S+)", config_text, re.MULTILINE)
    return match.group(1) if match else ""


def _remote_head(repo_url: str) -> str:
    env = dict(os.environ)
    env["GIT_TERMINAL_PROMPT"] = "0"  # never hang on an auth prompt for a private/unreachable fork
    result = subprocess.run(
        ["git", "ls-remote", repo_url, "HEAD"],
        capture_output=True, text=True, timeout=TIMEOUT_SECONDS, env=env,
    )
    if result.returncode != 0 or not result.stdout.strip():
        return ""
    return result.stdout.split()[0]


def _file_at_commit(repo_url: str, commit: str, path: str) -> str | None:
    """Best-effort shallow fetch of a single commit into a throwaway bare repo, returning
    `path` as it existed there, or None on any failure (never required for the base nudge)."""
    env = dict(os.environ)
    env["GIT_TERMINAL_PROMPT"] = "0"
    try:
        with tempfile.TemporaryDirectory() as tmp:
            subprocess.run(
                ["git", "init", "-q", "--bare", tmp],
                capture_output=True, timeout=TIMEOUT_SECONDS, env=env, check=True,
            )
            subprocess.run(
                ["git", "fetch", "-q", "--depth", "1", repo_url, commit],
                cwd=tmp, capture_output=True, timeout=TIMEOUT_SECONDS, env=env, check=True,
            )
            result = subprocess.run(
                ["git", "show", f"FETCH_HEAD:{path}"],
                cwd=tmp, capture_output=True, text=True, timeout=TIMEOUT_SECONDS, env=env, check=True,
            )
            return result.stdout
    except (OSError, subprocess.SubprocessError):
        return None


def _document_keys(yaml_text: str) -> set[str] | None:
    try:
        data = yaml.safe_load(yaml_text)
    except yaml.YAMLError:
        return None
    documents = data.get("documents") if isinstance(data, dict) else None
    if not isinstance(documents, dict):
        return None
    return set(documents.keys())


def _removed_document_keys(repo_url: str, old_commit: str, new_commit: str) -> set[str]:
    old_text = _file_at_commit(repo_url, old_commit, REGISTRY_PATH)
    new_text = _file_at_commit(repo_url, new_commit, REGISTRY_PATH)
    if old_text is None or new_text is None:
        return set()
    old_keys = _document_keys(old_text)
    new_keys = _document_keys(new_text)
    if old_keys is None or new_keys is None:
        return set()
    return old_keys - new_keys


def main() -> None:
    try:
        with open(CONFIG_PATH, encoding="utf-8") as f:
            config_text = f.read()
    except OSError:
        return

    local_commit = _read_field(config_text, "framework_commit")
    if not local_commit:
        return  # not opted in -- nothing recorded to compare against

    repo_url = _read_field(config_text, "framework_repo_url") or DEFAULT_REPO_URL

    try:
        remote_commit = _remote_head(repo_url)
    except (OSError, subprocess.SubprocessError):
        return

    if not remote_commit or remote_commit == local_commit:
        return

    removed_keys = _removed_document_keys(repo_url, local_commit, remote_commit)
    if removed_keys:
        print(
            "project_starter_v5 (the framework this project was scaffolded from) has a "
            "STRUCTURAL update upstream -- document-registry.yaml dropped or renamed the "
            f"document key(s) {sorted(removed_keys)} between local framework_commit "
            f"{local_commit[:12]} and upstream HEAD {remote_commit[:12]}. This usually means "
            "a document was renamed or split into new files, not deleted outright -- do not "
            "delete the corresponding local file without migrating its content first. Ask "
            "the user with AskUserQuestion whether they want to pull the latest "
            "project_starter_v5 and run the retrofit-existing-project Skill's update-recheck "
            "section, which covers migrating a renamed/split document key. If they decline, "
            "do nothing further this session -- this same nudge repeats next session until "
            "framework_commit in .project-starter.yml is updated to the new upstream SHA."
        )
        return

    print(
        "project_starter_v5 (the framework this project was scaffolded from) has updates "
        f"upstream -- local framework_commit is {local_commit[:12]}, upstream HEAD is now "
        f"{remote_commit[:12]}. Ask the user with AskUserQuestion whether they want to pull "
        "the latest project_starter_v5 and use it to re-check this project (the "
        "retrofit-existing-project Skill's update-recheck section covers how). If they "
        "decline, do nothing further this session -- this same nudge repeats next session "
        "until framework_commit in .project-starter.yml is updated to the new upstream SHA "
        "(done as part of that recheck, or by hand to silence it without recheck)."
    )


if __name__ == "__main__":
    main()
