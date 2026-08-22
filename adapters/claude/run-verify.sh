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
# Sprint Documentation Sync / verify_docs+logs+tests+content --strict failures are
# also enforced by .githooks/pre-commit, but ONLY at `git commit` — a workflow that
# pulls once, does a long stretch of local work, then pushes/merges once at the end
# may go a very long time without committing, so those gates would barely ever run.
# This surfaces the same checks on every Stop event instead: the first four read the
# working tree directly (no staged-file concept needed, since there's no commit to
# inspect); the validator failures reuse the --json output already captured above for
# logs/verify-*.json, since --strict only changes the exit code, never the JSON
# content. Non-blocking by design (Stop hooks can't block), using the same
# hookSpecificOutput.additionalContext mechanism session-start-hook.sh already uses
# (Stop hooks support the identical schema — see https://code.claude.com/docs/en/hooks).
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

# ── Validator failures (--strict, without re-running anything) ─────────────
# verify_docs/logs/tests/content already ran with --json above to build
# logs/verify-*.json -- --strict only ever changes the exit code, never the JSON
# content (confirmed by reading each validator's main()), so the JSON already
# captured is enough to compute the same pass/fail --strict would. Previously this
# JSON was written to a log file nobody reads proactively; parsing the failures out
# here and adding them to the same nudge as the four checks above costs nothing extra
# to run, only the parsing itself.
if command -v python3 &>/dev/null; then
    VALIDATOR_ISSUES=$(python3 -c "
import json, sys

def docs_failures(raw):
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return []
    return [r['doc'] for r in data.get('results', []) if r.get('status') == 'missing_required']

def check_failures(raw):
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return []
    return [r['check'] for r in data.get('results', []) if r.get('status') == 'fail']

def content_failures(raw):
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return []
    failed = [d['name'] for d in data.get('documents', [])
              if not d.get('present') or d.get('quality') == 'fail']
    failed += [m['name'] for m in data.get('modules', [])
               if not m.get('flow_file_present') or m.get('quality') == 'fail']
    return failed

for label, extractor, raw in (
    ('verify_docs.py', docs_failures, sys.argv[1]),
    ('verify_logs.py', check_failures, sys.argv[2]),
    ('verify_tests.py', check_failures, sys.argv[3]),
    ('verify_content.py', content_failures, sys.argv[4]),
):
    failed = extractor(raw)
    if not failed:
        continue
    shown = ', '.join(failed[:5])
    if len(failed) > 5:
        shown += f' (+{len(failed) - 5} more)'
    print(f'{label} would fail --strict: {shown}')
" "$DOCS_OUT" "$LOGS_OUT" "$TESTS_OUT" "$CONT_OUT" 2>/dev/null)
    if [ -n "$VALIDATOR_ISSUES" ]; then
        while IFS= read -r line; do
            [ -n "$line" ] && ISSUES+=("$line")
        done <<< "$VALIDATOR_ISSUES"
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
