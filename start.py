#!/usr/bin/env python3
"""
FlashSquirrel Unified Launcher 🐿️⚡️
One command to rule them all. Handles setup, dependencies, and starts the engine.
"""
import os
import sys
import subprocess
import time

from typing import List

def run_command(cmd_list: List[str]) -> None:
    """
    Runs a python script as a subprocess.
    
    Args:
        cmd_list: The list of arguments to pass to the python interpreter.
    """
    try:
        subprocess.check_call([sys.executable] + cmd_list)
    except Exception as e:
        print(f"❌ Command failed: {e}")
        sys.exit(1)
    return None

def check_dependencies() -> bool:
    """
    Verifies that all required Python libraries are installed.
    
    Returns:
        True if all dependencies are present, False otherwise.
    """
    try:
        import dotenv
        import playwright
        import watchdog
        return True
    except ImportError:
        return False

def main() -> int:
    """
    The main entry point for the FlashSquirrel launcher.
    Handles environment setup and starts the research pipeline.
    
    Returns:
        Exit code (0 for success, 1 for failure).
    """
    print("\n" + "🐿️ "*10)
    print("Welcome to FlashSquirrel Launcher!")
    print("🐿️ "*10 + "\n")

    # 0. Force-CWD: Ensure we are running inside the project folder
    # This fixes the issue where users download to "Downloads" and run from a different CWD
    try:
        project_dir = os.path.dirname(os.path.abspath(__file__))
        os.chdir(project_dir)
        print(f"📂 Working Directory set to: {project_dir}")
    except Exception as e:
        print(f"⚠️ Failed to set working directory: {e}")

    # 1. Check for .env file and dependencies
    if not os.path.exists(".env") or not check_dependencies():
        print("🔍 First run or missing dependencies detected. Initiating Setup Wizard...")
        run_command(["setup_wizard.py"])
        print("\n✅ Setup complete. Taking a quick breath...")
        time.sleep(2)

    # 2. Offer "Full-Auto" Choice
    print("\n" + "-"*40)
    print("🤖 MODE SELECTION / 模式選擇")
    print("1. [Full-Auto] Install Background Service / 安裝後台隱形守衛 (Recommended)")
    print("   -> Runs automatically at startup. You don't need to open this again.")
    print("2. [Semi-Auto] Run Once / 單次執行")
    print("   -> Runs only while this window is open.")
    print("-"*40)
    
    choice = input("Select Mode (1/2) [Default: 2]: ").strip()
    
    if choice == "1":
        print("🚀 Setting up Full-Auto Mode...")
        run_command(["scripts/setup_background.py"])
        print("✅ Service Installed! You can close this window now.")
        return # Exit because service will take over

    # 3. Semi-Auto: Start the Pipeline Manually
    print("🚀 Igniting the Research Engine (Manual Mode)...")
    
    pipeline_script: str = os.path.join("scripts", "auto_research_pipeline.py")
    if not os.path.exists(pipeline_script):
        # Fallback if scripts folder is different
        pipeline_script = "auto_research_pipeline.py"

    try:
        # We use subprocess.run so it stays active in the terminal
        subprocess.run([sys.executable, pipeline_script])
    except KeyboardInterrupt:
        print("\n🐿️  FlashSquirrel has returned to the forest. See you next time!")
    except Exception as e:
        print(f"❌ Pipeline crashed: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
