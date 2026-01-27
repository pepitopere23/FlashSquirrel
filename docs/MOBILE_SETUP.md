# 📱 Mobile-to-PC Workflow (行動端同步工作流)

[繁體中文](#繁體中文) | [English](#english)

---

<a name="繁體中文"></a>

## 1. Apple (iOS) 用戶：利用「捷徑」實現光速捕捉

對於 iPhone 用戶，最強大的方式是利用系統內建的「捷徑 (Shortcuts)」與 iCloud Drive 的無縫同步。

### 設定步驟：
1.  **建立捷徑**：
    - [點此下載設定好的「光速研究」捷徑](https://www.icloud.com/shortcuts/b7238297c2494f73addcd1b7330bdebf)。
2.  **加入動作**：
    - **動作 1: 建立資料夾**：在 iCloud Drive 的 `研究工作流/input_thoughts` 目錄下，根據當前日期建立一個新資料夾。
    - **動作 2: 儲存檔案**：將「分享表單 (Share Sheet)」傳入的圖片、PDF 或文字存入該資料夾。
3.  **使用方式**：
    - 在閱讀網頁或查看照片時，點擊「分享」->「光速研究」。
    - 電腦端的 `FlashSquirrel` 偵測到 iCloud 同步後會立即開始處理。

---

## 2. Windows 用戶：實現類似 Apple 的生態圈

雖然 Windows 沒有內建的 iOS 捷徑，但您可以透過以下方式達成同樣的自動化效果：

### 方案 A：iCloud for Windows (推薦)
1.  從 Microsoft Store 安裝 **iCloud**。
2.  在手機端，依然使用上述的 **iOS 捷徑**。
3.  因為 iCloud 會在 Windows 電腦上建立一個虛擬硬碟，電腦端的 `FlashSquirrel` 只要監控 Windows 上的 iCloud 目錄即可。這對 iPhone + Windows 用戶最友好的方案。

### 方案 B：OneDrive / Google Drive / Dropbox
1.  在手機端安裝對應的 App（如 OneDrive）。
2.  將檔案分享到雲端硬碟的特定資料夾。
3.  在電腦端設定 `FlashSquirrel` 監控該雲端同步資料夾。

---

<a name="english"></a>

## 1. Apple (iOS) Users: Light-speed Capture via "Shortcuts"

For iPhone users, the most powerful method is to leverage the built-in "Shortcuts" app and seamless synchronization with iCloud Drive.

### Setup Steps:
1.  **Create Shortcut**:
    - Open the "Shortcuts" app on your iPhone.
    - Create a new shortcut named "Flash Research".
2.  **Add Actions**:
    - **Action 1: Create Folder**: Under the `input_thoughts` directory in iCloud Drive, create a new folder based on the current date/time.
    - **Action 2: Save File**: Save images, PDFs, or text passed from the "Share Sheet" into that folder.
3.  **How to Use**:
    - While browsing a web page or viewing a photo, tap "Share" -> "Flash Research".
    - `FlashSquirrel` on your computer will detect the iCloud sync and begin processing immediately.

---

## 2. Windows Users: Achieving the Same Ecosystem

While Windows doesn't have built-in iOS Shortcuts, you can achieve the same automation through the following methods:

### Option A: iCloud for Windows (Recommended)
1.  Install **iCloud** from the Microsoft Store.
2.  On your iPhone, continue using the **iOS Shortcuts** mentioned above.
3.  Since iCloud creates a virtual drive on your Windows PC, `FlashSquirrel` can simply monitor the iCloud directory on Windows. This is the best solution for iPhone + Windows users.

### Option B: OneDrive / Google Drive / Dropbox
1.  Install the corresponding app (e.g., OneDrive) on your smartphone.
2.  Share files to a specific folder in your cloud drive.
3.  Configure `FlashSquirrel` on your computer to monitor that synced cloud folder.

---

> *"Sync once, research everywhere."*
