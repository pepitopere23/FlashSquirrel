# ❓ 常見問題與故障排除 (FAQ & Troubleshooting)

[繁體中文](#繁體中文) | [English](#english)

---

<a name="繁體中文"></a>

## 繁體中文

### Q1: 我已經把檔案弄進資料夾了，為什麼沒有產出報告？
**A**: 請檢查以下三點：
1.  **引擎是否啟動**：確保您已經執行了 `python start.py` 且視窗沒有關閉。
2.  **檔名格式**：系統會監控 `input_thoughts/` 底下的 **「子資料夾」**。請不要直接把檔案丟在 `input_thoughts/` 根目錄，應該要建立一個如 `input_thoughts/我的研究主題/` 的資料夾。
3.  **iCloud 同步**：如果您是使用手機上傳，Mac 可能還沒下載完畢。請打開 Finder 看看該檔案是否有一個「雲端下載」的圖示。

### Q2: 出現 `Quota Exceeded` 或 `429 Error` 怎麼辦？
**A**: 這是因為您使用的是 **免費版 API**，Google 限制每分鐘的請求次數。
*   **別擔心**：FlashSquirrel 內建自動排隊機制，它會每隔一段時間自動重試，您只需放著不管即可。
*   **想解鎖極速**：建議前往 Google AI Studio 綁定信用卡開啟付費方案，費用極低（見 README 試算）。

### Q3: 為什麼 NotebookLM 的自動上傳失敗了？
**A**: 通常是因為 **Cookie 過期**。
*   **解決方案**：請再次執行 `python setup_wizard.py`（或透過 `start.py` 重新配置），它會彈出瀏覽器讓您重新登入並擷取最新憑證。

---

<a name="english"></a>

## English

### Q1: I dropped the files into the folder, but why is there no report?
**A**: Please check these three things:
1.  **Is the Engine Running?**: Make sure you have executed `python start.py` and the terminal window remains open.
2.  **Sub-folder Structure**: The system watches **sub-folders** inside `input_thoughts/`. Instead of dropping files into the root, create a folder like `input_thoughts/My_Project/`.
3.  **iCloud Sync**: If uploading via mobile, your Mac might still be downloading the file. Check Finder for the "cloud download" icon next to the file.

### Q2: What should I do if I see `Quota Exceeded` or `429 Error`?
**A**: This occurs because you are using the **Free Tier API**, which has rate limits.
*   **Don't Panic**: FlashSquirrel has a built-in auto-queuing mechanism. It will retry automatically, so you can just leave it running.
*   **For Speed**: Consider enabling the Paid Tier in Google AI Studio. The cost is extremely low (see the table in README).

### Q3: Why did the NotebookLM auto-upload fail?
**A**: This is usually due to **expired cookies**.
*   **Solution**: Run `python setup_wizard.py` again (or re-configure via `start.py`). A browser window will open for you to log in and capture fresh credentials.
