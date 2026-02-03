#!/usr/bin/env python3
import os
import sys
import asyncio
import logging

# Configuration
ROOT_DIR = os.path.expanduser("~/Library/Mobile Documents/com~apple~CloudDocs/研究工作流")
AUTOMATOR_SCRIPT = os.path.join(os.path.dirname(__file__), "notebooklm_automator.py")
PYTHON_EXE = sys.executable

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

async def force_sync():
    logging.info("🚀 Starting Manual Sync of historical folders...")
    
    map_file = os.path.join(ROOT_DIR, ".notebook_map.json")

    for root, dirs, files in os.walk(ROOT_DIR):
        if "upload_package.md" in files:
            folder_path = root
            package_path = os.path.join(root, "upload_package.md")
            topic = os.path.basename(folder_path)
            
            # Simple ID generation for mapping
            import hashlib
            topic_id = hashlib.md5(topic.encode()).hexdigest()[:8]
            
            logging.info(f"📤 Pushing folder: {topic} (ID: {topic_id})")
            
            # FIXED: Pass ALL arguments (Map File + Topic ID) so the automator can use its full logic
            proc = await asyncio.create_subprocess_exec(
                PYTHON_EXE, AUTOMATOR_SCRIPT, package_path, topic, map_file, topic_id,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            
            # Check for success and semantic renaming
            output = stdout.decode().strip()
            # Parse the output for the "RESULT:" line
            new_topic = None
            lines = output.split('\n')
            for line in lines:
                if line.startswith("RESULT:"):
                    new_topic = line.replace("RESULT:", "").strip()
            
            # 🛡️ Safety Logic: Only rename if we got a VALID name (not Untitled)
            if new_topic and new_topic != topic and "Untitled" not in new_topic and "未命名" not in new_topic:
                 logging.info(f"🏷️ Semantic Refinement Detected: {topic} -> {new_topic}")
                 try:
                     new_folder_path = os.path.join(os.path.dirname(folder_path), new_topic)
                     os.rename(folder_path, new_folder_path)
                     logging.info(f"✅ Local Folder Renamed: {new_topic}")
                 except Exception as e:
                     logging.error(f"⚠️ Rename failed (Locked?): {e}")

            if proc.returncode == 0:
                logging.info(f"✅ Successfully synced: {topic}")
            else:
                logging.error(f"❌ Failed to sync {topic}: {stderr.decode()}")

if __name__ == "__main__":
    asyncio.run(force_sync())
