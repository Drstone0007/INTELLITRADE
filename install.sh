#!/usr/bin/env bash
set -e

BOLD='\033[1m'
DIM='\033[2m'
GREEN='\033[0;32m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}"
echo "  ██████  ██████  ████████ ██████  ███████ ██      ███  "
echo " ██      ██    ██    ██    ██   ██ ██      ██      ███  "
echo " ██      ██    ██    ██    ██████  █████   ██      ███  "
echo " ██      ██    ██    ██    ██   ██ ██      ██           "
echo "  ██████  ██████     ██    ██   ██ ███████ ███████ ███  "
echo -e "${NC}"
echo -e "${BOLD}INTELLITRADE — Drtlemon Elite Tech Conglomerate${NC}"
echo -e "${DIM}Engineering the asymmetric edge. Systems over outcomes. Mathematics over emotion.${NC}"
echo ""

REPO="https://github.com/Drstone0007/INTELLITRADE.git"
INSTALL_DIR="${HOME}/intellitrade"

# ── Clone ──────────────────────────────────────────────
if [ -d "$INSTALL_DIR" ]; then
    echo "→ Updating existing installation at $INSTALL_DIR"
    cd "$INSTALL_DIR"
    git pull origin master 2>/dev/null || true
else
    echo "→ Cloning into $INSTALL_DIR"
    git clone --depth 1 "$REPO" "$INSTALL_DIR"
    cd "$INSTALL_DIR"
fi

# ── Python ─────────────────────────────────────────────
PY=$(command -v python3)
if [ -z "$PY" ]; then
    echo "✗ Python 3 not found. Install it first."
    exit 1
fi

echo "→ Setting up Python environment"
if python3 -m venv .venv 2>/dev/null; then
    source .venv/bin/activate
    PIP="python3 -m pip"
else
    echo "  (venv unavailable — installing globally)"
    PIP="python3 -m pip"
fi

$PIP install eth-account --quiet --break-system-packages 2>/dev/null || \
$PIP install eth-account --quiet 2>/dev/null || true

# ── Verify ─────────────────────────────────────────────
echo "→ Verifying installation"
SCAN_CMD="timeout 30 python3 _POLYARB/Tools/polyarb_main.py scan --max-events 10"
if $SCAN_CMD 2>/dev/null | python3 -c "import sys,json;d=json.load(sys.stdin);print(f'✓ {sum(len(v) for v in d.values())} arb opportunities found')" 2>/dev/null; then
    echo ""
    echo -e "${GREEN}${BOLD}INTELLITRADE is ready.${NC}"
    echo ""
    echo -e "${BOLD}Quick start:${NC}"
    echo "  cd ~/intellitrade"
    echo "  python3 _POLYARB/Tools/polyarb_main.py agent --interval 300"
    echo "  python3 _POLYARB/Tools/polyarb_main.py telegram start"
    echo ""
    echo -e "${BOLD}Documentation:${NC}"
    echo "  cat docs/BLUEPRINT_POLYARB.md"
    echo "  cat docs/DEPLOYMENT.md"
else
    echo "✗ Scan failed — check Python dependencies"
    $SCAN_CMD 2>&1 || true
fi
