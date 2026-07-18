#!/usr/bin/env bash
# Optional Claude Code fast-feedback script (Phase 20).
# Called by .claude/settings.json Stop hook after every Claude session.
# Writes verify output to logs/ — non-blocking (always exits 0).

mkdir -p logs
if [ ! -f .project-starter.yml ] || [ ! -f docs/script/validators/verify_docs.py ]; then
    exit 0
fi
TYPE=$(grep '^project_type:' .project-starter.yml | sed 's/project_type:[[:space:]]*//' | tr -d "\"'")
[ -z "$TYPE" ] && exit 0
STAMP=$(date +%Y%m%d-%H%M%S)
{
    [ -f docs/script/validators/verify_docs.py ]    && python3 docs/script/validators/verify_docs.py    --project-type "$TYPE" --content --json 2>&1
    [ -f docs/script/validators/verify_logs.py ]    && python3 docs/script/validators/verify_logs.py    --project-type "$TYPE" 2>&1
    [ -f docs/script/validators/verify_tests.py ]   && python3 docs/script/validators/verify_tests.py   --project-type "$TYPE" 2>&1
    [ -f docs/script/validators/verify_content.py ] && python3 docs/script/validators/verify_content.py --project-type "$TYPE" 2>&1
} > "logs/verify-${STAMP}.json" 2>&1 || true
