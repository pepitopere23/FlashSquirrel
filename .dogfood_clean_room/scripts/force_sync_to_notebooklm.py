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
    
    for root, dirs, files in os.walk(ROOT_DIR):
        if "upload_package.md" in files:
            folder_path = root
            package_path = os.path.join(root, "upload_package.md")
            topic = os.path.basename(folder_path)
            
            logging.info(f"📤 Pushing folder: {topic}")
            
            proc = await asyncio.create_subprocess_exec(
                PYTHON_EXE, AUTOMATOR_SCRIPT, package_path, topic,
                stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
            )
            stdout, stderr = await proc.communicate()
            
            # Check for success and semantic renaming
            output = stdout.decode().strip()
            new_topic = output.split('\n')[-1]
            
            if new_topic and new_topic != topic and "Success" not in new_topic and "Error" not in new_topic:
                 logging.info(f"🏷️ Semantic Refinement: {topic} -> {new_topic}")
                 # Note: We won't rename here to avoid breaking the walk, 
                 # the main daemon can handle re-syncing if needed.
            
            if proc.returncode == 0:
                logging.info(f"✅ Successfully synced: {topic}")
            else:
                logging.error(f"❌ Failed to sync {topic}: {stderr.decode()}")

if __name__ == "__main__":
    asyncio.run(force_sync())
