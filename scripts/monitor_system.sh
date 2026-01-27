#!/bin/bash

# Configuration
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
LOG_FILE="$PROJECT_DIR/pipeline_bg.log"
ENV_FILE="$PROJECT_DIR/.env"
AUTH_FILE="$HOME/.notebooklm-mcp/auth.json"

echo "=================================================="
echo "🩺 光速研究工作流 - 系統健康檢查 (System Health Check)"
echo "=================================================="
echo "時間: $(date)"
echo ""

# 1. Check Process Status
echo "[1] 檢查背景核心 (Core Engine)..."
PID=$(pgrep -f "auto_research_pipeline.py")
if [ -n "$PID" ]; then
    echo "   ✅ 運作中 (PID: $PID)"
else
    echo "   ❌ 未運行 (Process NOT found)"
    echo "   💡 建議執行: launchctl load ~/Library/LaunchAgents/com.user.research_pipeline.plist"
fi
echo ""

# 2. Check Configuration
echo "[2] 檢查設定檔 (Configuration)..."
if [ -f "$ENV_FILE" ]; then
    echo "   ✅ .env 檔案存在"
else
    echo "   ❌ .env 遺失！ (請確認 API Key 是否設定)"
fi

if [ -f "$AUTH_FILE" ]; then
    echo "   ✅ NotebookLM 認證檔存在"
else
    echo "   ⚠️ NotebookLM 認證檔遺失 (可能無法自動歸檔)"
    echo "   💡 建議執行: scripts/fix_auth.sh"
fi
echo ""

# 3. Check Logs
echo "[3] 檢查最近日誌 (Recent Logs)..."
if [ -f "$LOG_FILE" ]; then
    echo "   📂 日誌路徑: $LOG_FILE"
    echo "   --- 最近 5 行紀錄 ---"
    tail -n 5 "$LOG_FILE" | sed 's/^/   /'
    echo "   ---------------------"
    
    # Check for errors in the last 50 lines
    ERROR_COUNT=$(tail -n 50 "$LOG_FILE" | grep -i "Error" | wc -l)
    if [ "$ERROR_COUNT" -gt 0 ]; then
        echo "   ⚠️ 警告: 在最近 50 行中發現 $ERROR_COUNT 個錯誤。"
        tail -n 50 "$LOG_FILE" | grep -i "Error" | tail -n 3 | sed 's/^/   🔴 /'
    else
        echo "   ✅ 最近無明顯錯誤。"
    fi
else
    echo "   ❌ 找不到日誌檔案！"
fi
echo ""

# 4. Check Internet
echo "[4] 檢查連線能力 (Connectivity)..."
if ping -c 1 google.com &> /dev/null; then
    echo "   ✅ 網際網路連線正常"
else
    echo "   ❌ 無法連線到 Internet (影響 Gemini/NotebookLM)"
fi

echo ""
echo "=================================================="
echo "檢查完畢。"
