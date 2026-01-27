#!/usr/bin/env python3
"""
FlashSquirrel Health Check 🐿️💪
Ensures the system is "healthy as an ox" and ready for research.
"""

import os
import sys
import platform
import subprocess
from pathlib import Path

def print_status(component, status, detail=""):
    icon = "✅" if status else "❌"
    color_start = "\033[92m" if status else "\033[91m"
    color_end = "\033[0m"
    print(f"{icon} {component:25}: {color_start}{detail}{color_end}")

def check_python():
    version = sys.version.split()[0]
    is_valid = sys.version_info >= (3, 9)
    print_status("Python Version", is_valid, version)
    return is_valid

def check_env():
    has_env = os.path.exists(".env")
    if has_env:
        with open(".env", "r") as f:
            content = f.read()
            has_key = "GEMINI_API_KEY=" in content and "your_api_key_here" not in content
            print_status(".env Configuration", has_key, "API Key detected" if has_key else "Missing/Default Key")
            return has_key
    else:
        print_status(".env Configuration", False, "File missing")
        return False

def check_auth():
    auth_file = Path.home() / ".notebooklm-mcp" / "auth.json"
    has_auth = auth_file.exists()
    print_status("NotebookLM Auth", has_auth, "Logged in" if has_auth else "Session missing")
    return has_auth

def check_dirs():
    # Detect root dir from .env if possible
    root_dir = os.getcwd()
    if os.path.exists(".env"):
        with open(".env", "r") as f:
            for line in f:
                if line.startswith("RESEARCH_ROOT_DIR="):
                    root_dir = line.split("=", 1)[1].strip()
                    break
    
    root_name = os.path.basename(root_dir)
    is_standard = root_name in ["研究工作流", "research_pipeline"] or "研究工作流" in str(root_dir)
    input_path = Path(root_dir) / "input_thoughts"
    exists = input_path.exists()
    
    print_status("Detected Root", True, str(root_dir))
    print_status("Path Consistency", is_standard, "Matches '研究工作流'" if is_standard else f"Warning: {root_name}")
    print_status("Data Structure", exists, "OK" if exists else "Folders missing")
    return exists and is_standard

def check_background_service():
    if platform.system() == "Darwin":
        plist = Path.home() / "Library/LaunchAgents/com.flashsquirrel.agent.plist"
        exists = plist.exists()
        label = "com.flashsquirrel.agent"
        # Check if loaded
        loaded = subprocess.run(["launchctl", "list", label], capture_output=True).returncode == 0
        print_status("Background Service", loaded, "Active (LaunchAgent)" if loaded else ("Installed but not running" if exists else "Not Installed"))
        return loaded
    elif platform.system() == "Windows":
        try:
            output = subprocess.check_output(["schtasks", "/Query", "/TN", "FlashSquirrel_AutoGuard"], stderr=subprocess.DEVNULL)
            exists = b"FlashSquirrel_AutoGuard" in output
            print_status("Background Service", exists, "Active (Task Scheduler)" if exists else "Not Installed")
            return exists
        except:
            print_status("Background Service", False, "Not Installed")
            return False
    return True

def check_17_layers():
    print("\n🛡️  Running 17-Layer Code Integrity Audit...")
    try:
        sys.path.append(os.path.join(os.getcwd(), "scripts"))
        from validation_17_layers import validate_code_17_layers
        
        core_files = ["scripts/auto_research_pipeline.py", "start.py"]
        all_passed = True
        
        for file_path in core_files:
            if os.path.exists(file_path):
                with open(file_path, "r") as f:
                    code = f.read()
                result = validate_code_17_layers(code, file_path)
                score = result['quality_score']
                is_ok = score >= 80
                print_status(f"Layer Audit: {os.path.basename(file_path)}", is_ok, f"{score}/100")
                if not is_ok:
                    all_passed = False
                    print(f"   💡 Suggestions for {os.path.basename(file_path)}:")
                    for s in result.get('suggestions', []):
                        print(f"      - {s}")
        return all_passed
    except Exception as e:
        print_status("Layer Audit", False, f"Failed to run: {e}")
        return False

def check_security():
    # Passive security check: ensure no sensitive files are tracked by git
    try:
        result = subprocess.check_output(["git", "ls-files", ".env", "auth.json"], stderr=subprocess.DEVNULL)
        leaked = result.decode().strip()
        is_safe = not leaked
        print_status("Privacy Shield", is_safe, "Safe" if is_safe else f"WARNING: {leaked} is tracked!")
        return is_safe
    except:
        return True

def main():
    print("\n" + "🐿️  " * 10)
    print("FlashSquirrel System Health Check")
    print("🐿️  " * 10 + "\n")

    results = [
        check_python(),
        check_env(),
        check_auth(),
        check_dirs(),
        check_background_service(),
        check_security(),
        check_17_layers()
    ]

    print("\n" + "-"*40)
    if all(results):
        print("🌟 閃電松鼠壯得像頭牛！")
        print("   (FlashSquirrel is as strong as an ox!)")
        print("\nYour system is 100% ready for high-speed research.")
    else:
        print("⚠️  System needs attention.")
        print("Please run `python start.py` to fix missing components.")
    print("-"*40 + "\n")

if __name__ == "__main__":
    main()
