#!/usr/bin/env bash
# setup.sh — one-shot setup for project_starter_v5
#
# Usage:
#   bash setup.sh                                  # download plantuml.jar + check Java (framework dev)
#   bash setup.sh --init <type> <dest>             # bootstrap a new project into <dest>
#   bash setup.sh --detect [path] ["requirements"] # infer project type from code or text
#
# Valid types: web-app | cli-tool | library | data-pipeline | ml-pipeline
#              microservices | llm-app | iac | mobile-app

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLANTUML_JAR="${SCRIPT_DIR}/templates/script/generators/plantuml.jar"
PLANTUML_VERSION="1.2024.6"
PLANTUML_URL="https://github.com/plantuml/plantuml/releases/download/v${PLANTUML_VERSION}/plantuml-${PLANTUML_VERSION}.jar"

VALID_TYPES="web-app cli-tool library data-pipeline ml-pipeline microservices llm-app iac mobile-app"

# ── --detect mode ─────────────────────────────────────────────────────────────
if [[ "${1:-}" == "--detect" ]]; then
    DETECT_PATH="${2:-.}"
    REQUIREMENTS="${3:-}"

    if ! command -v python3 &>/dev/null; then
        echo "[FAIL] python3 not found. Install Python 3.8+ to use --detect."
        exit 1
    fi

    DETECT_SCRIPT="${SCRIPT_DIR}/detect_type.py"
    if [[ ! -f "$DETECT_SCRIPT" ]]; then
        echo "[FAIL] detect_type.py not found at ${DETECT_SCRIPT}"
        exit 1
    fi

    CMD=(python3 "$DETECT_SCRIPT" "$DETECT_PATH")
    [[ -n "$REQUIREMENTS" ]] && CMD+=(--requirements "$REQUIREMENTS")

    "${CMD[@]}"
    exit 0
fi

# ── --init mode ───────────────────────────────────────────────────────────────
if [[ "${1:-}" == "--init" ]]; then
    PROJECT_TYPE="${2:-}"
    DEST="${3:-}"

    if [[ -z "$PROJECT_TYPE" || -z "$DEST" ]]; then
        echo "Usage: bash setup.sh --init <type> <dest>"
        echo "  type: $VALID_TYPES"
        echo "  dest: target project directory (will be created if absent)"
        exit 1
    fi

    VALID=false
    for t in $VALID_TYPES; do
        [[ "$PROJECT_TYPE" == "$t" ]] && VALID=true && break
    done
    if [[ "$VALID" == false ]]; then
        echo "[FAIL] Unknown project type: $PROJECT_TYPE"
        echo "       Valid values: $VALID_TYPES"
        exit 1
    fi

    echo "=== project_starter_v5 init: $PROJECT_TYPE → $DEST ==="
    echo ""
    mkdir -p "$DEST"

    # Copy framework files
    for f in AGENTS.md orchestrator.py build-context.py _workflow_utils.py \
              workflow-registry.yaml document-registry.yaml detect_type.py \
              debug-instrumentation-rules.md code-quality-check.md; do
        cp "${SCRIPT_DIR}/${f}" "${DEST}/"
        echo "[OK] copied $f"
    done

    cp -r "${SCRIPT_DIR}/.githooks" "${DEST}/"
    echo "[OK] copied .githooks/"

    cp -r "${SCRIPT_DIR}/guidance" "${DEST}/"
    echo "[OK] copied guidance/"

    # CLAUDE.md is Claude Code's auto-loaded context file — importing AGENTS.md here
    # guarantees its rules (including Learning Checkpoint) load at the start of every
    # session, with no dependency on which task-specific docs current-state.md points to.
    if [[ ! -f "${DEST}/CLAUDE.md" ]]; then
        echo "@AGENTS.md" > "${DEST}/CLAUDE.md"
        echo "[OK] wrote CLAUDE.md (@AGENTS.md)"
    fi

    mkdir -p "${DEST}/docs/script"
    cp -r "${SCRIPT_DIR}/templates/script/." "${DEST}/docs/script/"
    echo "[OK] copied templates/script/ → docs/script/"

    # Write pre-filled .project-starter.yml
    cat > "${DEST}/.project-starter.yml" <<EOF
# project_starter — project configuration
# Do not rename this file.

