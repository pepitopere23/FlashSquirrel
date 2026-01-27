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

def configure_api_key():
    print("\n🔑 Step 1: Gemini API Key")
    print("Get your free key here: https://aistudio.google.com/app/apikey")
    
    current_key = os.getenv("GEMINI_API_KEY", "")
    prompt = f"Paste your Gemini API Key [{current_key[:6]}...]: " if current_key else "Paste your Gemini API Key: "
    
    key = input(prompt).strip()
    if not key and current_key:
        key = current_key
    elif not key:
        print("⚠️ API Key is required to run the pipeline.")
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
            
            # Wait for a selector that only appears after login, e.g., the user profile or "New Notebook"
            try:
                page.wait_for_selector("text=New Notebook", timeout=300000)
            except:
                try:
                    page.wait_for_selector("text=建立新的筆記本", timeout=1000)
                except:
                    print("⚠️ Login timeout or browser closed. Proceeding with captured cookies if possible...")
            
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
    root_p.mkdir(parents=True, exist_ok=True)
    for p in paths:
        (root_p / p).mkdir(exist_ok=True)
    
    # Write .env
    with open(".env", "w") as f:
        f.write(f"GEMINI_API_KEY={api_key}\n")
        f.write(f"RESEARCH_ROOT_DIR={root_path}\n")
    
    print(f"✅ .env file created.")
    print(f"✅ Directory structure initialized at {root_path}")

def main():
    print_banner()
    check_dependencies()
    api_key = configure_api_key()
    capture_cookies()
    setup_environment(api_key)
    
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
