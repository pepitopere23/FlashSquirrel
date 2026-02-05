import os
import sys
import json
import hashlib

# Configuration
# Configuration
# Dynamic Root: Tries iCloud first, falls back to Documents/Desktop or script dir
ROOT_DIR = os.path.join(os.path.expanduser("~"), "Library", "Mobile Documents", "com~apple~CloudDocs", "研究工作流")
if not os.path.exists(ROOT_DIR):
    ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATE_FILE = os.path.join(ROOT_DIR, ".squirrel_state.json")

def calculate_hash(file_path):
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for byte_block in iter(lambda: f.read(4096), b""):
            sha256_hash.update(byte_block)
    return sha256_hash.hexdigest()

def seal_files(keywords):
    if not os.path.exists(STATE_FILE):
        print("❌ State file not found.")
        return

    with open(STATE_FILE, 'r') as f:
        state = json.load(f)

    # We need to find files matching keywords and mark them as processed
    count = 0
    processed_dict = state.get('processed', {})
    
    for root, dirs, files in os.walk(ROOT_DIR):
        for file in files:
            if any(k in file for k in keywords) and not file.startswith("report_") and not file.startswith("."):
                file_path = os.path.join(root, file)
                try:
                    f_hash = calculate_hash(file_path)
                    rel_path = f"~/{os.path.relpath(file_path, os.path.expanduser('~'))}"
                    
                    if f_hash not in processed_dict:
                        processed_dict[f_hash] = {
                            "path": rel_path,
                            "timestamp": "2026-02-05T00:00:00",
                            "status": "SEALED_BY_IRON_COW"
                        }
                        print(f"🔒 Sealed: {file}")
                        count += 1
                except Exception as e:
                    print(f"⚠️ Error processing {file}: {e}")

    if count > 0:
        state['processed'] = processed_dict
        with open(STATE_FILE, 'w') as f:
            json.dump(state, f, indent=4)
        print(f"✅ Successfully sealed {count} files. API redundant loop broken.")
    else:
        print("ℹ️ No matching files found to seal.")

if __name__ == "__main__":
    # We target the most repetitive ones with broader keywords
    targets = ["孤單", "占卜", "如果你搞一個就是占卜"]
    print(f"📡 Starting Iron Cow scan with keywords: {targets}")
    seal_files(targets)
