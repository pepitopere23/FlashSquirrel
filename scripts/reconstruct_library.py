import os
import sys
import json
import asyncio
import logging
from typing import List, Dict
import subprocess

# Configuration
ROOT_DIR = "/Users/chenpeijun/Library/Mobile Documents/com~apple~CloudDocs/研究工作流"
LOG_FILE = os.path.join(os.path.dirname(__file__), "reconstruction.log")
MAP_FILE = os.path.join(os.path.dirname(ROOT_DIR), ".notebook_map.json") # Check path logic, might need fix
# Fix MAP_FILE path to match pipeline
MAP_FILE = "/Users/chenpeijun/Desktop/研究工作流/.notebook_map.json"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s', filename=LOG_FILE, filemode='w')
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logging.getLogger('').addHandler(console)

def get_research_folders() -> List[str]:
    folders = []
    # 1. Check Root subfolders
    for item in os.listdir(ROOT_DIR):
        p = os.path.join(ROOT_DIR, item)
        if os.path.isdir(p) and item not in ["processed_reports", "docs", "scripts", "skills", "input_thoughts"]:
            # Check if it has content
            if any(f.endswith((".pdf", ".txt", ".md")) for f in os.listdir(p)):
                folders.append(p)
    
    # 2. Check input_thoughts
    input_thoughts = os.path.join(ROOT_DIR, "input_thoughts")
    if os.path.exists(input_thoughts):
        for item in os.listdir(input_thoughts):
            p = os.path.join(input_thoughts, item)
            if os.path.isdir(p):
                 if any(f.endswith((".pdf", ".txt", ".md")) for f in os.listdir(p)):
                    folders.append(p)
    return folders

async def reconstruct():
    print("🔥 Starting Phoenix Protocol: Library Reconstruction...")
    folders = get_research_folders()
    print(f"📦 Found {len(folders)} local research topics to rebuild.")
    
    # We must wipe the map file because the old IDs point to deleted notebooks
    if os.path.exists(MAP_FILE):
        print("🧹 Clearing invalid notebook map...")
        # Backup just in case
        os.rename(MAP_FILE, MAP_FILE + ".bak")
        with open(MAP_FILE, 'w') as f:
            json.dump({}, f)
            
    total = len(folders)
    for i, folder in enumerate(folders):
        topic = os.path.basename(folder)
        print(f"\n[{i+1}/{total}] 🏗️ Rebuilding: {topic}")
        
        # Determine what to upload
        # Priority: upload_package.md -> MASTER_SYNTHESIS.md -> report_*.md -> source files
        # Actually, let's just upload the 'best' file to initialize the notebook.
        # The automator usually handles 'upload_package.md' best.
        
        target_file = None
        # Look for upload package
        if os.path.exists(os.path.join(folder, "upload_package.md")):
            target_file = os.path.join(folder, "upload_package.md")
        elif os.path.exists(os.path.join(folder, "MASTER_SYNTHESIS.md")):
             target_file = os.path.join(folder, "MASTER_SYNTHESIS.md")
        else:
            # Find any report
            reports = [f for f in os.listdir(folder) if f.startswith("report_") and f.endswith(".md")]
            if reports:
                target_file = os.path.join(folder, reports[0])
            else:
                # Find any source text
                sources = [f for f in os.listdir(folder) if f.endswith((".txt", ".pdf"))]
                if sources:
                    target_file = os.path.join(folder, sources[0])
        
        if not target_file:
            print(f"⚠️ Skipping {topic} - No suitable source file found.")
            continue
            
        print(f"   📄 Uploading source: {os.path.basename(target_file)}")
        
        # Get Topic ID (ensure it exists)
        topic_id_file = os.path.join(folder, ".topic_id")
        topic_id = ""
        if os.path.exists(topic_id_file):
            with open(topic_id_file, 'r') as f: topic_id = f.read().strip()
        
        if not topic_id:
             import uuid
             topic_id = uuid.uuid4().hex[:8]
             with open(topic_id_file, 'w') as f: f.write(topic_id)

        # Call Automator
        # scripts/notebooklm_automator.py [file_path] [legacy_topic_name] [map_file] [topic_id]
        cmd = [
            sys.executable,
            "scripts/notebooklm_automator.py",
            target_file,
            topic,
            MAP_FILE,
            topic_id
        ]
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await process.communicate()
        output_str = stdout.decode()
        
        cloud_title = None
        for line in output_str.splitlines():
            if line.startswith("RESULT:"):
                cloud_title = line.split("RESULT:", 1)[1].strip()
                break

        if process.returncode == 0 and cloud_title:
            print(f"   ✅ Successfully Rebuilt: {cloud_title}")
            
            # --- SYNC RENAME START ---
            # Sanitize title
            safe_title = "".join([c for c in cloud_title if c.isalnum() or c in (" ", "_", "-", ".", "：", "，", "、", "（", "）", "「", "」")]).strip()
            
            # TITLE CORRECTION SAFETY NET
            # If NotebookLM returns "Untitled", DO NOT rename if we already have a better name.
            if "Untitled" in safe_title or "未命名" in safe_title:
                print(f"   ⚠️ Cloud returned generic title: '{safe_title}'. Keeping local name.")
            else:
                # Proceed with rename
                if not safe_title: safe_title = f"Reconstructed_{topic_id}"
                new_path = os.path.join(ROOT_DIR, safe_title)
                
                if new_path != folder and os.path.abspath(new_path) != os.path.abspath(folder):
                    try:
                        if os.path.exists(new_path):
                            print(f"   ⚠️ Destination exists: {safe_title}. Appending ID.")
                            new_path = os.path.join(ROOT_DIR, f"{safe_title}_{topic_id}")
                        os.rename(folder, new_path)
                        print(f"   🔄 Synced local folder name: {os.path.basename(folder)} -> {safe_title}")
                    except OSError as e:
                        print(f"   ⚠️ Rename failed: {e}")
            # --- SYNC RENAME END ---

        else:
            print(f"   ❌ Failed to rebuild {topic}")
            print(f"      Error: {stderr.decode().strip()}")
            if "RESULT:" in output_str:
                 print(f"      Partial Output: {cloud_title}")

    print("\n✅ Phoenix Protocol Complete. Local Library has been mirrored to NotebookLM.")

if __name__ == "__main__":
    asyncio.run(reconstruct())
