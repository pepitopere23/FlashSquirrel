#!/bin/bash

CHROME_PATH="/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"
USER_DATA_DIR="/tmp/chrome-debug-profile"

echo "========================================================"
echo "   NotebookLM Auth Fixer (Bypass Security)"
echo "========================================================"
echo "Phase 1: Closing existing Chrome instances..."
pkill -f "Google Chrome"
sleep 2

echo "Phase 2: Launching Chrome in Debug Mode..."
echo "Please wait for the window to open..."

# Launch Chrome with specific flags to allow MCP connection
"$CHROME_PATH" \
  --remote-debugging-port=9222 \
  --remote-allow-origins=* \
  --user-data-dir="$USER_DATA_DIR" \
  --no-first-run \
  "https://notebooklm.google.com" &

CHROME_PID=$!

echo ""
echo "👉 ACTION REQUIRED:"
echo "1. A new Chrome window has opened (temporary profile)."
echo "2. Please LOGIN to your Google Account in that window."
echo "3. Ensure you are on the NotebookLM homepage."
echo "4. Once you are logged in, return here and press ENTER."
echo "========================================================"
read -p "Press ENTER when you are logged in..."

echo "Phase 3: Extracting Tokens..."
# Run the auth tool in no-launch mode, connecting to our properly flagged Chrome
uv tool run --from notebooklm-mcp-server notebooklm-mcp-auth --no-auto-launch

echo ""
echo "Closing temporary Chrome..."
kill $CHROME_PID

echo "========================================================"
echo "Token extraction attempt complete."
echo "Run 'python3 scripts/test_mcp_connection.py' to verify."
echo "========================================================"
