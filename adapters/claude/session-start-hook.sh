#!/usr/bin/env bash
# Non-blocking SessionStart nudge (Claude Code only — see adapters/claude/README context).
#
# Why this exists: AGENTS.md's "New requirement from the user" rule / Constitution's
# "Unscoped New Requirement" item only work if the agent actually reads that part of
# AGENTS.md fresh each session. CLAUDE.md's `@AGENTS.md` auto-load is not guaranteed to
# put that specific section in front-of-mind every time (a long AGENTS.md, a session that
# jumps straight into a task) — this hook re-surfaces the one fact that matters (is the
# current task actually scoped, was Checkpoint B done) at the moment a session starts,
# instead of depending on it having been read and retained.
#
# Never blocks: always exits 0, even on any internal failure. This is a reminder, not a
# gate — the actual gate is the Clarifying Questions Asked check in .githooks/pre-commit.

CS="docs/current-state.md"
MSG=""

if [ -f "$CS" ]; then
    TASK_LINE=$(grep -E '^\*\*Task:\*\*' "$CS" 2>/dev/null | head -1)
    if echo "$TASK_LINE" | grep -qE '\['; then
        MSG="docs/current-state.md has no scoped Current Task yet (still the template placeholder). Before implementing a new requirement, ask scope / edge cases / acceptance criteria first -- see AGENTS.md -> Constitution -> Unscoped New Requirement, and New requirement from the user below it."
    elif [ -n "$TASK_LINE" ]; then
        CQA_LINE=$(grep -E '^\*\*Clarifying Questions Asked:\*\*' "$CS" 2>/dev/null | head -1)
        if [ -z "$CQA_LINE" ] || echo "$CQA_LINE" | grep -qE '\['; then
            MSG="docs/current-state.md has a real Current Task but Clarifying Questions Asked is unfilled -- set it to Y (asked before implementing) or N/A (pre-scoped task / Checkpoint A applied) once confirmed. pre-commit blocks the commit until this is set."
        fi
    fi
fi

if [ -n "$MSG" ] && command -v python3 &>/dev/null; then
    python3 -c "
import json, sys
print(json.dumps({
    'hookSpecificOutput': {
        'hookEventName': 'SessionStart',
        'additionalContext': sys.argv[1],
    },
}))
" "$MSG" 2>/dev/null
fi

exit 0
