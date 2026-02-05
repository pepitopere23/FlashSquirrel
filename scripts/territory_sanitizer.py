
import os
import shutil
import logging

# Configure logging to be very explicit for the user
logging.basicConfig(level=logging.INFO, format='%(asctime)s - 🛡️ SANITIZER - %(message)s')

# Normalize Root Directory handling for portability
DEFAULT_MAC_ICLOUD = os.path.expanduser("~/Library/Mobile Documents/com~apple~CloudDocs/研究工作流")
ROOT_DIR = os.getenv("RESEARCH_ROOT_DIR") or DEFAULT_MAC_ICLOUD

def sanitize_territory():
    """
    Scans the iCloud research root for folders with illegal characters (like \n)
    and renames them safely while preserving internal .topic_id files.
    """
    if not os.path.exists(ROOT_DIR):
        logging.error(f"Root dir not found: {ROOT_DIR}")
        return

    logging.info(f"🚀 Starting Sanitation on: {ROOT_DIR}")
    
    # 1. Broad Scan
    all_items = os.listdir(ROOT_DIR)
    mangled_count = 0
    
    for item in all_items:
        full_path = os.path.join(ROOT_DIR, item)
        
        # We only care about directories in 'input_thoughts' or root
        if not os.path.isdir(full_path):
            continue
            
        # Detect mangled names: Newlines, carriage returns, or extremely suspicious long strings of dates
        is_mangled = False
        if "\n" in item or "\r" in item:
            is_mangled = True
        
        # Check for the specific "multiple date stack" pattern we saw in forensics
        if item.count("202") > 2: # e.g., 2026-01-27\n2026-01-28...
             is_mangled = True
             
        if is_mangled:
            logging.warning(f"⚠️ Mangled folder detected: {repr(item)}")
            
            # Create a clean name: Replace all \n with _ and trim
            clean_name = item.replace("\n", "_").replace("\r", "_").strip()
            # If still messy, just use a timestamp fallback to preserve content
            if not clean_name or clean_name == item:
                import time
                clean_name = f"recovered_folder_{int(time.time())}"
            
            new_path = os.path.join(ROOT_DIR, clean_name)
            
            # Collision guard
            if os.path.exists(new_path):
                import uuid
                clean_name = f"{clean_name}_{uuid.uuid4().hex[:4]}"
                new_path = os.path.join(ROOT_DIR, clean_name)

            try:
                os.rename(full_path, new_path)
                logging.info(f"✅ RECOVERED: {repr(item)} -> {clean_name}")
                mangled_count += 1
            except Exception as e:
                logging.error(f"❌ Failed to rename {repr(item)}: {e}")

    logging.info(f"✨ Sanitation finished. Total mangled folders fixed: {mangled_count}")

if __name__ == "__main__":
    sanitize_territory()
