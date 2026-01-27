#!/usr/bin/env python3
"""
FlashSquirrel Unified Launcher 🐿️⚡️
One command to rule them all. Handles setup, dependencies, and starts the engine.
"""

import os
import sys
import subprocess
import time

def run_command(cmd_list):
    try:
        subprocess.check_call([sys.executable] + cmd_list)
    except Exception as e:
        print(f"❌ Command failed: {e}")
        sys.exit(1)

def main():
    print("\n" + "🐿️ "*10)
    print("Welcome to FlashSquirrel Launcher!")
    print("🐿️ "*10 + "\n")

    # 1. Check for .env file
    if not os.path.exists(".env"):
        print("🔍 First run detected. Initiating Setup Wizard...")
        run_command(["setup_wizard.py"])
        print("\n✅ Setup complete. Taking a quick breath...")
        time.sleep(2)

    # 2. Start the Pipeline
    print("🚀 Igniting the Research Engine...")
    
    pipeline_script = os.path.join("scripts", "auto_research_pipeline.py")
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

if __name__ == "__main__":
    main()
