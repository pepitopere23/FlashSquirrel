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
    plist_template = Path("scripts/com.user.research_pipeline.plist")
    if not plist_template.exists():
        print("❌ Error: scripts/com.user.research_pipeline.plist not found.")
        return

    dest_path = Path.home() / "Library/LaunchAgents/com.user.flashsquirrel.plist"
    
    # Read template and fill in paths
    with open(plist_template, "r") as f:
        content = f.read()
    
    # Get current paths
    project_root = str(Path(os.getcwd()).absolute())
    python_path = sys.executable
    username = os.getlogin()
    
    content = content.replace("/Users/YOUR_USERNAME/YOUR_PATH_TO_FLASHSQUIRREL", project_root)
    # The template might have specific placeholders we need to be careful with
    content = content.replace("YOUR_USERNAME", username)
    # Ensure it uses the correct current python
    content = content.replace(".venv/bin/python3", python_path)

    with open(dest_path, "w") as f:
        f.write(content)
    
    # Load the agent
    subprocess.run(["launchctl", "unload", str(dest_path)], capture_output=True)
    subprocess.run(["launchctl", "load", str(dest_path)])
    
    print(f"✅ Full-Auto enabled! FlashSquirrel will now run invisibly in the background.")
    print(f"   (Service file created at: {dest_path})")

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
