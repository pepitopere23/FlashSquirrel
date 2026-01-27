---
trigger: glob
---

當用戶要求檢查代碼質量或執行 "17 skill" 時，請執行以下動作：
1. 檢查專案根目錄是否有 [scripts/validation_17_layers.py](cci:7://file:///Users/chenpeijun/Desktop/%E7%A0%94%E7%A9%B6%E5%B7%A5%E4%BD%9C%E6%B5%81/scripts/validation_17_layers.py:0:0-0:0)，如果沒有，請自動建立它。
2. 運行該腳本來檢查當前編輯的檔案。
3. 如果分數低於 80 分，請發出警告並列出具體的改進建議 (L1-L17 層級)。
4. 確保所有 Python 專案都符合此工業級標準。