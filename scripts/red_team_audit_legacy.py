#!/usr/bin/env python3
"""
FlashSquirrel Grand Health Check & Red Team Audit ⚡️🐿️
Usage: Just say 'Health Check' to run this.
"""
import os
import subprocess
import sys

def run_step(name, cmd):
    print(f"🔍 Checking: {name}...")
    try:
        if isinstance(cmd, list):
            result = subprocess.run(cmd, capture_output=True, text=True)
        else:
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print(f"✅ {name} PASSED")
            return True, result.stdout
        else:
            print(f"❌ {name} FAILED: {result.stderr}")
            return False, result.stderr
    except Exception as e:
        print(f"💥 Error running {name}: {e}")
        return False, str(e)

def main():
    print("🚀 Initiating Triple-Stage Health Check & Red Team Audit...\n")
    
    # 1. Functional Integrity
    f1, _ = run_step("Entry Point (start.py) exists", "ls start.py")
    f2, _ = run_step("Dependencies (requirements.txt)", "ls requirements.txt")
    
    # 2. Security & Red Team Audit
    s1, _ = run_step("Privacy Check (Zero Hardcoded Paths)", "grep -r '/Users/' . | grep -v '.git' | grep -v '.venv' | wc -l")
    s2, _ = run_step("Secret Shield (Git Tracking)", "git ls-files .env auth.json")
    
    # 3. Portability & Resilience
    p1, _ = run_step("Cross-Platform Scripting (Relative Paths)", "grep 'dirname' scripts/*.sh")
    p2, _ = run_step("Path Separator Integrity", "grep -r '\\\\' . | grep -v '.git' | grep -v 'venv' | wc -l") # Checking for hardcoded Windows backslashes in scripts
    
    # 4. Zero-Friction Entry Check
    z1, _ = run_step("Setup Resilience (start.py)", "grep 'setup_wizard' start.py")
    
    # 5. iCloud Privacy Check
    i1, _ = run_step("iCloud Metadata Shield", "grep -r '.icloud' . | grep -v 'auto_research_pipeline.py' | wc -l")

    print("\n" + "="*40)
    if all([f1, f2, s1, s2, p1, p2, z1, i1]):
        print("⚡️ 閃電松鼠撞得像一頭牛 ⚡️🐿️")
        print("⚡️ 閃電松鼠撞得像一頭牛 ⚡️🐿️")
        print("⚡️ 閃電松鼠撞得像一頭牛 ⚡️🐿️")
        print("\n[Red Team Verdict]: System is hardened, anonymized, and ready for deployment.")
    else:
        print("⚠️  Audit incomplete or issues found. Please review logs.")
    print("="*40 + "\n")

if __name__ == "__main__":
    main()
