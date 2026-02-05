
import os
import sys

ROOT_DIR = os.path.expanduser("~/Library/Mobile Documents/com~apple~CloudDocs/研究工作流")

def should_ignore(file_path):
    basename = os.path.basename(file_path)
    if basename.startswith('.') or file_path.endswith('.py'): return True
    root_parts = os.path.relpath(file_path, ROOT_DIR).split(os.sep)
    if any(p in ["processed_reports", "docs", "scripts", "skills", "chrome_profile_notebooklm"] for p in root_parts): 
        return True
    ignore_patterns = (
        "report_", "visualizations", "MASTER_SYNTHESIS", 
        "upload_package", "RESEARCH_FAILURE_", "RESEARCH_SUSPENDED_",
        "mindmap_", "slide_", ".research_lock", ".topic_id", ".DS_Store"
    )
    if any(p in basename for p in ignore_patterns): return True
    return False

found = []
for root, dirs, files in os.walk(ROOT_DIR):
    for file in files:
        file_path = os.path.join(root, file)
        if should_ignore(file_path):
            continue
        
        stem = os.path.splitext(file)[0]
        report_name = f"report_{stem}.md"
        failure_name = f"RESEARCH_FAILURE_{stem}.md"
        
        if os.path.exists(os.path.join(root, report_name)) or os.path.exists(os.path.join(root, failure_name)):
            continue

        found.append(file_path)

print(f"FOUND {len(found)} FILES")
for f in found[:20]:
    print(f)
