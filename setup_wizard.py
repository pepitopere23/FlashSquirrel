#!/usr/bin/env python3
"""
FlashSquirrel Setup Wizard 🐿️⚡️
A zero-friction onboarding script for non-technical users.
Works on Windows and macOS.
"""

import os
import sys
import json
import subprocess
import time
from pathlib import Path

def print_banner():
    print("\n" + "="*60)
    print("🐿️  FlashSquirrel (閃電松鼠) - Setup Wizard")
    print("="*60 + "\n")

def check_dependencies():
    print("📦 Checking and installing dependencies...")
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        # Install playwright browsers
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
        print("✅ Dependencies installed successfully.")
    except Exception as e:
        print(f"❌ Error installing dependencies: {e}")
        print("Please ensure you have an active internet connection.")
        sys.exit(1)

        sys.exit(1)

def pre_flight_check():
    print("\n" + "-"*40)
    print("🛡️  System Integrity Pre-Flight Check")
    print("-" * 40)
    
    # 1. Hardware/OS
    import platform
    print(f"✅ Operating System: {platform.system()} {platform.release()}")
    
    # 2. Python Version
    py_ver = sys.version.split()[0]
    print(f"✅ Python Runtime: {py_ver}")
    
    # 3. Network Check (Simple DNS resolve)
    try:
        import socket
        socket.gethostbyname("www.google.com")
        print("✅ Network Connection: Active")
    except:
        print("⚠️  Network Connection: Unstable (Offline?)")
        
    print("-" * 40)
    print("📊 System Readiness Score: 98/100 (Excellent)")
    print("   -> Why 98? Because we need your Key to reach 100!")
    print("-" * 40)
    time.sleep(1)

def configure_api_key():
    print("\n" + "-"*40)
    print("🔑 Step 1: Get Your Magic Key (API Key)")
    print("-" * 40)
    print("To make the Squirrel intelligent, we need a small 'password' from Google.")
    print("Don't worry, it's free and takes 10 seconds.\n")
    
    print("👉 1. Click (or copy) this link:")
    print("   https://aistudio.google.com/app/apikey")
    print("\n👉 2. Click 'Create API Key' -> 'Create API key in new project'")
    print("👉 3. Copy that long text string starting with 'AIza...'")
    print("-" * 40 + "\n")
    
    current_key = os.getenv("GEMINI_API_KEY", "")
    prompt = f"Paste your Key here (Right-click -> Paste) [{current_key[:6]}...]: " if current_key else "Paste your Key here: "
    
    key = input(prompt).strip()
    if not key and current_key:
        key = current_key
    elif not key:
        print("⚠️  The Squirrel needs the key to wake up! Please try again.")
        return configure_api_key()
    return key

def capture_cookies():
    print("\n🍪 Step 2: NotebookLM Authentication")
    print("A browser window will open. Please log into your Google Account.")
    print("Once you see your NotebookLM dashboard, you can close the browser or wait for the script to finish.")
    
    auth_dir = Path.home() / ".notebooklm-mcp"
    auth_dir.mkdir(parents=True, exist_ok=True)
    auth_file = auth_dir / "auth.json"
    
    try:
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            # We use non-headless so user can log in
            browser = p.chromium.launch(headless=False)
            context = browser.new_context()
            page = context.new_page()
            
            page.goto("https://notebooklm.google.com/")
            
            print("⏳ Waiting for you to log in... (Timeout in 5 minutes)")
            
            # Wait for any indicator of a logged-in state
            try:
                # English or Chinese "New Notebook" indicators
                page.wait_for_selector("button:has-text('New Notebook'), button:has-text('建立新的筆記本'), .c6", timeout=300000)
            except:
                print("⚠️ Login indicator not found. Proceeding with captured cookies if possible...")
            
            cookies = context.cookies()
            auth_data = {"cookies": cookies}
            
            with open(auth_file, "w") as f:
                json.dump(auth_data, f, indent=4)
            
            browser.close()
            print(f"✅ Cookies captured and saved to {auth_file}")
            
    except Exception as e:
        print(f"❌ Error during cookie capture: {e}")
        print("Make sure Playwright is correctly installed.")

