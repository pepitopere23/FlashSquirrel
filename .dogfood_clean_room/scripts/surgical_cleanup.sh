#!/bin/bash
# 🐿️ FlashSquirrel: 歷史保衛戰 (History Safeguard) - Surgical Cleanup
# 僅刪除毒素，保留所有「綠色點點」(GitHub Contributions) 與開發紀錄。

echo "🐿️  啟動歷史保衛戰 (History Safeguard Protocol)..."

# 1. 檢查是否安裝了 git-filter-repo (推薦) 或使用傳統的 BFG
# 如果沒有安裝，我們使用 git filter-branch (內建)
echo "🛡️  正在執行外科手術式清洗：dashboard_debug.html..."

git filter-branch --force --index-filter \
  "git rm --cached --ignore-unmatch **/dashboard_debug.html" \
  --prune-empty --tag-name-filter cat -- --all

echo ""
echo "============================================================"
echo "✅ 外科手術完成！"
echo "1. 毒素 (dashboard_debug.html) 已從所有歷史 Commit 中移除。"
echo "2. 您的「綠色點點」與 Commit 紀錄已被完整保留。"
echo ""
echo "請執行以下步驟來更新 GitHub (請手動確認)："
echo "git push origin --force --all"
echo "============================================================"
echo "🐿️  歷史已恢復純淨，回憶完好無損。"