project_type: ${PROJECT_TYPE}
# Valid values: web-app | cli-tool | library | data-pipeline | ml-pipeline
#               microservices | llm-app | iac | mobile-app

docs_path: docs/

task_type:
# Optional. Filters .ai/AI_CONTEXT.md to task-relevant documents.
# Valid values: feature | pipeline-stage | bug-fix | sprint-end | eval-run | iac-change

spec_code_adapter:
spec_code_spec:
spec_code_src:
# Optional — all three must be set together to enable the spec ↔ code drift gate.
# See README.md → Spec ↔ Code Validator for the full list of adapter names.

test_command:
# Optional. Shell command that runs this project's test suite, e.g. \`pytest -q\` |
# \`npm test\` | \`go test ./...\`. When set, .githooks/pre-commit actually runs it on every
# commit and blocks if it exits non-zero. Leave blank to skip this gate.
EOF
    echo "[OK] wrote .project-starter.yml (project_type: ${PROJECT_TYPE})"

    # Install pre-commit hook — only if a real git repo exists (HEAD file is the marker)
    if [[ -f "${DEST}/.git/HEAD" ]]; then
        mkdir -p "${DEST}/.git/hooks"
        cp "${DEST}/.githooks/pre-commit" "${DEST}/.git/hooks/pre-commit"
        chmod +x "${DEST}/.git/hooks/pre-commit"
        echo "[OK] pre-commit hook installed"
    else
        echo "[WARN] ${DEST} is not a git repository — run git init first, then:"
        echo "       cp .githooks/pre-commit .git/hooks/pre-commit && chmod +x .git/hooks/pre-commit"
    fi

    echo ""
    echo "Next steps:"
    echo "  cd ${DEST}"
    echo "  python3 orchestrator.py --adapter claude   # generate .ai/WORKFLOW.md + start-task.md"
    echo "  Open templates/init/${PROJECT_TYPE}.md and follow its numbered steps."
    exit 0
fi

# ── Standard setup (no --init) ────────────────────────────────────────────────
echo "=== project_starter_v5 setup ==="
echo ""

# ── 1. Check Java ─────────────────────────────────────────────────────────────
if java -version &>/dev/null 2>&1; then
    JAVA_VER=$(java -version 2>&1 | head -1)
    echo "[OK] Java found: ${JAVA_VER}"
else
    echo "[WARN] Java not found. Install JDK 11+ to render PlantUML diagrams."
    echo "     macOS:   brew install openjdk"
    echo "     Ubuntu:  sudo apt install default-jdk"
    echo "     Windows: https://adoptium.net"
    echo ""
fi

# ── 2. Download plantuml.jar ──────────────────────────────────────────────────
if [ -f "${PLANTUML_JAR}" ]; then
    echo "[OK] plantuml.jar already present: ${PLANTUML_JAR}"
else
    echo "Downloading plantuml.jar v${PLANTUML_VERSION}..."
    if command -v curl &>/dev/null; then
        curl -fL "${PLANTUML_URL}" -o "${PLANTUML_JAR}"
    elif command -v wget &>/dev/null; then
        wget -q -O "${PLANTUML_JAR}" "${PLANTUML_URL}"
    else
        echo "[FAIL] curl and wget not found."
        echo "    Download plantuml.jar manually and place it at:"
        echo "    ${PLANTUML_JAR}"
        echo "    Download URL: ${PLANTUML_URL}"
        exit 1
    fi
    echo "[OK] plantuml.jar downloaded: ${PLANTUML_JAR}"
fi

echo ""
echo "Setup complete."
echo ""
echo "To detect project type from existing code or a description:"
echo "  bash setup.sh --detect /path/to/your-project"
echo "  bash setup.sh --detect . \"web API with LLM chatbot\""
echo ""
echo "To bootstrap a new project:"
echo "  bash setup.sh --init <type> /path/to/your-project"
echo "  Valid types: $VALID_TYPES"
echo ""
echo "Next steps (framework development):"
echo "  pip install \"pytest>=7\" pyyaml"
echo "  pytest tests/"
echo ""
echo "To generate a PDF (after initializing a project):"
echo "  pip install markdown weasyprint cairosvg --break-system-packages"
echo "  python3 docs/script/generators/build_pdf.py docs --lang en --project-type <type>"
