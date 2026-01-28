#!/usr/bin/env python3
import os
import re
from pathlib import Path

ROOT_DIR = os.path.expanduser("~/Library/Mobile Documents/com~apple~CloudDocs/研究工作流")

def get_real_title(folder_path):
    # Try MASTER_SYNTHESIS.md first
    ms = os.path.join(folder_path, "MASTER_SYNTHESIS.md")
    if os.path.exists(ms):
        with open(ms, 'r', encoding='utf-8') as f:
            first_line = f.readline()
            if first_line.startswith("# "):
                title = first_line.replace("# Master Synthesis:", "").replace("#", "").strip()
                if "2026年" not in title and title:
                    return title
    
    # Try report_*.md
    for f in os.listdir(folder_path):
        if f.startswith("report_") and f.endswith(".md"):
            with open(os.path.join(folder_path, f), 'r', encoding='utf-8') as rf:
                for line in rf:
                    if line.startswith("# Study Title:"):
                        return line.replace("# Study Title:", "").strip()
                    if line.startswith("# "):
                        return line.replace("#", "").strip()
    return None

def cleanup():
    print(f"🛠️ Starting Emergency Renaming Cleanup in: {ROOT_DIR}")
    for item in os.listdir(ROOT_DIR):
        item_path = os.path.join(ROOT_DIR, item)
        if not os.path.isdir(item_path) or item == ".gemini" or item == "input_thoughts":
            continue
            
        # Detect messy folder names
        if "🚀" in item or "DONE_Untitled" in item or item.count("DONE_") > 1:
            print(f"⚠️ Found messy folder: {item}")
            
            real_title = get_real_title(item_path)
            if not real_title or "Untitled" in real_title:
                # Try to extract the date part if it's there
                date_match = re.search(r"(\d{4}年\d{1,2}月\d{1,2}日.*?\d{2}:\d{2}:\d{2})", item)
                if date_match:
                    new_name = f"PENDING_{date_match.group(1).replace('/', '_')}"
                else:
                    new_name = f"REPAIR_NEEDED_{item[:20]}"
            else:
                new_name = f"DONE_{real_title}"
            
            # Final touch: Clean up illegal characters
            new_name = "".join([c for c in new_name if c not in '<>:"/\\|?*']).strip()
            
            new_path = os.path.join(ROOT_DIR, new_name)
            if new_path != item_path:
                try:
                    os.rename(item_path, new_path)
                    print(f"✅ Repaired: {item} -> {new_name}")
                except Exception as e:
                    print(f"❌ Failed to rename: {e}")

if __name__ == "__main__":
    cleanup()
