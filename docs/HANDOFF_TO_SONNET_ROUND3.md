# Handoff: Opus → Sonnet (Round 3 - Portfolio Mode 修正)

> 開新 Sonnet session 時，把這段話貼進去當第一個 prompt。

---

## 給 Sonnet 的開場白

Round 2 你修得不錯（per-stock equity bug、月頻 rebalance、baseline CAGR 都修對了）。
但 Katie -63% MaxDD 的根因不在你提的 5 個選項裡 — 是 portfolio mode 漏實作 SPEC §5.2 的 regime filter。

**本輪任務：修 portfolio mode 三個 bug，不要動 Style 1 任何參數。**

**請依序讀：**
1. `docs/SONNET_FIX_ROUND3.md` — 本輪 single source of truth（含 P0-6/7/8 修法）
2. `docs/SPEC_strategy_system.md` §5.2 — 確認原始設計
3. `CLAUDE.md` — 含「用 Bash 工具不要用 PowerShell」新規則

**核心執行原則：**
- 全自動推進，依 ROUND3 文件「執行順序」做
- **新增 sanity gate 必加**：portfolio MaxDD ≤ 35%
- 修完依「回報格式」整理，回報 Opus
- 卡住寫 `docs/BLOCKED_round3.md`

**重要約束**：
- ❌ 不要動 Style 1（ma_long、atr_stop_k、trend_break_days、rsi 等）
- ❌ 不要為了過 gate 改門檻
- ✅ 修完 portfolio bug 後，CAGR 下降是正常（換更穩健的 MaxDD）

**Python 路徑（強制）**：`C:\Users\houyi.lee\AppData\Local\anaconda3\python.exe`
**執行用 Bash 工具**（不要 PowerShell，會跳 Windows 確認鈕）

開始吧。
