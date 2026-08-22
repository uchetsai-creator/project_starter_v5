#!/usr/bin/env bash
# Optional Claude Code fast-feedback script (Phase 20).
# Called by .claude/settings.json Stop hook after every Claude session.
# Writes verify output to logs/ as a valid JSON array — non-blocking (always exits 0).

mkdir -p logs
STAMP=$(date +%Y%m%d-%H%M%S)
if [ ! -f .project-starter.yml ] || [ ! -f docs/script/validators/verify_docs.py ]; then
    echo '{"skipped": true, "reason": "project not initialised — .project-starter.yml or validators not found"}' \
        > "logs/verify-${STAMP}.json" 2>/dev/null || true
    exit 0
fi
TYPE=$(grep '^project_type:' .project-starter.yml | sed 's/project_type:[[:space:]]*//' | tr -d "\"'")
if [ -z "$TYPE" ]; then
    echo '{"skipped": true, "reason": "project_type not set in .project-starter.yml"}' \
        > "logs/verify-${STAMP}.json" 2>/dev/null || true
    exit 0
fi

# Each validator is invoked with --json and captured separately, then wrapped
# in a top-level JSON array so the output file is always valid JSON.
run_validator() {
    local script="$1"; shift
    if [ -f "$script" ]; then
        python3 "$script" "$@" --json 2>/dev/null || echo "null"
    fi
}

{
    printf '[\n'
    DOCS_OUT=$(run_validator docs/script/validators/verify_docs.py    --project-type "$TYPE" --content)
    LOGS_OUT=$(run_validator docs/script/validators/verify_logs.py    --project-type "$TYPE")
    TESTS_OUT=$(run_validator docs/script/validators/verify_tests.py  --project-type "$TYPE")
    CONT_OUT=$(run_validator docs/script/validators/verify_content.py --project-type "$TYPE")
    printf '%s,\n' "$DOCS_OUT"
    printf '%s,\n' "$LOGS_OUT"
    printf '%s,\n' "$TESTS_OUT"
    printf '%s\n'  "$CONT_OUT"
    printf ']\n'
} > "logs/verify-${STAMP}.json" 2>/dev/null || true

# ── Real-time gate checks (no git commit dependency) ───────────────────────
# project_type_confirmed / Clarifying Questions Asked / Doc Checklist completeness /
# Sprint Documentation Sync are also enforced by .githooks/pre-commit, but ONLY at
# `git commit` — a workflow that pulls once, does a long stretch of local work, then
# pushes/merges once at the end may go a very long time without committing, so those
# gates would barely ever run. This ports the same checks to read the working tree
# directly (no staged-file concept needed, since there's no commit to inspect) so they
# surface on every Stop event instead. Non-blocking by design (Stop hooks can't
# block), using the same hookSpecificOutput.additionalContext mechanism
# session-start-hook.sh already uses (Stop hooks support the identical schema — see
# https://code.claude.com/docs/en/hooks).
CONFIG=".project-starter.yml"
ISSUES=()

if [ -f "$CONFIG" ]; then
    DOCS_CANDIDATE=$(grep '^docs_path:' "$CONFIG" | sed 's/docs_path:[[:space:]]*//' | tr -d "\"' /")
    DOCS_PATH="${DOCS_CANDIDATE:-docs}"

    if grep -qE '^project_type_confirmed:[[:space:]]*false' "$CONFIG"; then
        ISSUES+=("project_type_confirmed: false in $CONFIG -- detect_type.py's guess hasn't been confirmed yet. Confirm the detected project_type is correct, then set project_type_confirmed: true (or remove the line).")
    fi

    CS_PATH="${DOCS_PATH}/current-state.md"
    if [ -f "$CS_PATH" ]; then
        CS_CONTENT=$(cat "$CS_PATH")

        CS_TASK=$(printf '%s\n' "$CS_CONTENT" | grep -E '^\*\*Task:\*\*' | head -1 || true)
        if [ -n "$CS_TASK" ] && ! printf '%s\n' "$CS_TASK" | grep -qE '\['; then
            CS_CQA=$(printf '%s\n' "$CS_CONTENT" | grep -E '^\*\*Clarifying Questions Asked:\*\*' | head -1 || true)
            CQA_VALUE=$(printf '%s' "$CS_CQA" | sed 's/^\*\*Clarifying Questions Asked:\*\*[[:space:]]*//')
            if [ -z "$CS_CQA" ] || printf '%s\n' "$CS_CQA" | grep -qE '\[' \
                || ! printf '%s' "$CQA_VALUE" | grep -qiE '^(Y|N/A)([^A-Za-z]|$)'; then
                ISSUES+=("$CS_PATH has a real Current Task but Clarifying Questions Asked is missing, still a placeholder, or not Y/N/A. Set it to Y or N/A -- see AGENTS.md -> New requirement from the user.")
            fi
        fi

        CS_STATUS=$(printf '%s\n' "$CS_CONTENT" | grep -iE '^\*\*Status:\*\*' | head -1 || true)
        if printf '%s\n' "$CS_STATUS" | grep -qi 'Complete'; then
            DOC_CHECKLIST_SECTION=$(printf '%s\n' "$CS_CONTENT" | awk '/^## Doc Checklist/{p=1} /^## Closeout/{p=0} p{print}')
            if printf '%s\n' "$DOC_CHECKLIST_SECTION" | grep -qE '^- \[ \]|\[relevant spec\]'; then
                ISSUES+=("$CS_PATH Status is Complete but Doc Checklist has an unchecked item (- [ ]) or the unfilled template placeholder (\`[relevant spec]\`). Apply each item and check it off (- [x]) -- see AGENTS.md -> Closing out a task.")
            fi
        fi
    fi

    # Sprint Documentation Sync -- also enforced by .githooks/pre-commit (blocking,
    # working-tree state, same >= 3 threshold), mirrored here as an early warning for
    # the same reason as the three checks above: a long stretch without a commit means
    # this would otherwise stay invisible until the next commit finally happens.
    SPRINT_LOG="${DOCS_PATH}/sprint-change-log.md"
    if [ -f "$SPRINT_LOG" ]; then
        PENDING_COUNT=$(grep -cE '^\*\*Status:\*\* Pending documentation synchronization' "$SPRINT_LOG" || true)
        PENDING_COUNT=${PENDING_COUNT:-0}
        if [ "$PENDING_COUNT" -ge 3 ]; then
            ISSUES+=("$SPRINT_LOG has $PENDING_COUNT entries at 'Pending documentation synchronization' (threshold: 3). Run Sprint Documentation Sync (templates/sprint-sync.md) -- see AGENTS.md -> Sprint Documentation Sync.")
        fi
    fi
fi

if [ "${#ISSUES[@]}" -gt 0 ] && command -v python3 &>/dev/null; then
    ISSUES_TEXT=$(printf -- '- %s\n' "${ISSUES[@]}")
    python3 -c "
import json, sys
print(json.dumps({
    'hookSpecificOutput': {
        'hookEventName': 'Stop',
        'additionalContext': (
            'project_starter_v5: the following are normally caught by .githooks/pre-commit at '
            'git commit, surfaced here instead since these only fire at commit time:\n'
            + sys.argv[1]
        ),
    },
}))
" "$ISSUES_TEXT" 2>/dev/null
fi
