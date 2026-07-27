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
