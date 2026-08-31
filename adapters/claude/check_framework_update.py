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
"""
from __future__ import annotations

import os
import re
import subprocess

DEFAULT_REPO_URL = "https://github.com/uchetsai-creator/project_starter_v5.git"
CONFIG_PATH = ".project-starter.yml"
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
