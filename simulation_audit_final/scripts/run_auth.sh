#!/bin/bash
echo "========================================================"
echo "   NotebookLM Automated Authentication Helper"
echo "========================================================"
echo "This script will attempt to automatically extract login cookies from Chrome."
echo ""
echo "⚠️  IMPORTANT:"
echo "1. Please CLOSE Google Chrome completely before proceeding."
echo "2. This tool will launch a new Chrome window."
echo "3. If it asks you to login, please do so."
echo "========================================================"
echo "Press ENTER to start (or Ctrl+C to cancel)..."
read

echo "Running authentication tool..."
uv tool run --from notebooklm-mcp-server notebooklm-mcp-auth

echo ""
echo "If the above completed successfully, run 'python3 scripts/test_mcp_connection.py' to verify."
