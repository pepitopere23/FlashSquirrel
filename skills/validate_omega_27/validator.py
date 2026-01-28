"""
Industrial-Omega-27 Certifier
Orchestratror for Static (Alpha) and Runtime (Sigma) validation scales.
"""

import sys
import os
import json

# Ensure scripts can be found
sys.path.append(os.getcwd())
sys.path.append(os.path.join(os.getcwd(), 'scripts'))

try:
    from scripts.validation_17_layers import validate_code_17_layers
    from skills.validate_runtime_10.validator import validate_runtime_10_layers
except ImportError:
    # Fallback for different folder structures
    def validate_code_17_layers(c, n): return {"quality_score": 0}
    def validate_runtime_10_layers(): return {"score": 0}

def certify_omega_27(target_files: list) -> dict:
    """Combines Alpha and Sigma scores."""
    static_scores = []
    for f in target_files:
        if os.path.exists(f):
            with open(f, 'r') as code:
                res = validate_code_17_layers(code.read(), f)
                static_scores.append(res['quality_score'])
    
    alpha_score = sum(static_scores) / len(static_scores) if static_scores else 0
    sigma_report = validate_runtime_10_layers()
    sigma_score = sigma_report['score']
    
    omega_score = (alpha_score * 0.6) + (sigma_score * 0.4)
    
    return {
        "certification": "Omega-27",
        "omega_score": omega_score,
        "alpha_score": alpha_score,
        "sigma_score": sigma_score,
        "passed": omega_score >= 85
    }

if __name__ == "__main__":
    targets = ["start.py", "setup_wizard.py"]
    print(json.dumps(certify_omega_27(targets), indent=2))
