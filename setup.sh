#!/usr/bin/env bash
set -e

echo ""
echo "═══════════════════════════════════════"
echo "  Hotel Mirror — Setup"
echo "═══════════════════════════════════════"

# 1. Install dependencies
echo ""
echo "▸ Installing Python dependencies..."
pip install -r requirements.txt

# 2. Check for API key
echo ""
if [ -z "$ANTHROPIC_API_KEY" ]; then
  echo "▸ No ANTHROPIC_API_KEY found in environment."
  echo ""
  echo "  Option A — set it for this session:"
  echo "    export ANTHROPIC_API_KEY=sk-ant-..."
  echo ""
  echo "  Option B — create a .env file:"
  echo "    cp .env.example .env"
  echo "    # then edit .env and add your key"
  echo "    # then run:  source .env  (or use python-dotenv)"
  echo ""
  echo "  Get a key at: https://console.anthropic.com → API Keys"
else
  echo "▸ ANTHROPIC_API_KEY is set ✓"
fi

echo ""
echo "═══════════════════════════════════════"
echo "  Ready. Run the agent:"
echo "    python agent.py"
echo "  or open hotel_mirror.html in a browser"
echo "═══════════════════════════════════════"
echo ""
