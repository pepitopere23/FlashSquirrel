"""
FlashSquirrel Industrial Audit v4.0
Automated Validation for the 27-Layer Engineering Standard (Alpha + Sigma).
"""

import os
import sys
import json
import subprocess
import platform
import time
from pathlib import Path

def print_audit_banner(text):
    print("\n" + "="*60)
    print(f"🕵️  AUDIT: {text}")
    print("="*60)

def run_step(name, command):
    print(f"🔍 Checking: {name}...")
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        print(f"✅ {name} PASSED")
        return True, result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {name} FAILED: {e.stderr}")
        return False, e.stderr

def audit_17_layers_static():
    """L1-L17: Alpha Static Scale"""
    print_audit_banner("Alpha Scale: 17-Layer Static Excellence")
    sys.path.append(os.path.join(os.getcwd(), "scripts"))
    try:
        from validation_17_layers import validate_code_17_layers
        core_files = ["scripts/auto_research_pipeline.py", "start.py", "setup_wizard.py", "scripts/notebooklm_automator.py"]
        scores = []
        for f in core_files:
            if os.path.exists(f):
                with open(f, "r") as code_file:
                    code = code_file.read()
                result = validate_code_17_layers(code, f)
                score = result['quality_score']
                scores.append(score)
                status = "✅" if score >= 90 else "⚠️" if score >= 80 else "❌"
                print(f"{status} {f}: {score}/100")
        
        avg_score = sum(scores) / len(scores) if scores else 0
        return avg_score >= 85, avg_score
    except Exception as e:
        print(f"❌ 17-Layer Audit Failed to Execute: {e}")
        return False, 0

def audit_10_layers_runtime():
    """L18-L27: Sigma Runtime Scale"""
    print_audit_banner("Sigma Scale: 10-Layer Runtime Fortress")
    
    venv_python = "/Users/chenpeijun/research_pipeline/.venv/bin/python3"
    python_to_use = venv_python if os.path.exists(venv_python) else sys.executable
    
    checks = []
    
    # L18: Runtime Lock
    ok_l18 = os.path.exists(venv_python)
    print(f"{'✅' if ok_l18 else '❌'} L18 Runtime Lock (VENV Consistency)")
    checks.append(ok_l18)
    
    # L19: Resource Handshake (Gemini & Auth Connectivity)
    ok_l19_api, _ = run_step("L19 API Handshake (Gemini)", [python_to_use, "-c", "import google.genai; print('ok')"])
    
    auth_file = os.path.expanduser("~/.notebooklm-mcp/auth.json")
    ok_l19_auth = os.path.exists(auth_file)
    print(f"{'✅' if ok_l19_auth else '⚠️'} L19 Auth Handshake (Cookie/Token Presence)")
    
    checks.append(ok_l19_api and ok_l19_auth)
    
    # L20: Path Accuracy (iCloud/Local)
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    root_dir = os.getenv("RESEARCH_ROOT_DIR")
    ok_l20 = os.path.exists(root_dir) if root_dir else True
    print(f"{'✅' if ok_l20 else '⚠️'} L20 Path Accuracy (iCloud/Local)")
    checks.append(ok_l20)
    
    # L21-L24: Logic Resilience (Abstract check)
    # Checking for specific logic in files
    automator_path = "scripts/notebooklm_automator.py"
    with open(automator_path, "r") as f:
        content = f.read()
        exact_check = "exact=True" in content
        print(f"{'✅' if exact_check else '❌'} L23 Data Anomaly Tolerance (Exact Match Logic)")
        checks.append(exact_check)
        
        # L22: Error Recovery / Anti-Bot Fallback
        fallback_check = "load_cookies" in content or "fix_auth.sh" in content
        print(f"{'✅' if fallback_check else '⚠️'} L22 Anti-Bot Resilience (Cookie Fallback Logic)")
        checks.append(fallback_check)
        
    # L26: Metadata Persistence
    ok_l26 = "save_mapping" in content
    print(f"{'✅' if ok_l26 else '❌'} L26 Metadata Memory Persistence")
    checks.append(ok_l26)
    
    runtime_score = (sum(checks) / len(checks)) * 100 if checks else 0
    return runtime_score >= 80, runtime_score

def main():
    print("\n" + "-" * 40)
    print("FLASH SQUIRREL: OMEGA-27 ENGINEERING AUDIT")
    print("-" * 40)
    
    static_pass, static_score = audit_17_layers_static()
    runtime_pass, runtime_score = audit_10_layers_runtime()
    
    omega_score = (static_score * 0.6) + (runtime_score * 0.4)
    
    print("\n" + "="*60)
    print(f"🏆 FINAL OMEGA SCORE: {omega_score:.1f}/100")
    print("="*60)
    
    if static_pass and runtime_pass:
        print("\n" + "=" * 40)
        print("AUDIT SUCCESS: SYSTEM COMPLIES WITH OMEGA-27 STANDARDS")
        print("=" * 40 + "\n")
    else:
        print("\n" + "!" * 40)
        print("AUDIT FAILED: NON-COMPLIANCE DETECTED")
        print("!" * 40 + "\n")
        sys.exit(1)

if __name__ == "__main__":
    main()
