# 自動化規格書 (Automation Specification)

## 1. 系統概觀
本系統旨在自動化知識研發流程，包含三個主要階段：研發生成 (Ingestion)、知識編碼 (Encoding)、視覺化交付 (Visualization)。

## 2. 核心組件與架構
- **控制中心**: Google Antigravity IDE
- **研發引擎**: Gemini CLI / Batch API (via `generate_reports.py`)
- **知識庫**: NotebookLM (via `upload_to_brain.py` & `notebooklm-mcp`)
- **通訊協議**: Model Context Protocol (MCP)

## 3. 詳細實作規格

### 3.1 第一工作流：研發生成 (Ingestion Stream)
- **腳本**: `scripts/generate_reports.py`
- **輸入**: `raw_thoughts/` (*.txt, *.md)
- **輸出**: `processed_reports/` (*.md)
- **邏輯**:
  1. 掃描輸入目錄。
  2. 讀取檔案內容並套用 Meta-Prompt (學術報告格式)。
  3. 呼叫 Google Generative AI API (Gemini 1.5 Pro)。
  4. 儲存 Markdown 報告。
- **驗證標準**: 必須通過 17-Layer Validation (AST 檢查, 錯誤處理等)。

### 3.2 第二工作流：知識庫自動化 (Encoding Stream)
- **腳本**: `scripts/upload_to_brain.py`
- **輸入**: `processed_reports/` (*.md)
- **工具**: `notebooklm-mcp-server` (MCP)
- **邏輯**:
  1. 初始化 MCP Client Session。
  2. 檢查 `notebook_create` 工具可用性。
  3. 建立或鎖定目標 Notebook (標題: "Automated Research")。
  4. 遍歷報告，使用 `source_add_text` 上傳內容。
- **必要依賴**: 用戶需完成 `notebooklm-mcp` 的 Cookie 認證。

### 3.3 第三工作流：視覺化 (Visualization Stream)
- **執行者**: Antigravity Agent (Human-in-the-loop)
- **觸發方式**: `@automation_spec.md` 指令
- **工具**: 
  - Slidev (簡報生成)
  - Mermaid (流程圖/心智圖)
- **指令範本**:
  - "請讀取 NotebookLM 中的報告，並為我生成一份 Slidev 簡報 (`slides.md`)。"
  - "請根據報告中的數據，繪製 Mermaid 趨勢圖。"

## 4. 部署與執行清單
1. [x] 安裝 Python 依賴 (`uv pip install google-generativeai mcp python-dotenv`)。
2. [x] 安裝 MCP Server (`uv tool install notebooklm-mcp-server`)。
3. [x] 建立並驗證 `generate_reports.py` (17-Layer Passed)。
4. [x] 建立並驗證 `upload_to_brain.py` (17-Layer Passed)。
5. [ ] **關鍵路徑**: 用戶手動配置 `mcp_config.json` 與 Cookie。
6. [ ] **全流程測試**: 執行 `run_pipeline.py` (待建立)。

## 5. 風險評估
- **高風險**: NotebookLM Cookie 過期導致 MCP 連線失敗。-> **對策**: 腳本中加入明確的錯誤提示，引導用戶更新 Cookie。
- **中風險**: Gemini API 配額限制。-> **對策**: 腳本已實作 `time.sleep(2)` 簡單限流。
