#!/usr/bin/env bash
# setup.sh — one-shot setup for project_starter_v5
#
# Downloads plantuml.jar and verifies Java is installed.
# Run once after cloning the repo.

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PLANTUML_JAR="${SCRIPT_DIR}/templates/script/generators/plantuml.jar"
PLANTUML_VERSION="1.2024.6"
PLANTUML_URL="https://github.com/plantuml/plantuml/releases/download/v${PLANTUML_VERSION}/plantuml-${PLANTUML_VERSION}.jar"

echo "=== project_starter_v5 setup ==="
echo ""

# ── 1. Check Java ─────────────────────────────────────────────────────────────
if java -version &>/dev/null 2>&1; then
    JAVA_VER=$(java -version 2>&1 | head -1)
    echo "✅  Java found: ${JAVA_VER}"
else
    echo "⚠️   Java not found. Install JDK 11+ to render PlantUML diagrams."
    echo "     macOS:   brew install openjdk"
    echo "     Ubuntu:  sudo apt install default-jdk"
    echo "     Windows: https://adoptium.net"
    echo ""
fi

# ── 2. Download plantuml.jar ──────────────────────────────────────────────────
if [ -f "${PLANTUML_JAR}" ]; then
    echo "✅  plantuml.jar already present: ${PLANTUML_JAR}"
else
    echo "Downloading plantuml.jar v${PLANTUML_VERSION}..."
    if command -v curl &>/dev/null; then
        curl -fL "${PLANTUML_URL}" -o "${PLANTUML_JAR}"
    elif command -v wget &>/dev/null; then
        wget -q -O "${PLANTUML_JAR}" "${PLANTUML_URL}"
    else
        echo "❌  curl and wget not found."
        echo "    Download plantuml.jar manually and place it at:"
        echo "    ${PLANTUML_JAR}"
        echo "    Download URL: ${PLANTUML_URL}"
        exit 1
    fi
    echo "✅  plantuml.jar downloaded: ${PLANTUML_JAR}"
fi

echo ""
echo "Setup complete."
echo ""
echo "Next steps:"
echo "  pip install pytest"
echo "  pytest tests/"
echo ""
echo "To generate a PDF (after initializing a project):"
echo "  pip install markdown weasyprint cairosvg --break-system-packages"
echo "  python3 docs/script/generators/build_pdf.py docs --lang en --project-type <type>"
