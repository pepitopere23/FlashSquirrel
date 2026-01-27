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

*   **解決方案**：請再次執行 `python setup_wizard.py`（或透過 `start.py` 重新配置），它會彈出瀏覽器讓您重新登入並擷取最新憑證。

### Q4: 那個終端機（黑框框）可以關掉嗎？
**A**: **目前不行**。
*   這個視窗是 FlashSquirrel 的「肉身」，它必須開著才能監控資料夾的變動。如果您關掉它，松鼠就下班了，不會再自動幫您研發。
*   **專業提示**：如果您是高階用戶，可以使用 `scripts/com.user.research_pipeline.plist` 將其設定為後台服務，這樣就完全看不到視窗了。

### Q5: 我在 Mac 上明明丟了檔案，為什麼它一直說「找不到檔案」？
**A**: 這是典型的 **「權限不足」** 問題。
*   **原因**：macOS 為了保護您的個資，預設禁止程式讀取 iCloud 或桌面。
*   **解決方案**：前往「系統設定 -> 隱私與安全性 -> 完全磁碟取用權限」，手動將 **Terminal** (或您使用的終端機軟體) 加入並開啟即可。

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

*   **Solution**: Run `python setup_wizard.py` again (or re-configure via `start.py`). A browser window will open for you to log in and capture fresh credentials.

### Q4: Can I close the terminal window?
**A**: **Currently, no**.
*   This window is the physical process of FlashSquirrel. It must stay open to "watch" your folders. If you close it, the "squirrel" goes home and stops working.
*   **Pro Tip**: Advanced users can use the `scripts/com.user.research_pipeline.plist` to set it as a background service, making it truly invisible.

### Q5: I'm on a Mac and dropped files, but it says "File not found"?
**A**: This is a classic **"Permissions"** issue.
*   **Cause**: macOS limits app access to iCloud or Desktop by default.
*   **Solution**: Go to "System Settings -> Privacy & Security -> Full Disk Access" and toggle ON for **Terminal**.
