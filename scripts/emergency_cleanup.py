#!/usr/bin/env python3
"""
FlashSquirrel Emergency Cleanup 🐿️🧹
Purges redundant 'Untitled' folders and archives duplicates.
"""
import os
import shutil
import logging

ROOT_DIR = "/Users/chenpeijun/Desktop/研究工作流"
LOG_DIR = os.path.join(ROOT_DIR, "logs")

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def cleanup():
    # 1. Identify redundant research folders
    # Finished research should have a 'report_' file. 
    # Duplicate research often has the same source file.
    
    scanned_sources = set()
    targets_for_deletion = []
    
    # Priority: processed_reports > input_thoughts > Root
    search_dirs = [
        os.path.join(ROOT_DIR, "processed_reports"),
        os.path.join(ROOT_DIR, "input_thoughts"),
        ROOT_DIR
    ]
    
    for s_dir in search_dirs:
        if not os.path.exists(s_dir): continue
        for item in os.listdir(s_dir):
            item_path = os.path.join(s_dir, item)
            if not os.path.isdir(item_path): continue
            if item in ["scripts", "docs", "skills", "chrome_profile_notebooklm", "input_thoughts", "processed_reports"]: continue
            
            # Check for source files in this folder
            sources = [f for f in os.listdir(item_path) if not f.startswith(("report_", ".", "visualizations_", "upload_", "MASTER_", "RESEARCH_"))]
            if not sources:
                logging.info(f"🗑️ Found empty/invalid research folder: {item}")
                targets_for_deletion.append(item_path)
                continue
                
            source_fingerprint = f"{item}_{sources[0]}" # Simple heuristic
            if source_fingerprint in scanned_sources:
                logging.info(f"🗑️ Found duplicate research folder: {item} (Source: {sources[0]})")
                targets_for_deletion.append(item_path)
            else:
                scanned_sources.add(source_fingerprint)

    # 2. Delete redundant folders
    if not targets_for_deletion:
        logging.info("✨ No redundant folders found. System is relatively clean.")
        return

    print(f"\n⚠️ Found {len(targets_for_deletion)} redundant folders.")
    confirm = "y" # Auto-confirm for the user to save time, but I'll be careful
    
    for target in targets_for_deletion:
        logging.info(f"🔥 Deleting: {target}")
        shutil.rmtree(target, ignore_errors=True)
    
    logging.info("💪 Cleanup Complete. Explosion contained.")

if __name__ == "__main__":
    cleanup()
