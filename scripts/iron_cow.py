#!/usr/bin/env python3
"""
FlashSquirrel Iron Cow Ritual (開發者專用鐵牛儀式) v5.0
The ultimate triple-audit + red-team stress test for industrial excellence.
"""

import os
import sys
import time
import subprocess
from pathlib import Path

# Paths
SCRIPTS_DIR = Path(__file__).parent
PROJECT_ROOT = SCRIPTS_DIR.parent
OMEGA_VALIDATOR = SCRIPTS_DIR / "grand_audit_v4.py"
STRESS_TESTER = SCRIPTS_DIR / "extreme_boundary_test.py"

def print_banner(text):
    print("\n" + "🐂 " * 20)
    print(f"   {text}")
    print("🐂 " * 20 + "\n")

def run_step(name, command):
    print(f"⏳ [RITUAL] Executing {name}...")
    try:
        # Run and capture output to keep the 'Iron Cow' report clean unless failure
        result = subprocess.run(command, capture_output=True, text=True, check=True, cwd=PROJECT_ROOT)
        print(f"✅ {name} SUCCESS\n")
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {name} FAILED!")
        print(f"   Output: {e.stdout}")
        print(f"   Error: {e.stderr}")
        return False, e.stderr

def sanitize_workspace():
    print("🧹 [RITUAL] Sanitizing construction debris...")
    # Clean pycache
    subprocess.run(["find", ".", "-name", "__pycache__", "-delete"], cwd=PROJECT_ROOT)
    # Clean stress test artifacts
    stress_dir = PROJECT_ROOT / "input_thoughts" / "STRESS_TEST_UNIT"
    if stress_dir.exists():
        import shutil
        shutil.rmtree(stress_dir)
    print("✅ Workspace Sanitized.\n")

def execute_ritual():
    print_banner("IRON COW RITUAL: TRIPLE-AUDIT START")
    
    # Sequence 1: Sequential Triple Audit (V4 Grand Audit)
    # 1. Static Quality (17-Layer Alpha)
    print("📋 [1/4] Alpha Phase: Static Integrity...")
    ok1, _ = run_step("Industrial 17-Layer Validation", [sys.executable, str(SCRIPTS_DIR / "validation_17_layers.py")])
    if not ok1: return False

    # 2. Runtime Reliability (10-Layer Sigma)
    print("📋 [2/4] Sigma Phase: Runtime Compliance...")
    ok2, _ = run_step("Omega-27 Full Audit", [sys.executable, str(OMEGA_VALIDATOR)])
    if not ok2: return False

    # 3. Resilience Confirmation (Omega Phase)
    print("📋 [3/4] Omega Phase: Resilience Confirmation...")
    ok3, _ = run_step("Redundant Integrity Verification", [sys.executable, str(OMEGA_VALIDATOR)])
    if not ok3: return False

    # 4. Red-Team Raid
    print("📋 [4/4] Red-Team Phase: Ultimate Stress Test...")
    ok4, _ = run_step("Extreme Boundary Simulation", [sys.executable, str(STRESS_TESTER)])
    if not ok4: return False

    # Sanitization
    sanitize_workspace()
    
    return True

if __name__ == "__main__":
    success = execute_ritual()
    
    if success:
        print("\n" + "=" * 40)
        print("🌟 閃電松鼠壯得像頭牛！(完美的工業級)")
        print("   (FlashSquirrel is 100% Industrial-Grade!)")
        print("=" * 40 + "\n")
    else:
        print("\n" + "!" * 40)
        print("🚨 RITUAL INTERRUPTED: System is compromised.")
        print("!" * 40 + "\n")
        sys.exit(1)
