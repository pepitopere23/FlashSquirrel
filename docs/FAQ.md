# ❓ 常見問題與故障排除 (FAQ & Troubleshooting)

[繁體中文](#繁體中文) | [English](#english)

---

<a name="繁體中文"></a>

## 繁體中文

### Q1: 我已經把檔案弄進資料夾了，為什麼沒有產出報告？
**A**: 請檢查以下三點：
1.  **引擎是否啟動**：確保您已經執行了 `python start.py` 且視窗沒有關閉。
2.  **檔名格式**：系統會監控 `input_thoughts/` 底下的 **「子資料夾」**。請不要直接把檔案丟在 `input_thoughts/` 根目錄，應該要建立一個如 `input_thoughts/我的研究主題/` 的資料夾。
3.  **iCloud 同步**：如果您是使用手機上傳，Mac 可能還沒下載完畢。FlashSquirrel 內建「下載等待」機制，會等到此圖示消失後才開始工作。

### Q2: 出現 `Quota Exceeded` 或 `429 Error` 怎麼辦？
**A**: 這是因為您使用的是 **免費版 API**，Google 限制每分鐘的請求次數。
*   **別擔心**：FlashSquirrel v1.0.0 內建 **「指數退避 (Exponential Backoff)」** 機制。它會自動暫停、等待、然後重試。您只需放著不管即可。
*   **想解鎖極速**：建議前往 Google AI Studio 綁定信用卡開啟付費方案，費用極低（見 README 試算）。

### Q3: 速度好像有點慢？能不能一次跑 10 篇？
**A**: 系統刻意設計為 **單一序列處理 (Single Queue)**，速度約為 **1 分鐘/篇**。
*   **原因**：如果同時開啟 10 個瀏覽器分頁去轟炸 NotebookLM，您的帳號極高機率會被 Google 判定為濫用 (Abuse) 而封鎖。
*   **策略**：FlashSquirrel 選擇「穩定長跑」而非「短跑衝刺」，確保您的帳號安全。

### Q4: Windows 能用嗎？
**A**: **可以！(v1.0.0+)**
*   最新版本已經完整支援 Windows。如果您遇到 `pathlib` 相關錯誤，請務必點擊 GitHub 上的 `Sync Fork` 進行更新。
*   初次安裝請執行 `python setup_wizard.py`，它會自動處理 Windows 的環境設定。

### Q5: 我可以用 `.docx` 或圖片嗎？
**A**: **當然。**
*   系統支援：`.md`, `.txt`, `.docx`, `.pdf`, `.jpg`, `.png`, 甚至 Mac 的網站連結 `.webloc`。

---

<a name="english"></a>

## English

### Q1: I dropped the files, but no report?
**A**: Check these:
1.  **Is Engine Running?**: Ensure `python start.py` is active.
2.  **Sub-folders**: Files must be inside a **sub-folder** (e.g., `input_thoughts/Topic_A/`), not the root.
3.  **iCloud Sync**: The system waits for iCloud downloads to complete automatically.

### Q2: `Quota Exceeded` / `429 Error`?
**A**: This is normal for the Free Tier API.
*   **Solution**: Do nothing. FlashSquirrel v1.0.0 has **Exponential Backoff**. It will pause and retry automatically.

### Q3: Can it be faster? Can I process 10 papers at once?
**A**: The system deliberately uses a **Single Queue** (approx. 1 min/paper).
*   **Safety**: Opening 10 browser tabs simultaneously triggers Google's Abuse Detection.
*   **Strategy**: "Slow and steady" protects your account from being banned.

### Q4: Does it work on Windows?
**A**: **YES! (v1.0.0+)**
*   Critical compatibility fixes have been applied. If you see errors, please `Sync Fork` on GitHub.
*   Run `python setup_wizard.py` to auto-configure for Windows.

### Q5: Can I use `.docx` or images?
**A**: **Yes.**
*   Supported: `.md`, `.txt`, `.docx`, `.pdf`, `.jpg`, `.png`, and even `.webloc` (Mac links).

