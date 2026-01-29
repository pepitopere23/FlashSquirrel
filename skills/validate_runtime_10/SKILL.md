---
name: validate_runtime_10
description: >
  FlashSquirrel 10-Layer Dynamic Validation System (Sigma Scale). 
  Ensures environment consistency, dynamic stability, and goal fulfillment.
  Triggers: "runtime check", "sigma", "10層驗證", "stability audit"
allowed-tools:
  - Read
  - Bash
  - Grep
  - Glob
user-invocable: true
context: fork
---

# FlashSquirrel 10-Layer Dynamic Validation Skill (Sigma / 動態)

專業級系統穩定性驗證系統。專注於「Sigma 動態量表」(L18-L27) 的自動化檢測。

## Usage

```bash
python3 scripts/validate_runtime_10.py
```

---

# Sigma-10 Validation Checklist

## Group 5: L18-L20 環境地基驗證 (Infrastructure)

### L18: 執行路徑鎖定 (Runtime Consistency)
**檢核點**: 驗證 VENV 與 Python 解釋器路徑的一致性。
**Check**: Verify `sys.executable` matches project venv.
**Pass**: VENV active and correct.
**Fail**: "VENV 衝突或未激活".

### L19: 外部資源握手 (Resource Handshake)
**What**: API Key & dependency connectivity (including Cookie/Session tokens).
**Check**: ping/mock call to Gemini/DB + validate browser cookie strings.
**Pass**: All external resources and auth tokens verified.
**Fail**: "API、資料庫或認證令牌失效".

### L20: 持久化與 IO 權限 (IO Guard)
**What**: File system write permissions.
**Check**: Attempt write to restricted path (e.g., iCloud/Processed folder).
**Pass**: Write success.
**Fail**: "權限不足，無法寫入資料".

---

## Group 6: L21-L24 邏輯抗壓驗證 (Resilience)

### L21: 併發狀態安全 (State Safety)
**What**: Race condition protection.
**Check**: Async lock or queue logic presence.
**Pass**: Safeguards detected.
**Fail**: "缺少併發鎖或競態防修護".

### L22: 異常退避與自癒 (Backoff Strategy)
**What**: Retry logic and **Anti-Bot Fallback**.
**Check**: Presence of `retry` loops AND human-in-the-loop fallback (e.g., cookie pasting UI).
**Pass**: Automated backoff verified AND manual override available.
**Fail**: "系統在攔截點死掉且無手動授權機制".

### L23: 數據畸變抗性 (Anomaly Tolerance)
**What**: Handling malformed data/emojis.
**Check**: Logic for character encoding or fuzzy matching.
**Pass**: Robustness verified.
**Fail**: "數據容錯性低".

### L24: 跨服務語義同步 (Service Sync)
**What**: Metadata consistency (Local vs Cloud).
**Check**: `.notebook_map.json` or equivalent sync log.
**Pass**: States match.
**Fail**: "本地與遠端狀態不同步".

---

## Group 7: L25-L27 終極交付驗證 (Goal Fulfillment)

### L25: 產品級交互驗證 (Contract Alignment)
**What**: Aesthetic and UI/CLI output quality.
**Check**: Output format matches spec (e.g., Emoji titles).
**Pass**: Visual/Textual alignment.

### L26: 元數據記憶持久化 (Memory Lock)
**What**: Persistence after reboot.
**Check**: Check if mapping file survived session.
**Pass**: Persistent memory ok.

### L27: 終極目標達成度 (Goal Satisfaction)
**What**: E2E business value fulfillment.
**Check**: Does the report exist? Was the folder renamed?
**Pass**: Core objective achieved.

---

## Output Format
Similar to BlueMouse 17-Layer, reports scores for Group 5-7.

*Part of the FlashSquirrel v2.1 Industrial Suite*
