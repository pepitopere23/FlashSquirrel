import os
import hashlib
import re
from datetime import datetime

# Root Directory (iCloud Mac default)
# Root Directory (iCloud Mac default) # TODO: Make cross-platform for Windows
ROOT_DIR = os.path.join(os.path.expanduser("~"), "Library", "Mobile Documents", "com~apple~CloudDocs", "研究工作流")
if not os.path.exists(ROOT_DIR): # Fallback for Windows/Standard
    ROOT_DIR = os.path.join(os.path.expanduser("~"), "Desktop", "研究工作流")

REPORT_PATH = os.path.join(os.path.dirname(__file__), "..", "PURGE_LIST.md")

# JUNK Patterns (Naming Fog Variations)
JUNK_PATTERNS = [
    r"\.[rt]\s?[0-9]+",       # .r 5, .t 12, .r45
    r"\.rea(son)?(\s?[0-9]+)?", # .rea, .reason, .rea 5
    r"\.bak$",                # .bak files
    r" \(副本 [0-9]+\)",      # iCloud Duplicates
]

def get_file_hash(path):
    """Simple MD5 hash for duplicate detection."""
    try:
        hasher = hashlib.md5()
        with open(path, 'rb') as f:
            buf = f.read(65536)
            while len(buf) > 0:
                hasher.update(buf)
                buf = f.read(65536)
        return hasher.hexdigest()
    except:
        return None

def scan():
    print(f"🔦 Starting Surgical Scan in: {ROOT_DIR}...")
    
    junk_list = []
    dupe_map = {} # hash -> list of paths
    safe_count = 0
    
    for root, dirs, files in os.walk(ROOT_DIR):
        # Ignore engine-internal folders (already safe)
        if "_QUARANTINE_" in root or ".gemini" in root:
            continue
            
        for file in files:
            file_path = os.path.join(root, file)
            is_junk = False
            
            # 1. Pattern Matching (Known Junk)
            for pattern in JUNK_PATTERNS:
                if re.search(pattern, file, re.IGNORECASE):
                    junk_list.append((file_path, "Naming Relic (Naming Loop Variant)"))
                    is_junk = True
                    break
            
            if is_junk: continue
            
            # 2. Duplicate Detection (The "Hidden" Camouflage)
            f_hash = get_file_hash(file_path)
            if f_hash:
                if f_hash not in dupe_map:
                    dupe_map[f_hash] = []
                dupe_map[f_hash].append(file_path)
            
            safe_count += 1

    # Filter actual duplicates
    actual_dupes = {h: paths for h, paths in dupe_map.items() if len(paths) > 1}
    
    # Generate Report
    with open(REPORT_PATH, 'w') as f:
        f.write(f"# 🧹 FlashSquirrel: 外科手術查殺名單 (V17 Audit)\n\n")
        f.write(f"> 生成時間: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        f.write(f"## 📊 掃描概覽\n")
        f.write(f"* 找到顯性垃圾: {len(junk_list)} 個\n")
        f.write(f"* 找到內容重複組: {len(actual_dupes)} 組\n")
        f.write(f"* 正常數據量: {safe_count} 個\n\n")
        
        f.write(f"## 🔴 建議清理：顯性垃圾 (後綴殘留)\n")
        f.write(f"這些檔案帶有 `.t`、`.r`、`.rea` 等錯誤後綴。\n\n")
        for path, reason in junk_list[:100]: # Limit report size
            rel_path = os.path.relpath(path, ROOT_DIR)
            f.write(f"- [ ] `{rel_path}` ({reason})\n")
        if len(junk_list) > 100:
            f.write(f"- ... 及其他 {len(junk_list)-100} 個檔案\n")
            
        f.write(f"\n## 🟡 疑慮清單：內容重複 (影分身鑑定)\n")
        f.write(f"這些檔案名字「看起來很正經」，但內容哈希值 100% 一致。建議保留一個，刪除其餘。\n\n")
        for h, paths in list(actual_dupes.items())[:50]:
            f.write(f"### 組別 {h[:8]}\n")
            for p in paths:
                rel_path = os.path.relpath(p, ROOT_DIR)
                f.write(f"- [ ] `{rel_path}`\n")
            f.write("\n")
            
    print(f"✅ Report generated at: {REPORT_PATH}")

if __name__ == "__main__":
    scan()
