import shutil
import os

# Dynamic Root
ROOT_DIR = os.path.join(os.path.expanduser("~"), "Library", "Mobile Documents", "com~apple~CloudDocs", "研究工作流")
if not os.path.exists(ROOT_DIR):
    ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

src = os.path.join(ROOT_DIR, "_QUARANTINE_", "Critical_Error", "如果我搞一個就是占卜 就是不管是塔羅還是什麼 然後一個日曆跟日記那種 他可以單點分析跟鏈式分析的 （雖然我不懂 這個 然後可以線上抽牌 也可以導入結果  ）不知道 這樣好玩嗎.txt")
dst = os.path.join(ROOT_DIR, "input_thoughts", "如果我搞一個就是占卜_RESCUED.txt")

if os.path.exists(src):
    shutil.move(src, dst)
    print("✅ Rescued file back to input!")
else:
    print("❌ Source file not found.")
