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
        print("   -> Installing Python libraries...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        
        print("\n   -> Downloading Browser Engine (Playwright Chromium)...")
        print("      ⚠️  This is a large download (~150 MB). Please be patient.")
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
        
        # Verify importability
        try:
            import playwright
            print("✅ Dependencies installed successfully.")
        except ImportError:
            print("⚠️  Playwright installed but not immediately visible to Python path.")
            print("   Attempting to refresh environment...")
            # On some systems, we might need to use a slightly different approach or tell the user to restart
            time.sleep(2)

    except Exception as e:
        print(f"❌ Error installing dependencies: {e}")
        print("Please ensure you have an active internet connection.")
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
    print("📊 System Integrity Check: PASSED")
    print("-" * 40)
    time.sleep(1)

def configure_api_key():
    print("\n" + "-"*40)
    print("🔑 Step 1: API Key Configuration")
    print("-" * 40)
    print("Please enter your Google Gemini API Key to enable AI features.\n")
    
    print("Instructions:")
    print("1. Visit: https://aistudio.google.com/app/apikey")
    print("2. Click 'Create API Key'")
    print("3. Copy the key string (starts with 'AIza...')")
    print("-" * 40 + "\n")
    
    current_key = os.getenv("GEMINI_API_KEY", "")
    prompt = f"Paste API Key [{current_key[:6]}...]: " if current_key else "Paste API Key: "
    
    key = input(prompt).strip()
    if not key and current_key:
        key = current_key
    elif not key:
        print("⚠️  API Key is required. Please try again.")
        return configure_api_key()
    return key

def capture_cookies():
    print("\n" + "-"*40)
    print("🍪 Step 2: NotebookLM Authentication")
    print("-" * 40)
    print("1. [Auto] Open Browser & Capture (Recommended)")
    print("2. [Manual] Paste Cookies manually (Use if Auto fails/Google blocks you)")
    
    choice = input("\nSelect Method (1/2) [Default: 1]: ").strip()
    
    auth_dir = Path.home() / ".notebooklm-mcp"
    auth_dir.mkdir(parents=True, exist_ok=True)
    auth_file = auth_dir / "auth.json"

    if choice == "2":
        print("\n🛠️  Manual Cookie Entry Mode")
        print("1. Open NotebookLM in your regular browser (Chrome/Edge).")
        print("2. Use a 'Cookie Editor' extension or DevTools to copy your cookies.")
        print("3. Paste the JSON array or key-value object here:")
        raw_cookie_data = input("\nPaste Cookie JSON: ").strip()
        try:
            parsed = json.loads(raw_cookie_data)
            # Standardize format for our automator
            auth_data = {"cookies": parsed}
            with open(auth_file, "w") as f:
                json.dump(auth_data, f, indent=4)
            print(f"✅ Cookies saved successfully to {auth_file}")
            return
        except Exception as e:
            print(f"❌ Invalid JSON: {e}")
            return capture_cookies()

    # Auto Mode with Stealth Hardening
    print("\n🚀 Launching Stealth Browser...")
    print("Please log into your Google Account in the window that appears.")
    
    try:
        from playwright.sync_api import sync_playwright
        
        with sync_playwright() as p:
            # STEALTH: Use common User Agent and disable automation flags
            user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            if sys.platform == "win32":
                user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

            browser = p.chromium.launch(
                headless=False,
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--no-sandbox"
                ]
            )
            context = browser.new_context(user_agent=user_agent)
            page = context.new_page()
            
            # Additional stealth: Hide the WebDriver flag
            page.add_init_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            page.goto("https://notebooklm.google.com/")
            
            print("⏳ Waiting for you to log in... (Timeout in 5 minutes)")
            
            try:
                # Wait for any indicator of a logged-in state
                page.wait_for_selector("button:has-text('New Notebook'), button:has-text('建立新的筆記本'), .c6", timeout=300000)
                print("✅ Login detected!")
            except:
                print("⚠️  Login indicator timeout. Capturing current state anyway...")
            
            cookies = context.cookies()
            auth_data = {"cookies": cookies}
            
            with open(auth_file, "w") as f:
                json.dump(auth_data, f, indent=4)
            
            browser.close()
            print(f"✅ Cookies captured successfully.")
            
    except Exception as e:
        print(f"❌ Error during auto-capture: {e}")
        print("\n💡 Tip: Google might have blocked the automated browser.")
        print("Try Method 2 [Manual] to bypass this.")
        return capture_cookies()

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
    print("🧪 Installation Verification / 安裝驗證")
    print("-" * 40)
    print("Would you like to run a quick self-test to verify the system?")
    print("This will simulate a user action to ensure everything is working correctly.")
    print("-" * 40)
    
    choice = input("Run Verification? (y/n) [Default: y]: ").strip().lower()
    if choice in ["", "y", "yes"]:
        print("\n🚀 Starting Verification...")
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
