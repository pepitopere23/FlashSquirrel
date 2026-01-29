---
name: validate_omega_27
description: >
  The Ultimate FlashSquirrel Omega-27 Industrial Certification.
  Combines 17 layers of Static standards (Alpha) with 10 layers of Runtime stability (Sigma).
  Triggers: "omega audit", "27層驗證", "industrial certification", "omega score"
allowed-tools:
  - Read
  - Bash
  - Grep
  - Glob
user-invocable: true
context: fork
---

# Omega-27 綜合工程認證 Skill (Static + Dynamic)

Omega 認證是自動化軟體工程的最高驗證等級。它確保系統不僅在代碼層面具備專業性（Alpha 靜態審計），且在實際運行環境中具備高度可靠性（Sigma 動態驗證）。

## The Omega Equation
**Omega Score = (Alpha Static * 0.6) + (Sigma Dynamic * 0.4)**

---

# Verification Roadmap

## Phase 1: Alpha Static (L1-L17)
Refer to the `validate-17-layers` checklist for:
- Syntax & Structure (L1-L4)
- Signature & Docs (L5-L8)
- Dependencies (L9-L12)
- Logic & Security (L13-L17)

## Phase 2: Sigma Runtime (L18-L27)
Refer to the `validate-runtime-10` checklist for:
- Infrastructure (L18-L20)
- Resilience (L21-L24)
- Goal Fulfillment (L25-L27)

---

## Usage

```bash
python3 scripts/grand_audit_v4.py
```

## Output Format
Combines both reports into a single **Omega-27 Gold Certificate**.
