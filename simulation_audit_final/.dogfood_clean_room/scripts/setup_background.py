#!/usr/bin/env python3
"""
FlashSquirrel Background Service Setup 🐿️🛡️
Automates 'Full-Automatic' (Invisble Shield) setup for Mac and Windows.
"""

import os
import sys
import platform
import subprocess
from pathlib import Path

def setup_mac():
    print("🍎 Setting up macOS LaunchAgent...")
    plist_template = Path("scripts/com.user.research_pipeline.plist.template")
    if not plist_template.exists():
        # Fallback to non-template for legacy support during migration
        plist_template = Path("scripts/com.user.research_pipeline.plist")
        
    if not plist_template.exists():
        print("❌ Error: Background service template not found.")
        return

    dest_path = Path.home() / "Library/LaunchAgents/com.flashsquirrel.agent.plist"
    
    # Read template and fill in paths
    with open(plist_template, "r") as f:
        content = f.read()
    
    # Get current paths (Dynamic Injection)
    project_root = os.getcwd()
    python_path = sys.executable
    
    # Precise replacement using tokens
    content = content.replace("{{PROJECT_ROOT}}", project_root)
    content = content.replace("{{VENV_PYTHON}}", python_path)
    
    # Legacy Fallback (for existing installs matching the creator's path)
    if "/Users/chenpeijun" in content:
        content = content.replace("/Users/chenpeijun/research_pipeline/.venv/bin/python3", python_path)
        content = content.replace("/Users/chenpeijun/Desktop/研究工作流", project_root)

    with open(dest_path, "w") as f:
        f.write(content)
    
    # Load the agent specifically for the current user session
    subprocess.run(["launchctl", "unload", str(dest_path)], capture_output=True)
    subprocess.run(["launchctl", "load", "-w", str(dest_path)], capture_output=True)
    
    # Verification using the exact label in the plist
    check_result = subprocess.run(["launchctl", "list", "com.flashsquirrel.agent"], capture_output=True)
    if check_result.returncode == 0:
        print(f"✅ Full-Auto enabled! FlashSquirrel is verified and running in the background.")
    else:
        print(f"⚠️ Service created but not yet active. (Wait for login or check permissions)")

    print(f"   (Service file created at: {dest_path})")
    print("\n" + "🚨" * 20)
    print("🍎 CRITICAL macOS PERMISSION REQUIRED (Full-Auto Mode):")
    print("FlashSquirrel runs in the background to monitor your iCloud/Folders.")
    print("It will fail SILENTLY if you don't grant permission:")
    print("\n1. Open System Settings -> Privacy & Security -> Full Disk Access.")
    print("2. Click the [+] button or find 'Terminal' (or your Code Editor).")
    print("3. Ensure the switch is ON.")
    print("4. Restart your Mac or log out/in to activate the background watcher.")
    print("🚨" * 20 + "\n")

def setup_windows():
    print("🪟 Setting up Windows Task Scheduler...")
    # We'll use a .vbs wrapper to run it hidden
    project_root = Path(os.getcwd()).absolute()
    vbs_path = project_root / "scripts/launch_hidden.vbs"
    python_exe = sys.executable
    script_path = project_root / "scripts/auto_research_pipeline.py"
    
    vbs_content = f'CreateObject("Wscript.Shell").Run "{python_exe} {script_path}", 0, False'
    
    with open(vbs_path, "w") as f:
        f.write(vbs_content)
    
    # Create task with schtasks
    task_name = "FlashSquirrel_AutoGuard"
    cmd = [
        "schtasks", "/Create", "/F", "/SC", "ONLOGON", 
        "/TN", task_name, 
        "/TR", f"wscript.exe \"{vbs_path}\"",
        "/RL", "HIGHEST"
    ]
    
    try:
        subprocess.check_call(cmd)
        print(f"✅ Full-Auto enabled! FlashSquirrel will guard your folders invisibly every time you log in.")
    except Exception as e:
        print(f"❌ Failed to create Windows task: {e}")
        print("Try running this script as Administrator.")

def main():
    print("\n" + "🛡️ " * 10)
    print("Welcome to Full-Auto Mode Setup!")
    print("🛡️ " * 10 + "\n")
    
    if platform.system() == "Darwin":
        setup_mac()
    elif platform.system() == "Windows":
        setup_windows()
    else:
        print("❌ Unsupported OS for automatic background setup.")

if __name__ == "__main__":
    main()
