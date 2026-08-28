#!/usr/bin/env python3
"""PreToolUse hook: blocks Edit / Write / MultiEdit / NotebookEdit on source-like files
until docs/current-state.md has a real, scoped Current Task with Clarifying Questions
Asked filled in (Y or N/A).

This is the mechanical counterpart to .githooks/pre-commit's "Unscoped source-change
guard": that one catches an unscoped implementation at commit time (after the fact);
this one catches it at write time, before the agent produces any code at all -- the
only point in the pipeline that can actually make an agent ask first instead of just
recording, after the fact, whether it did. See AGENTS.md -> New requirement from the
user for the rule this enforces, and README.md -> Agent Adapters for how PreToolUse
hooks are wired into .claude/settings.json.

Install: add to .claude/settings.json:
  { "hooks": { "PreToolUse": [{ "matcher": "Edit|Write|MultiEdit|NotebookEdit",
      "hooks": [{ "type": "command",
                  "command": "python3 adapters/claude/pretooluse_scope_guard.py" }] }] } }

Fail-open by design: any parse error, missing/placeholder .project-starter.yml, or
unrecognized tool_name results in "allow" -- this hook must never be the reason a
session breaks, matching every other optional gate in this framework (spec_code_adapter,
security_scan_src, prose_scan_enabled all no-op cleanly when unset).

Default behavior (checkpoint_enforcement unset in .project-starter.yml): always enforces,
exactly as above -- no prompt, no opt-out, matches every version of this file before this
option existed. Two opt-in variants of that default, set via .project-starter.yml's
checkpoint_enforcement key:
  - `session-prompt`: only enforces once the *current Claude Code session* has explicitly
    chosen to turn this on -- session-start-hook.sh asks once per session (a session that
    hasn't answered yet fails open, same as `off`) and adapters/claude/
    record_checkpoint_choice.py records the answer, keyed to that session's session_id, in
    logs/telemetry/checkpoint-session-choices.json. See checkpoint_session_state.py.
  - `off`: always allows -- a killswitch that doesn't require touching .claude/settings.json.
"""
from __future__ import annotations

import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import checkpoint_session_state as _cps  # noqa: E402

GATED_TOOLS = {"Edit", "Write", "MultiEdit", "NotebookEdit"}

# Kept in sync BY HAND with .githooks/pre-commit's NON_SOURCE_REGEX -- same list of
# paths that are docs/framework/config rather than application source, so a file that
# would be excluded from the commit-time gate is also excluded here.
NON_SOURCE_PREFIXES = (
    "guidance/", ".githooks/", ".claude/", ".codex/", "adapters/", "logs/", ".ai/",
)
NON_SOURCE_NAMES = {
    "AGENTS.md", "CLAUDE.md", "orchestrator.py", "build-context.py",
    "_workflow_utils.py", "workflow-registry.yaml", "document-registry.yaml",
    "detect_type.py", "debug-instrumentation-rules.md", "code-quality-check.md",
    "learning-log.md",
    ".project-starter.yml", "README.md", "LICENSE", ".gitignore",
    ".pre-commit-config.yaml",
}


def _emit(decision: str, reason: str) -> None:
    print(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": decision,
            "permissionDecisionReason": reason,
        },
    }))


def _allow(reason: str = "") -> None:
    _emit("allow", reason)


def _deny(reason: str) -> None:
    _emit("deny", reason)


def _read_config_value(path: str, key: str) -> str:
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                if line.startswith(f"{key}:"):
                    return line.split(":", 1)[1].strip().strip("\"'")
    except OSError:
        pass
    return ""


def _is_source_path(rel_path: str, docs_path: str) -> bool:
    rel_path = rel_path.replace("\\", "/").lstrip("./")
    docs_prefix = docs_path.strip("/") + "/"
    if rel_path.startswith(docs_prefix):
        return False
    if any(rel_path.startswith(p) for p in NON_SOURCE_PREFIXES):
        return False
    if rel_path in NON_SOURCE_NAMES:
        return False
    return True


def _cqa_is_valid(value: str) -> bool:
    return bool(re.match(r"(?i)^(Y|N/A)([^a-z]|$)", value.strip()))


