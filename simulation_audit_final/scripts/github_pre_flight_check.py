import os
import re
import sys

# Configuration
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
try:
    import getpass
    CURRENT_USER = getpass.getuser()
except:
    CURRENT_USER = "UNKNOWN_USER"

FORBIDDEN_PATTERNS = [
    (r"/Users/(?!yourname|username)[a-zA-Z0-9]+", "⚠️ Hardcoded User Path (Potentially PII)"),
    (rf"{CURRENT_USER}", "🚨 Specific PII Leak (Your Username Found!)"),
    (r"shutil\.rmtree", "⚠️ Recursive Deletion (Verify Safety)"),
    (r"os\.remove", "⚠️ File Deletion (Verify Safety)"),
    (r"GEMINI_API_KEY\s*=\s*['\"]AI", "⚠️ Exposed API Key")
]

IGNORE_DIRS = [".git", ".venv", "__pycache__", "processed_reports", ".agent", ".gemini"]
IGNORE_FILES = ["github_pre_flight_check.py", ".DS_Store", "reconstruction.log", "pipeline.log", "pipeline_error.log", "pipeline_bg.log", ".env"]

def audit_codebase():
    print(f"🚀 Starting GitHub Pre-Flight Audit...")
    print(f"📂 Scanning Root: {ROOT_DIR}\n")
    
    issues_found = 0
    
    for root, dirs, files in os.walk(ROOT_DIR):
        # Filter directories
        dirs[:] = [d for d in dirs if d not in IGNORE_DIRS]
        
        for file in files:
            if file in IGNORE_FILES: continue
            if file.endswith((".pyc", ".png", ".jpg", ".zip")): continue
            
            check_file(os.path.join(root, file), issues_found)

def check_file(filepath, counter):
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            lines = content.splitlines()
            
            rel_path = os.path.relpath(filepath, ROOT_DIR)
            file_issues = []
            
            for i, line in enumerate(lines):
                for pattern, msg in FORBIDDEN_PATTERNS:
                    if re.search(pattern, line):
                        # Context awareness: Ignore if it's in a comment? Maybe not, strict mode.
                        # Exclude self-references in this script or log files if accidentaly scanned
                        file_issues.append(f"   L{i+1}: {msg} -> {line.strip()[:60]}...")
            
            if file_issues:
                print(f"🚩 Issue in: {rel_path}")
                for issue in file_issues:
                    print(issue)
                print("")

    except Exception as e:
        print(f"❌ Error reading {filepath}: {e}")

if __name__ == "__main__":
    audit_codebase()
