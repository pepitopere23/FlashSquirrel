import shutil
import os

src = "/Users/chenpeijun/Library/Mobile Documents/com~apple~CloudDocs/研究工作流/_QUARANTINE_/Critical_Error/如果我搞一個就是占卜 就是不管是塔羅還是什麼 然後一個日曆跟日記那種 他可以單點分析跟鏈式分析的 （雖然我不懂 這個 然後可以線上抽牌 也可以導入結果  ）不知道 這樣好玩嗎.txt"
dst = "/Users/chenpeijun/Library/Mobile Documents/com~apple~CloudDocs/研究工作流/input_thoughts/如果我搞一個就是占卜_RESCUED.txt"

if os.path.exists(src):
    shutil.move(src, dst)
    print("✅ Rescued file back to input!")
else:
    print("❌ Source file not found.")