def decide(payload: dict, cwd: str) -> tuple[str, str]:
    """Pure decision function, separated from stdin/stdout plumbing so it's unit
    testable without spawning a subprocess for every case."""
    tool_name = payload.get("tool_name", "")
    if tool_name not in GATED_TOOLS:
        return "allow", f"tool {tool_name!r} not gated"

    tool_input = payload.get("tool_input") or {}
    file_path = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
    if not file_path:
        return "allow", "no file_path in tool_input"

    config_path = os.path.join(cwd, ".project-starter.yml")
    project_type = _read_config_value(config_path, "project_type")
    if not project_type or re.match(r"^\[.+\]$", project_type):
        return "allow", "project_type unset or still a placeholder -- not initialized yet"

    enforcement_mode = _read_config_value(config_path, "checkpoint_enforcement").strip().lower()
    if enforcement_mode == "off":
        return "allow", "checkpoint_enforcement: off -- guard disabled via .project-starter.yml"
    if enforcement_mode == "session-prompt":
        session_id = payload.get("session_id", "")
        choice = _cps.read_choice(session_id, cwd)
        if choice is None:
            return "allow", (
                "checkpoint_enforcement: session-prompt -- this session has not chosen "
                "yet whether to enable enforcement, failing open (see SessionStart nudge "
                "and adapters/claude/record_checkpoint_choice.py)"
            )
        if choice is False:
            return "allow", (
                "checkpoint_enforcement: session-prompt -- user opted out of mechanical "
                "enforcement for this session (Checkpoint A/B still apply conversationally)"
            )
        # choice is True -> fall through to the scoping check below, same as the
        # always-on default.

    docs_path = _read_config_value(config_path, "docs_path") or "docs/"
    docs_path = docs_path.strip("/") or "docs"

    rel_path = os.path.relpath(file_path, cwd) if os.path.isabs(file_path) else file_path
    if not _is_source_path(rel_path, docs_path):
        return "allow", "not a source-like path"

    cs_path = os.path.join(cwd, docs_path, "current-state.md")
    try:
        with open(cs_path, encoding="utf-8") as f:
            cs_content = f.read()
    except OSError:
        return "deny", (
            f"{docs_path}/current-state.md does not exist yet, but this would write to "
            f"a source file ({rel_path}). Per AGENTS.md -> New requirement from the "
            "user: ask scope/edge-case/acceptance-criteria questions first, then set "
            "Current Task and Clarifying Questions Asked before implementing."
        )

    task_match = re.search(r"^\*\*Task:\*\*\s*(.*)$", cs_content, re.MULTILINE)
    task_value = task_match.group(1).strip() if task_match else ""
    if not task_value or re.match(r"^\[.*\]$", task_value):
        return "deny", (
            f"{docs_path}/current-state.md has no scoped Current Task yet, but this "
            f"would write to a source file ({rel_path}). Ask scope/edge-case/"
            "acceptance-criteria questions first -- see AGENTS.md -> New requirement "
            "from the user -- then set Current Task before implementing."
        )

    cqa_match = re.search(r"^\*\*Clarifying Questions Asked:\*\*\s*(.*)$", cs_content, re.MULTILINE)
    cqa_value = cqa_match.group(1).strip() if cqa_match else ""
    if not _cqa_is_valid(cqa_value):
        return "deny", (
            f"{docs_path}/current-state.md's Current Task is set but Clarifying "
            f"Questions Asked is not Y or N/A yet, and this would write to a source "
            f"file ({rel_path}). Confirm scope with the user, then set that field "
            "before implementing -- see AGENTS.md -> New requirement from the user."
        )

    return "allow", "current-state.md is scoped"


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, OSError):
        _allow("could not parse hook payload")
        return

    cwd = payload.get("cwd") or os.getcwd()
    try:
        decision, reason = decide(payload, cwd)
    except Exception as exc:  # fail-open: never break the session over this gate
        _allow(f"internal error, failing open: {exc}")
        return
    _emit(decision, reason)


if __name__ == "__main__":
    main()