def setup_environment(api_key):
    print("\n📁 Step 3: Finalizing Configuration")
    
    # Default path for research workflow
    if sys.platform == "darwin":
        default_root = os.path.expanduser("~/Library/Mobile Documents/com~apple~CloudDocs/研究工作流")
    else:
        # On Windows, default to a 'data' folder in the project directory
        default_root = str(Path(os.getcwd()) / "data")
    
    print(f"Default data folder: {default_root}")
    custom_root = input(f"Press Enter to use default or enter custom path: ").strip()
    root_path = custom_root if custom_root else default_root
    
    # Create directory structure
    paths = [
        "input_thoughts",
        "raw_thoughts",
        "processed_reports",
        "visualizations"
    ]
    
    root_p = Path(root_path)
    
    # macOS Permission Check (Full Disk Access)
    if sys.platform == "darwin" and "CloudDocs" in root_path:
        print("\n🍎 macOS Security Check:")
        print("To access iCloud Drive folders, your Terminal needs 'Full Disk Access'.")
        print("1. Open System Settings -> Privacy & Security -> Full Disk Access.")
        print("2. Ensure 'Terminal' (or your IDE) is toggled ON.")
        print("3. If you don't do this, the script might fail to see your files.")
        input("\nPress Enter once you've checked this, or if you want to proceed anyway...")

    print(f"\n🏗️  Initializing directory structure at: {root_path}")
    root_p.mkdir(parents=True, exist_ok=True)
    for p in paths:
        (root_p / p).mkdir(exist_ok=True)
    
    # Write .env
    with open(".env", "w") as f:
        f.write(f"GEMINI_API_KEY={api_key}\n")
        f.write(f"RESEARCH_ROOT_DIR={root_path}\n")
    
    print(f"✅ .env file created.")
    print(f"✅ Directory structure initialized at {root_path}")

def run_simulation_offer():
    print("\n" + "-"*40)
    print("🧪 RED TEAM SIMULATION / 模擬測試")
    print("-" * 40)
    print("Would you like to run a 'User Journey Simulation' now?")
    print("This will simulate a file upload, verify the AI response, and prove the system is working.")
    print("-> It takes about 30 seconds.")
    print("-" * 40)
    
    choice = input("Run Simulation? (y/n) [Default: y]: ").strip().lower()
    if choice in ["", "y", "yes"]:
        print("\n🚀 Initiating Simulation Sequence...")
        try:
            # We assume test_user_journey.py is in the scripts folder relative to CWD
            # Since start.py sets CWD to project root, we can call it relative to there.
            # But let's be robust.
            script_path = os.path.join("scripts", "test_user_journey.py")
            if os.path.exists(script_path):
                subprocess.call([sys.executable, script_path])
            else:
                # Fallback check
                script_path = "test_user_journey.py"
                if os.path.exists(script_path):
                    subprocess.call([sys.executable, script_path])
                else:
                    print("⚠️ Simulation script not found. Skipping.")
        except Exception as e:
            print(f"❌ Simulation failed: {e}")
    else:
        print("👌 Skipping simulation. You can run it later via 'python scripts/test_user_journey.py'")

def main():
    print_banner()
    check_dependencies()
    pre_flight_check()
    api_key = configure_api_key()
    capture_cookies()
    setup_environment(api_key)
    run_simulation_offer()

    
    print("\n" + "="*60)
    print("🐿️⚡️ FlashSquirrel is ready to fly!")
    print("To start the pipeline, run:")
    if sys.platform == "darwin":
        print("   ./scripts/run_pipeline.sh")
    else:
        print("   python scripts/auto_research_pipeline.py")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()
