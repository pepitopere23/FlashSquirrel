import os
import sys
import time
import subprocess
import glob
import json

# Configuration
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INPUT_DIR = os.path.join(ROOT_DIR, "input_thoughts")
LOG_FILE = os.path.join(ROOT_DIR, "health_check_result.log")

RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"

class UltimateDoctor:
    def __init__(self):
        self.points = 0
        self.total_checks = 0
        self.errors = []

    def check(self, name, condition, error_msg):
        self.total_checks += 1
        print(f"🩺 Checking {name}...", end=" ")
        if condition:
            print(f"{GREEN}PASSED{RESET}")
            self.points += 1
            return True
        else:
            print(f"{RED}FAILED{RESET}")
            self.errors.append(f"[{name}] {error_msg}")
            return False

    def run_process_check(self):
        # Check if the autoimmune system (pipeline) is running
        try:
            # Check for the pipeline script
            output = subprocess.check_output(["pgrep", "-f", "auto_research_pipeline.py"]).decode().strip()
            return self.check("System Pulse", bool(output), "Auto-Research Pipeline is NOT running!")
        except subprocess.CalledProcessError:
            return self.check("System Pulse", False, "Auto-Research Pipeline is NOT running!")

    def run_filesystem_check(self):
        # 1. Check prohibited files
        bad_files = glob.glob(os.path.join(INPUT_DIR, "report_*"))
        self.check("Recursion Shield", len(bad_files) == 0, f"Found {len(bad_files)} forbidden 'report_' files in input directory!")
        
        # 2. Check for Untitled local folders
        # This is a bit tricky, we need to scan directories in ROOT_DIR that are NOT system dirs
        system_dirs = ["scripts", "docs", "input_thoughts", "processed_reports", "skills", ".git", ".venv", ".agent", "_QUARANTINE_"]
        
        untitled_count = 0
        for name in os.listdir(ROOT_DIR):
            path = os.path.join(ROOT_DIR, name)
            if os.path.isdir(path) and name not in system_dirs:
                if "Untitled" in name or "未命名" in name:
                    untitled_count += 1
        
        self.check("Untitled Virus Scan", untitled_count == 0, f"Found {untitled_count} folders named 'Untitled' locally!")

    def run_agent_check(self):
        # Check if Launch Agent is loaded
        try:
            output = subprocess.check_output(["launchctl", "list"]).decode()
            is_loaded = "com.flashsquirrel.agent" in output
            self.check("Auto-Start Agent", is_loaded, "Launch Agent is NOT loaded (Standard/Background process only).")
        except:
             self.check("Auto-Start Agent", False, "Could not query launchctl.")

    def final_report(self):
        print("\n" + "="*30)
        print("🏥 FINAL HEALTH REPORT")
        print("="*30)
        if not self.errors:
            print(f"{GREEN}ALL SYSTEMS NOMINAL. 100% HEALTHY.{RESET}")
            print("The patient is ready for discharge.")
            return True
        else:
            print(f"{RED}SYSTEM CRITICAL. FOUND ISSUES:{RESET}")
            for err in self.errors:
                print(f" - {err}")
            return False

if __name__ == "__main__":
    print(f"🚀 Starting Super Ultimate Health Check (Triple Pass)...")
    doctor = UltimateDoctor()
    
    for i in range(1, 4):
        print(f"\n--- PASS {i}/3 ---")
        doctor.run_process_check()
        doctor.run_filesystem_check()
        doctor.run_agent_check()
        time.sleep(1) # Breath between checks
    
    success = doctor.final_report()
    if not success:
        sys.exit(1)
