
import sys
from validation_17_layers import validate_code_17_layers

with open(sys.argv[1], 'r') as f:
    code = f.read()

result = validate_code_17_layers(code, sys.argv[1])
print(f"SCORE: {result['quality_score']}")
for suggestion in result['suggestions']:
    print(f"SUGGESTION: {suggestion}")
