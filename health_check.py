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
    print(f"{icon} {component:25}: {detail}")

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
    
    input_path = Path(root_dir) / "input_thoughts"
    exists = input_path.exists()
    print_status("Data Structure", exists, str(input_path) if exists else "Folders missing")
    return exists

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
        check_security()
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
