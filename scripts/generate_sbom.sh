#!/usr/bin/env bash
# Generate Software Bill of Materials (SBOM) using CycloneDX
# Generates SBOMs for Python (backend) and Node.js (frontend)
# Output directory: sbom/
# Format: CycloneDX JSON

set -e

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SBOM_DIR="$REPO_ROOT/sbom"

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== CycloneDX SBOM Generation ===${NC}"
echo "Repository root: $REPO_ROOT"
echo "Output directory: $SBOM_DIR"
echo ""

# Create output directory
mkdir -p "$SBOM_DIR"

PYTHON_OK=0
NODE_OK=0

# ============================================================================
# Python (Backend) SBOM
# ============================================================================
echo -e "${YELLOW}[1/2] Generating Python SBOM from backend/requirements.txt...${NC}"

BACKEND_REQUIREMENTS="$REPO_ROOT/backend/requirements.txt"
PYTHON_SBOM="$SBOM_DIR/sbom-python.json"

if [ ! -f "$BACKEND_REQUIREMENTS" ]; then
    echo "  ERROR: $BACKEND_REQUIREMENTS not found"
else
    # Ensure cyclonedx-py is available
    if ! command -v cyclonedx-py &> /dev/null; then
        echo "  Installing cyclonedx-bom..."
        pip install cyclonedx-bom --quiet 2>/dev/null || {
            echo "  ERROR: Failed to install cyclonedx-bom. Ensure pip is configured."
            PYTHON_SBOM=""
        }
    fi

    if [ -n "$PYTHON_SBOM" ] && command -v cyclonedx-py &> /dev/null; then
        if cyclonedx-py requirements "$BACKEND_REQUIREMENTS" --output-file "$PYTHON_SBOM" 2>/dev/null; then
            SIZE=$(wc -c < "$PYTHON_SBOM")
            echo -e "${GREEN}  ✓ Generated: $PYTHON_SBOM ($SIZE bytes)${NC}"
            PYTHON_OK=1
        else
            echo "  ERROR: cyclonedx-py failed to generate SBOM"
            rm -f "$PYTHON_SBOM"
        fi
    fi
fi

# ============================================================================
# Node.js (Frontend) SBOM
# ============================================================================
echo -e "${YELLOW}[2/2] Generating Node.js SBOM from frontend/package-lock.json...${NC}"

FRONTEND_LOCKFILE="$REPO_ROOT/frontend/package-lock.json"
NODE_SBOM="$SBOM_DIR/sbom-nodejs.json"

if [ ! -f "$FRONTEND_LOCKFILE" ]; then
    echo "  WARNING: $FRONTEND_LOCKFILE not found. Skipping Node.js SBOM."
else
    # Check if npm is available
    if ! command -v npm &> /dev/null; then
        echo "  ERROR: npm not found. Cannot generate Node.js SBOM."
    else
        # Use npx to run cyclonedx-npm
        cd "$REPO_ROOT/frontend"

        if npx cyclonedx-npm --output-file "$NODE_SBOM" 2>&1 | grep -v "placeholder\|misconfiguration\|dependency confusion" > /dev/null; then
            if [ -f "$NODE_SBOM" ]; then
                SIZE=$(wc -c < "$NODE_SBOM")
                echo -e "${GREEN}  ✓ Generated: $NODE_SBOM ($SIZE bytes)${NC}"
                NODE_OK=1
            fi
        else
            echo "  ERROR: cyclonedx-npm failed or is not available."
            echo "  Note: cyclonedx-npm must be installed separately via 'npm install --save-dev @cyclonedx/npm'"
            rm -f "$NODE_SBOM" 2>/dev/null || true
        fi

        cd "$REPO_ROOT"
    fi
fi

# ============================================================================
# Summary
# ============================================================================
echo ""
echo -e "${BLUE}=== Summary ===${NC}"

if [ $PYTHON_OK -eq 1 ] && [ $NODE_OK -eq 1 ]; then
    echo -e "${GREEN}✓ Both Python and Node.js SBOMs generated successfully${NC}"
    ls -lh "$SBOM_DIR"/sbom-*.json
    exit 0
elif [ $PYTHON_OK -eq 1 ] || [ $NODE_OK -eq 1 ]; then
    echo -e "${YELLOW}⚠ At least one SBOM generated (partial success)${NC}"
    if [ $PYTHON_OK -eq 1 ]; then
        echo -e "  ✓ Python SBOM: $PYTHON_SBOM"
    fi
    if [ $NODE_OK -eq 1 ]; then
        echo -e "  ✓ Node.js SBOM: $NODE_SBOM"
    fi
    exit 0
else
    echo -e "${YELLOW}⚠ No SBOMs were generated. Check dependencies and logs above.${NC}"
    exit 1
fi
