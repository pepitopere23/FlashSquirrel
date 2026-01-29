
import os
import sys
import json
from pathlib import Path

# Add scripts to path
sys.path.append(os.path.join(os.getcwd(), "scripts"))
from validation_17_layers import validate_code_17_layers

def deep_audit(filepath):
    print(f"\n--- AUDIT: {filepath} ---")
    if not os.path.exists(filepath):
        print("File not found.")
        return
    
    with open(filepath, "r") as f:
        code = f.read()
    
    res = validate_code_17_layers(code, filepath)
    print(f"Score: {res['quality_score']}/100")
    for layer in res['layers']:
        status = "✅" if layer['passed'] else "❌"
        print(f"  {status} L{layer['layer']}: {layer['name']} - {layer['message']}")
    
    if res['suggestions']:
        print("\n  Suggestions:")
        for s in res['suggestions']:
            print(f"    - {s}")

if __name__ == "__main__":
    core_files = [
        "scripts/auto_research_pipeline.py",
        "scripts/notebooklm_automator.py",
        "start.py",
        "scripts/reconstruct_library.py"
    ]
    for f in core_files:
        deep_audit(f)
