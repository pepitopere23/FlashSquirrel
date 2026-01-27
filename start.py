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

def main() -> None:
    """
    The main entry point for the FlashSquirrel launcher.
    Handles environment setup and starts the research pipeline.
    """
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
    
    return None

if __name__ == "__main__":
    main()
