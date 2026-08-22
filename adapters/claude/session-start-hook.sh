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
RESEARCH="docs/specs/research.md"
MSG=""

# A **Decision:** line whose value isn't the template's own bracketed placeholder
# (e.g. "[Final choice, e.g., AWS SQS]") counts as real content. Deliberately looser
# than verify_content.py's check_research() (which also requires a real Rationale
# entry) — this is a non-blocking nudge, not the commit-time gate, so a slightly
# looser approximation is an acceptable tradeoff for staying simple in bash.
RESEARCH_HAS_REAL_DECISION=false
if [ -f "$RESEARCH" ]; then
    while IFS= read -r line; do
        value=$(printf '%s' "$line" | sed 's/^\*\*Decision:\*\*[[:space:]]*//')
        if [ -n "$value" ] && ! printf '%s' "$value" | grep -qE '^\['; then
            RESEARCH_HAS_REAL_DECISION=true
            break
        fi
    done < <(grep -E '^\*\*Decision:\*\*' "$RESEARCH" 2>/dev/null)
fi

if [ -f "$CS" ]; then
    TASK_LINE=$(grep -E '^\*\*Task:\*\*' "$CS" 2>/dev/null | head -1)
    if echo "$TASK_LINE" | grep -qE '\['; then
        MSG="docs/current-state.md has no scoped Current Task yet (still the template placeholder). Before implementing a new requirement, ask scope / edge cases / acceptance criteria first -- see AGENTS.md -> Constitution -> Unscoped New Requirement, and New requirement from the user below it."
        # No scoped task AND no recorded technology decision yet -- both signals together
        # (not either alone) are what mark this as a brand-new, undiscussed project; a
        # task-in-progress project with an already-empty research.md doesn't need this
        # extra nudge every session, only the very first one does.
        if [ "$RESEARCH_HAS_REAL_DECISION" = false ] && [ -f "$RESEARCH" ]; then
            MSG="$MSG This also looks like a brand-new project -- docs/specs/research.md has no recorded technology decisions yet either. Before writing code, discuss key technology decisions (framework, database, infra, etc.) with the user and record them in docs/specs/research.md -- see the research-decision-log Skill."
        fi
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
