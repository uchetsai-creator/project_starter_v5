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
#
# Also asks (via injected additionalContext) whether to turn on
# pretooluse_scope_guard.py's mechanical enforcement for *this* session, but only when
# .project-starter.yml sets checkpoint_enforcement: session-prompt — see that file's
# comment and pretooluse_scope_guard.py's docstring for the full opt-in design. Silent
# no-op (same as before this existed) when that key is unset, matching every other
# optional gate in this framework.

CS="docs/current-state.md"
RESEARCH="docs/specs/research.md"
MSG=""

HOOK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SESSION_ID=""
if command -v python3 &>/dev/null; then
    SESSION_ID=$(python3 -c "
import json, sys
try:
    print(json.load(sys.stdin).get('session_id', ''))
except Exception:
    print('')
" 2>/dev/null)
fi

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

    # ── Spec drift since last touch ─────────────────────────────────────────
    # Trigger: a real (non-placeholder) Current Task, with specific files listed
    # under Required Context. Compares each listed file's last commit timestamp
    # against current-state.md's own last commit timestamp -- no content diffing,
    # no judgment call about whether the change actually matters, purely "did this
    # move more recently than I last touched my own task file." Same mechanism as
    # learning_log_nudge.py (task-log.md vs learning-log.md commit timestamps).
    # This is the closest this framework gets to Spec Kit's "plan/tasks regenerate
    # when the spec changes" -- deliberately a nudge, not an auto-rewrite: silently
    # regenerating someone's Steps would mean discarding manual planning content
    # without asking, which no gate anywhere in this framework does.
    if [ -n "$TASK_LINE" ] && ! echo "$TASK_LINE" | grep -qE '\['; then
        CS_COMMIT_TS=$(git log -1 --format=%ct -- "$CS" 2>/dev/null)
        if [ -n "$CS_COMMIT_TS" ]; then
            REQUIRED_CONTEXT_SECTION=$(awk '/^## Required Context/{p=1; next} /^## /{p=0} p' "$CS" 2>/dev/null)
            STALE_FILES=""
            while IFS= read -r line; do
                PATH_CANDIDATE=$(printf '%s' "$line" | sed -n 's/^\* `\(.*\)`$/\1/p')
                [ -z "$PATH_CANDIDATE" ] && continue
                case "$PATH_CANDIDATE" in
                    *\[*) continue ;;  # still the template placeholder, not a real path
                esac
                [ -f "$PATH_CANDIDATE" ] || continue
                DOC_COMMIT_TS=$(git log -1 --format=%ct -- "$PATH_CANDIDATE" 2>/dev/null)
                if [ -n "$DOC_COMMIT_TS" ] && [ "$DOC_COMMIT_TS" -gt "$CS_COMMIT_TS" ]; then
                    STALE_FILES="${STALE_FILES}${PATH_CANDIDATE}, "
                fi
            done <<< "$REQUIRED_CONTEXT_SECTION"
            if [ -n "$STALE_FILES" ]; then
                STALE_FILES="${STALE_FILES%, }"
                SPEC_DRIFT_MSG="Required Context file(s) changed more recently than current-state.md itself: ${STALE_FILES}. The Steps here may have been planned against an older version of the spec -- worth re-reading before continuing."
                MSG="${MSG:+$MSG }$SPEC_DRIFT_MSG"
            fi
        fi
    fi
fi

# ── Learning Checkpoint enforcement prompt (opt-in) ─────────────────────────
# Only fires when .project-starter.yml sets checkpoint_enforcement: session-prompt
# AND this session hasn't already answered (checked via checkpoint_session_state.py,
# keyed by session_id) -- see pretooluse_scope_guard.py for the other half.
CFG=".project-starter.yml"
if [ -f "$CFG" ] \
    && grep -qE '^checkpoint_enforcement:[[:space:]]*session-prompt[[:space:]]*$' "$CFG" \
    && [ -n "$SESSION_ID" ] && command -v python3 &>/dev/null; then
    ANSWERED=$(SESSION_ID="$SESSION_ID" HOOK_DIR="$HOOK_DIR" python3 -c "
import os, sys
sys.path.insert(0, os.environ['HOOK_DIR'])
import checkpoint_session_state as s
choice = s.read_choice(os.environ['SESSION_ID'], '.')
print('' if choice is None else ('true' if choice else 'false'))
" 2>/dev/null)
    if [ -z "$ANSWERED" ]; then
        CHECKPOINT_MSG="This project has checkpoint_enforcement: session-prompt set in .project-starter.yml. This session (session_id: $SESSION_ID) has not yet chosen whether to enable Learning Checkpoint enforcement. Before doing any other work, ask the user with AskUserQuestion: 要不要在這個 session 啟用 learning-checkpoint 的強制機制？啟用後，修改程式碼前必須先在 docs/current-state.md 填好 Task 和 Clarifying Questions Asked 欄位，否則會被 PreToolUse hook 擋下；不啟用的話，仍要照 learning-checkpoint Skill 的 Checkpoint A/B 問題模板，用對話方式先問過再動手，只是不會被機制擋下。 Then record the answer by running: python3 adapters/claude/record_checkpoint_choice.py --session-id $SESSION_ID --enabled true (or --enabled false)."
        MSG="${MSG:+$MSG }$CHECKPOINT_MSG"
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
