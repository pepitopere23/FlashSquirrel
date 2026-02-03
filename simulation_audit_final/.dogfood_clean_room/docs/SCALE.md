# 🐭 BlueMouse Alpha Scale (17-Layer Static Standard)
*The Industrial Golden Standard for Static Code Analysis.*

This document defines the **Alpha Scale** (Layers 1-17), originally established by the BlueMouse project. It ensures code hygiene, structural integrity, and logic safety.

## Group 1: Syntax & Hygiene (L1-L4)
*   **L1: Basic Syntax**: Code must compile/parse without any syntax errors.
*   **L2: AST Structure**: Must have a valid Abstract Syntax Tree with clear class/function hierarchy.
*   **L3: Indentation**: Strict adherence to PEP-8 (4 spaces, no tabs).
*   **L4: Naming**: `snake_case` for functions/variables, `PascalCase` for classes.

## Group 2: Interface & Documentation (L5-L8)
*   **L5: Signature Check**: Function arguments must match the design specification.
*   **L6: Return Value**: Functions must return the expected types (no implicit `None` if `int` promisised).
*   **L7: Type Hints**: Explicit usage of Python typing (`List`, `Dict`, `Optional`, etc.).
*   **L8: Docstrings**: Every function and class must have a descriptive docstring.

## Group 3: Dependency Integrity (L9-L12)
*   **L9: Import Check**: No missing or broken modules.
*   **L10: Circular Ref**: Prevention of circular import loops (A->B->A).
*   **L11: Version Guard**: Package versions must match `requirements.txt`.
*   **L12: Path Resolution**: Correct usage of absolute vs relative imports.

## Group 4: Logic & Safety (L13-L17)
*   **L13: Complexity**: Cyclomatic complexity must remain low (avoid deeply nested loops).
*   **L14: Exception Handling**: No bare `try...except` blocks; specific exceptions required.
*   **L15: Resource Leak**: File handles and sockets must be closed (use `with` context managers).
*   **L16: Security Scan**: Zero tolerance for hardcoded passwords, API keys, or tokens.
*   **L17: Logic Flow**: No dead code or unreachable branches.

---
*Verified by FlashSquirrel Omega-27 Agent.*
